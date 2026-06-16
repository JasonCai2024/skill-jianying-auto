#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

from skill_config import load_runtime_config


def _deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(base or {})
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge_dict(out[k], v)
        else:
            out[k] = v
    return out


def _load_template_cfg(project_root: Path, template_id: str) -> Dict[str, Any]:
    tid = (template_id or "").strip()
    if not tid:
        return {}
    tp = project_root / "user_data" / "templates" / f"{tid}.json"
    if not tp.exists():
        raise FileNotFoundError(f"template not found: {tp}")
    return json.loads(tp.read_text(encoding="utf-8-sig"))


def _normalize_text(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", s)
    return s


def _segment_time_sec(seg: Dict[str, Any]) -> Tuple[float, float]:
    start_us = int(seg.get("start", 0) or 0)
    duration_us = int(seg.get("duration", 0) or 0)
    end_us = start_us + duration_us
    return start_us / 1_000_000.0, end_us / 1_000_000.0


def _parse_srt_time(ts: str) -> float:
    hms, ms = ts.split(",")
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _read_srt_rows(path: Path) -> List[Dict[str, Any]]:
    raw = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\r?\n\r?\n+", raw.strip())
    rows: List[Dict[str, Any]] = []
    for b in blocks:
        lines = [x.strip() for x in b.splitlines() if x.strip()]
        if len(lines) < 2:
            continue
        ts_line = lines[1] if "-->" in lines[1] else lines[0]
        m = re.search(r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})", ts_line)
        if not m:
            continue
        st = _parse_srt_time(m.group(1))
        ed = _parse_srt_time(m.group(2))
        txt = " ".join(lines[2:] if ts_line == lines[1] else lines[1:]).strip()
        rows.append({"start": st, "end": ed, "text": txt})
    return rows


def _calibrate_segments_with_srt_windows(
    segments: List[Dict[str, Any]],
    srt_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    用 SRT 时间窗校准 Aeneas 段时间（保留 Aeneas 文本），
    仅用于提升上屏时间稳定性，不改变素材对齐逻辑。
    """
    if not segments or not srt_rows:
        return segments

    out = [dict(x) for x in segments]
    groups: Dict[int, List[int]] = {}
    r = 0
    for i, seg in enumerate(out):
        st, _ = _segment_time_sec(seg)
        while r < len(srt_rows) - 1 and st >= float(srt_rows[r]["end"]):
            r += 1
        groups.setdefault(r, []).append(i)

    for r_idx, idxs in groups.items():
        row = srt_rows[r_idx]
        row_start_us = int(float(row["start"]) * 1_000_000)
        row_end_us = int(float(row["end"]) * 1_000_000)
        row_span = max(row_end_us - row_start_us, len(idxs) * 1_000)
        ws = []
        for i in idxs:
            d = int(out[i].get("duration", 0) or 0)
            ws.append(max(d, 1_000))
        sw = sum(ws) or len(idxs)

        cur = row_start_us
        remain = row_span
        for j, i in enumerate(idxs):
            if j == len(idxs) - 1:
                dur = max(remain, 1_000)
            else:
                dur = max(int(round(row_span * (ws[j] / sw))), 1_000)
                remain = max(remain - dur, 1_000)
            out[i]["start"] = cur
            out[i]["duration"] = dur
            out[i]["end"] = cur + dur
            cur += dur

    return out


def _split_text_for_display(text: str, max_chars: int = 18) -> List[str]:
    """按标点优先、字数兜底拆分上屏字幕，避免单条过长。"""
    s = (text or "").strip()
    if not s:
        return []

    # 先按强停顿切，保留语义自然边界
    pieces = re.split(r"(?<=[。！？；!?;])", s)
    pieces = [p.strip() for p in pieces if p.strip()]
    if not pieces:
        pieces = [s]

    out: List[str] = []
    for p in pieces:
        # 再按逗号/顿号等弱停顿拆
        sub = re.split(r"(?<=[，、,])", p)
        sub = [x.strip() for x in sub if x.strip()]
        if not sub:
            sub = [p]
        for part in sub:
            if len(part) <= max_chars:
                out.append(part)
                continue
            # 仍过长则按字数硬切（保底）
            cur = 0
            while cur < len(part):
                out.append(part[cur:cur + max_chars].strip())
                cur += max_chars
    return [x for x in out if x]


def _build_display_subtitle_segments(
    aligned_segments: List[Dict[str, Any]],
    max_chars: int = 18,
    min_duration_sec: float = 0.35,
) -> List[Dict[str, Any]]:
    """将对齐段转换为上屏段：时间保持、文本按显示规则切分。"""
    rows: List[Dict[str, Any]] = []
    for seg in aligned_segments:
        text = str(seg.get("text", "")).strip()
        if not text:
            continue
        start_s, end_s = _segment_time_sec(seg)
        total_dur = max(end_s - start_s, 0.001)
        chunks = _split_text_for_display(text, max_chars=max_chars)
        if not chunks:
            continue

        # 依据字符数按比例分配时长
        weights = [max(len(_normalize_text(c)), 1) for c in chunks]
        sw = sum(weights) or len(chunks)
        cur = start_s
        remain = total_dur
        for i, ch in enumerate(chunks):
            if i == len(chunks) - 1:
                dur = max(remain, min_duration_sec)
            else:
                dur = max(total_dur * (weights[i] / sw), min_duration_sec)
                remain = max(remain - dur, min_duration_sec)
            rows.append({"text": ch, "start": cur, "duration": dur})
            cur += dur
    return rows


def _merge_short_display_segments(
    rows: List[Dict[str, Any]],
    min_show_sec: float = 0.9,
    max_merge_chars: int = 22,
) -> List[Dict[str, Any]]:
    """合并过短字幕段，提升可读性与跟读观感。"""
    if not rows:
        return rows
    out: List[Dict[str, Any]] = []
    i = 0
    while i < len(rows):
        cur = dict(rows[i])
        cur_text = str(cur.get("text", "")).strip()
        cur_start = float(cur.get("start", 0.0))
        cur_dur = float(cur.get("duration", 0.0))
        j = i + 1
        while (
            j < len(rows)
            and cur_dur < min_show_sec
            and len(cur_text) < max_merge_chars
        ):
            nxt = rows[j]
            nxt_text = str(nxt.get("text", "")).strip()
            if len(cur_text) + len(nxt_text) > max_merge_chars:
                break
            cur_text = (cur_text + nxt_text).strip()
            cur_dur += float(nxt.get("duration", 0.0))
            j += 1
        out.append({"text": cur_text, "start": cur_start, "duration": cur_dur})
        i = j
    return out


def _resolve_existing_path(p: Path) -> Path:
    s = str(p).replace("\\", "/")
    # 对于百度网盘工作区，固定优先 E 盘，避免被 D 盘同名目录覆盖
    if s.startswith("D:/BaiduSyncdisk/"):
        prefer_e = Path("E:/" + s[len("D:/"):])
        if prefer_e.exists():
            return prefer_e
    if s.startswith("E:/BaiduSyncdisk/"):
        if Path(s).exists():
            return Path(s)
        alt = Path("D:/" + s[len("E:/"):])
        if alt.exists():
            return alt
        return Path(s)
    if p.exists():
        return p
    if s.startswith("D:/BaiduSyncdisk/"):
        alt = Path("E:/" + s[len("D:/"):])
        if alt.exists():
            return alt
    if s.startswith("E:/BaiduSyncdisk/"):
        alt = Path("D:/" + s[len("E:/"):])
        if alt.exists():
            return alt
    return p


def _rewrite_draft_paths_to_existing(draft_dir: Path) -> None:
    target_files = ["draft_content.json", "draft_content.json.bak", "template-2.tmp", "draft_meta_info.json"]
    for fn in target_files:
        fp = draft_dir / fn
        if not fp.exists():
            continue
        try:
            data = json.loads(fp.read_text(encoding="utf-8-sig"))
        except Exception:
            continue

        def fix_path(s: str) -> str:
            if not s:
                return s
            p = _resolve_existing_path(Path(str(s)))
            return str(p).replace("\\", "/")

        if fn == "draft_meta_info.json":
            for item in data.get("draft_materials", []) or []:
                for v in item.get("value", []) or []:
                    if "file_Path" in v:
                        v["file_Path"] = fix_path(v.get("file_Path", ""))
        else:
            mats = data.get("materials", {}) or {}
            for a in mats.get("audios", []) or []:
                if "path" in a:
                    a["path"] = fix_path(a.get("path", ""))
            for v in mats.get("videos", []) or []:
                if "path" in v:
                    v["path"] = fix_path(v.get("path", ""))
            data["materials"] = mats
        fp.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _extract_subtitle_style_from_sample(sample_draft_dir: Path) -> Dict[str, Any]:
    """从 sample 草稿提取字幕默认样式。"""
    dc = sample_draft_dir / "draft_content.json"
    if not dc.exists():
        return {}
    try:
        data = json.loads(dc.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}

    out: Dict[str, Any] = {}
    texts = ((data.get("materials") or {}).get("texts") or [])
    if texts:
        t0 = texts[0] or {}
        out["font_size"] = t0.get("font_size")
        out["text_color"] = t0.get("text_color")
        out["border_color"] = t0.get("border_color")
        out["border_width"] = t0.get("border_width")
        fonts = t0.get("fonts") or []
        if fonts and isinstance(fonts, list):
            title = (fonts[0] or {}).get("title")
            if title:
                out["font_title"] = title

    text_tracks = [x for x in (data.get("tracks") or []) if x.get("type") == "text"]
    if text_tracks and (text_tracks[0].get("segments") or []):
        seg0 = text_tracks[0]["segments"][0] or {}
        clip = seg0.get("clip") or {}
        transform = clip.get("transform") or {}
        scale = clip.get("scale") or {}
        out["transform_x"] = transform.get("x")
        out["transform_y"] = transform.get("y")
        out["scale_x"] = scale.get("x")
        out["scale_y"] = scale.get("y")

    return {k: v for k, v in out.items() if v is not None}


def _repair_alignment_segments_timing(segments: List[Dict[str, Any]], total_duration_us: int) -> List[Dict[str, Any]]:
    if not segments:
        return segments
    out = [dict(x) for x in segments]

    def is_bad(i: int) -> bool:
        st = int(out[i].get("start", 0) or 0)
        dur = int(out[i].get("duration", 0) or 0)
        if dur <= 0:
            return True
        if i > 0 and st <= int(out[i - 1].get("start", 0) or 0):
            return True
        return False

    i = 0
    while i < len(out):
        if not is_bad(i):
            i += 1
            continue
        j = i
        while j + 1 < len(out) and is_bad(j + 1):
            j += 1

        prev_end = int(out[i - 1].get("end", 0) or 0) if i > 0 else 0
        next_start = int(out[j + 1].get("start", total_duration_us) or total_duration_us) if j + 1 < len(out) else total_duration_us
        if next_start <= prev_end:
            next_start = total_duration_us
        if next_start <= prev_end:
            next_start = prev_end + (j - i + 1) * 1_000

        weights = []
        for k in range(i, j + 1):
            txt = str(out[k].get("text", "")).strip()
            weights.append(max(len(_normalize_text(txt)), 1))
        sw = sum(weights) or (j - i + 1)
        span = max(next_start - prev_end, (j - i + 1) * 1_000)

        cur = prev_end
        remain = span
        for idx, k in enumerate(range(i, j + 1)):
            if idx == (j - i):
                dur = max(remain, 1_000)
            else:
                dur = int(round(span * (weights[idx] / sw)))
                dur = max(dur, 1_000)
                remain = max(remain - dur, 1_000)
            st = cur
            ed = st + dur
            out[k]["start"] = st
            out[k]["end"] = ed
            out[k]["duration"] = max(ed - st, 0)
            cur = ed
        i = j + 1

    for k in range(1, len(out)):
        pst = int(out[k - 1].get("start", 0) or 0)
        ped = int(out[k - 1].get("end", pst) or pst)
        st = int(out[k].get("start", 0) or 0)
        ed = int(out[k].get("end", st) or st)
        if st < ped:
            st = ped
        if ed <= st:
            ed = st + 1_000
        out[k]["start"] = st
        out[k]["end"] = min(ed, total_duration_us)
        out[k]["duration"] = max(int(out[k]["end"]) - st, 0)
    return out


def _segments_too_many_tiny_tail(segments: List[Dict[str, Any]], tiny_us: int = 80_000, tail_n: int = 20) -> bool:
    if not segments:
        return False
    tail = segments[-tail_n:] if len(segments) >= tail_n else segments
    tiny = sum(1 for s in tail if int(s.get("duration", 0) or 0) <= tiny_us)
    return tiny >= max(5, len(tail) // 2)


def _build_segments_from_original_text(original_text: str, total_duration_us: int) -> List[Dict[str, Any]]:
    lines = [x.strip() for x in (original_text or "").splitlines() if x.strip()]
    if not lines:
        return []
    ws = [max(len(_normalize_text(x)), 1) for x in lines]
    sw = sum(ws) or len(lines)
    cur = 0
    out: List[Dict[str, Any]] = []
    remain = total_duration_us
    for i, line in enumerate(lines):
        if i == len(lines) - 1:
            dur = max(remain, 1_000)
        else:
            dur = max(int(round(total_duration_us * (ws[i] / sw))), 1_000)
            remain = max(remain - dur, 1_000)
        out.append({"text": line, "start": cur, "end": cur + dur, "duration": dur})
        cur += dur
    return out


def _find_item_range(
    segments: List[Dict[str, Any]],
    target_text: str,
    cursor: int,
) -> Tuple[int, int, bool]:
    target = _normalize_text(target_text)
    if not target:
        idx = min(max(cursor, 0), len(segments) - 1)
        return idx, idx, False

    for start_idx in range(cursor, len(segments)):
        acc = ""
        lengths: List[int] = []
        for end_idx in range(start_idx, len(segments)):
            piece = _normalize_text(segments[end_idx].get("text", ""))
            acc += piece
            lengths.append(len(piece))
            if target in acc:
                pos = acc.find(target)
                end_pos = pos + len(target) - 1

                cum = 0
                real_start = start_idx
                real_end = end_idx
                for k, ln in enumerate(lengths):
                    left = cum
                    right = cum + ln - 1
                    if ln > 0 and left <= pos <= right:
                        real_start = start_idx + k
                        break
                    cum += ln

                cum = 0
                for k, ln in enumerate(lengths):
                    left = cum
                    right = cum + ln - 1
                    if ln > 0 and left <= end_pos <= right:
                        real_end = start_idx + k
                        break
                    cum += ln
                return real_start, real_end, True
    # fallback
    idx = min(max(cursor, 0), len(segments) - 1)
    return idx, idx, False


def _find_first_segment_start(segments: List[Dict[str, Any]], target_text: str, cursor: int) -> Tuple[int, bool]:
    target = _normalize_text(target_text)
    if not target:
        idx = min(max(cursor, 0), len(segments) - 1)
        return idx, False
    for i in range(cursor, len(segments)):
        cur = _normalize_text(segments[i].get("text", ""))
        if cur and (cur in target or target in cur):
            return i, True
    for i in range(cursor, len(segments)):
        cur = _normalize_text(segments[i].get("text", ""))
        if cur:
            return i, False
    idx = min(max(cursor, 0), len(segments) - 1)
    return idx, False


def _repair_non_increasing_starts(
    cue_rows: List[Dict[str, Any]],
    total_duration_sec: float,
    min_gap_sec: float = 0.2,
) -> bool:
    if len(cue_rows) < 2:
        return False
    first_bad = -1
    for i in range(1, len(cue_rows)):
        if float(cue_rows[i]["start"]) <= float(cue_rows[i - 1]["start"]):
            first_bad = i
            break
    if first_bad < 0:
        return False

    anchor_idx = first_bad - 1
    while anchor_idx > 0:
        rem_count = len(cue_rows) - (anchor_idx + 1)
        rem_span = total_duration_sec - float(cue_rows[anchor_idx]["start"])
        if rem_count <= 0 or rem_span >= rem_count * min_gap_sec:
            break
        anchor_idx -= 1

    redistrib_start_idx = anchor_idx + 1
    anchor_start = float(cue_rows[anchor_idx]["start"])
    remaining_count = len(cue_rows) - redistrib_start_idx
    if remaining_count <= 0:
        return False

    available_span = max(total_duration_sec - anchor_start, min_gap_sec * remaining_count)
    weights: List[float] = []
    for row in cue_rows[redistrib_start_idx:]:
        narration = str((row.get("item") or {}).get("narration", "")).strip()
        weights.append(float(max(len(_normalize_text(narration)), 1)))
    total_weight = sum(weights) if weights else float(remaining_count)

    cum = 0.0
    for i, w in enumerate(weights):
        frac = (cum / total_weight) if total_weight > 0 else (i / remaining_count)
        s = anchor_start + available_span * frac
        if i == 0:
            s = max(s, anchor_start + min_gap_sec)
        else:
            prev_s = float(cue_rows[redistrib_start_idx + i - 1]["start"])
            s = max(s, prev_s + min_gap_sec)
        cue_rows[redistrib_start_idx + i]["start"] = min(s, total_duration_sec - min_gap_sec)
        cue_rows[redistrib_start_idx + i]["timing_repaired"] = True
        cum += w
    return True


def _ensure_track_ids(draft_para_collect: Dict[str, Any], track_ids: Dict[str, str]) -> None:
    tracks = draft_para_collect.get("tracks", {}) or {}
    for key, tid in (("video_track", track_ids["video"]), ("texts_track", track_ids["text"]), ("audios_track", track_ids["audio"])):
        arr = tracks.get(key, []) or []
        if arr:
            arr[-1]["id"] = tid
            tracks[key] = arr
    draft_para_collect["tracks"] = tracks


def _normalize_material_animations(draft_para_collect: Dict[str, Any]) -> None:
    for key in ("videos", "texts"):
        for item in draft_para_collect.get(key, []) or []:
            tr = item.get("tracks", {}) or {}
            ma = tr.get("material_animations")
            if not isinstance(ma, dict):
                ma = {}
            if not isinstance(ma.get("animations"), list):
                ma["animations"] = []
            tr["material_animations"] = ma
            item["tracks"] = tr


def _normalize_track_render_index_compat(draft_para_collect: Dict[str, Any]) -> None:
    # Compatibility for current complete_tracks_builder_fixed:
    # it treats audio track_render_index as ordinal list index.
    tracks = draft_para_collect.get("tracks", {}) or {}
    audios_track = tracks.get("audios_track", []) or []
    if len(audios_track) == 1:
        audios_track[0]["track_render_index"] = 0
        tracks["audios_track"] = audios_track
        for a in draft_para_collect.get("audios", []) or []:
            tr = a.get("tracks", {}) or {}
            tr["track_render_index"] = 0
            a["tracks"] = tr
    draft_para_collect["tracks"] = tracks


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose Jianying draft from aligned subtitles + storyboard images + dubbing audio.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--aligned-json", default="", help="Default: <project>/output/aligned_asr.json")
    parser.add_argument("--storyboard-json", default="", help="Default: <project>/output/storyboard_sequence.json")
    parser.add_argument("--audio-path", required=True)
    parser.add_argument("--ref-srt", default="", help="Optional ASR SRT for timing-window calibration.")
    parser.add_argument("--config", default="")
    parser.add_argument("--template-id", default="", help="Template id under user_data/templates, e.g. template1/template2.")
    parser.add_argument("--image-scale-x", type=float, default=None, help="CLI override for image scale x.")
    parser.add_argument("--image-scale-y", type=float, default=None, help="CLI override for image scale y.")
    parser.add_argument("--image-transform-x", type=float, default=None, help="CLI override for image transform x.")
    parser.add_argument("--image-transform-y", type=float, default=None, help="CLI override for image transform y.")
    parser.add_argument("--save-params", default="")
    parser.add_argument(
        "--allow-rebuild-fallback",
        action="store_true",
        help="Allow rebuilding timing from original text when tail segments are too tiny (disabled by default).",
    )
    parser.add_argument("--subtitle-max-chars", type=int, default=18, help="Max chars for one subtitle chunk.")
    parser.add_argument("--subtitle-min-duration", type=float, default=0.35, help="Min duration seconds per subtitle chunk.")
    parser.add_argument("--subtitle-min-show", type=float, default=0.9, help="Min display duration after merge.")
    parser.add_argument("--subtitle-merge-max-chars", type=int, default=22, help="Max chars allowed when merging short subtitle chunks.")
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Only generate draft_para_collect and timeline json, skip draft composition.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    sys.path.insert(0, str(project_root))
    config_path = Path(args.config).resolve() if args.config else None
    cfg = load_runtime_config(project_root, config_path)
    defaults = (((cfg.get("defaults") or {}).get("compose")) or {})
    template_id = (args.template_id or "").strip() or str(cfg.get("default_template_id", "")).strip()
    template_cfg = _load_template_cfg(project_root, template_id)
    cfg = _deep_merge_dict(cfg, template_cfg)
    if args.image_scale_x is not None:
        cfg.setdefault("image_style", {})["scale_x"] = float(args.image_scale_x)
    if args.image_scale_y is not None:
        cfg.setdefault("image_style", {})["scale_y"] = float(args.image_scale_y)
    if args.image_transform_x is not None:
        cfg.setdefault("image_style", {})["transform_x"] = float(args.image_transform_x)
    if args.image_transform_y is not None:
        cfg.setdefault("image_style", {})["transform_y"] = float(args.image_transform_y)

    aligned_default = str(defaults.get("aligned_json") or "output/aligned_asr.json")
    storyboard_default = str(defaults.get("storyboard_json") or "output/storyboard_sequence.json")
    save_params_default = str(defaults.get("save_params") or "output/draft_para_collect_from_assets.json")
    aligned_path = Path(args.aligned_json).resolve() if args.aligned_json else (project_root / aligned_default)
    storyboard_path = Path(args.storyboard_json).resolve() if args.storyboard_json else (project_root / storyboard_default)
    if not aligned_path.exists():
        raise FileNotFoundError(f"aligned json not found: {aligned_path}")
    if not storyboard_path.exists():
        raise FileNotFoundError(f"storyboard json not found: {storyboard_path}")
    aligned = json.loads(aligned_path.read_text(encoding="utf-8"))
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    segments = ((aligned.get("alignment_result") or {}).get("segments") or [])
    if not segments:
        raise ValueError("aligned json has no segments")
    total_duration_us = int(((aligned.get("alignment_result") or {}).get("total_duration", 0) or 0))
    if total_duration_us <= 0:
        total_duration_us = int(max(int(s.get("end", 0) or 0) for s in segments))
    segments = _repair_alignment_segments_timing(segments, total_duration_us)
    if args.allow_rebuild_fallback and _segments_too_many_tiny_tail(segments):
        rebuilt = _build_segments_from_original_text(str(aligned.get("original_text", "")), total_duration_us)
        if rebuilt:
            segments = rebuilt
    if args.ref_srt:
        srt_path = Path(args.ref_srt).resolve()
        if srt_path.exists():
            srt_rows = _read_srt_rows(srt_path)
            if srt_rows:
                segments = _calibrate_segments_with_srt_windows(segments, srt_rows)

    from utility.draft_para_collect import DraftParaCollect
    from utility.draft_config_comb import DraftConfigComb

    canvas_cfg = cfg.get("canvas", {}) or {}
    subtitle_style_cfg = cfg.get("subtitle_style", {}) or {}
    sample_style_dir = cfg.get("subtitle_style_sample_draft", "D:/JianyingPro Drafts/sample")
    sample_style = _extract_subtitle_style_from_sample(Path(str(sample_style_dir)))
    subtitle_style = {**sample_style, **subtitle_style_cfg}
    image_style = cfg.get("image_style", {}) or {}
    extra_text_overlays = cfg.get("extra_text_overlays", []) or []
    draft_parent = cfg.get("draft_parent_folder", "F:/JianyingPro Drafts")

    collector = DraftParaCollect(save_path=str(project_root / "output"))
    draft_para_collect = collector.set_canvas(
        width=int(canvas_cfg.get("width", 1920)),
        height=int(canvas_cfg.get("height", 1080)),
        jianying_folder_path=str(canvas_cfg.get("jianying_folder_path", "")),
        source_draft_fold_path="",
        output_parent_draft_folder_path=str(draft_parent),
    )

    draft_para_collect, video_track_id, _ = collector.add_track(draft_para_collect, "video")
    draft_para_collect, text_track_id, _ = collector.add_track(draft_para_collect, "text")
    draft_para_collect, audio_track_id, _ = collector.add_track(draft_para_collect, "audio")
    _ensure_track_ids(
        draft_para_collect,
        {"video": video_track_id, "text": text_track_id, "audio": audio_track_id},
    )

    # subtitles for display layer: directly use aligned ASR short-sentence timeline
    # (no second-round split/merge) to keep full consistency with image timing.
    display_subtitles: List[Dict[str, Any]] = []
    for seg in segments:
        txt = str(seg.get("text", "")).strip()
        if not txt:
            continue
        st, ed = _segment_time_sec(seg)
        dur = max(ed - st, 0.001)
        display_subtitles.append({"text": txt, "start": st, "duration": dur})
    for row in display_subtitles:
        draft_para_collect, _ = collector.add_text(
            draft_para_collect=draft_para_collect,
            track_id=text_track_id,
            content=str(row.get("text", "")).strip(),
            font_path="",
            font_resource_id="",
            fonts_title=str(subtitle_style.get("font_title", "系统")),
            text_color=str(subtitle_style.get("text_color", "#FFFFFF")),
            border_color=str(subtitle_style.get("border_color", "#000000")),
            border_width=float(subtitle_style.get("border_width", 40.0)),
            font_size=float(subtitle_style.get("font_size", 12.0)),
            start=float(row.get("start", 0.0)),
            duration=float(row.get("duration", 0.001)),
            transform_x=float(subtitle_style.get("transform_x", 0.0)),
            transform_y=float(subtitle_style.get("transform_y", -0.9259259259259259)),
            scale_x=float(subtitle_style.get("scale_x", 1.0)),
            scale_y=float(subtitle_style.get("scale_y", 1.0)),
            text_alpha=1.0,
        )

    # storyboard items aligned by narration start time
    items = storyboard.get("items", []) or []
    cue_rows = []
    cursor = 0
    image_timeline = []
    total_duration_sec = float(total_duration_us / 1_000_000.0)
    black_path_cfg = str((cfg.get("black_material", {}) or {}).get("path", "user_data/materials/black_scene.png"))
    black_path_abs = (project_root / black_path_cfg).resolve()

    for item in items:
        item_type = item.get("item_type", "image")
        if item_type == "black_note":
            material_path = black_path_abs
            image_name = material_path.name
        else:
            material_path = _resolve_existing_path(Path(item.get("image_abs_path", "")))
            image_name = item.get("image_name")
        if not material_path.exists():
            continue
        s_idx, e_idx, matched = _find_item_range(segments, item.get("narration", ""), cursor)
        s0, _ = _segment_time_sec(segments[s_idx])
        cue_rows.append(
            {
                "item": item,
                "item_type": item_type,
                "material_path": str(material_path).replace("\\", "/"),
                "image_name": image_name,
                "segment_index": s_idx,
                "start": s0,
                "matched": matched,
                "end_segment_index": e_idx,
            }
        )
        cursor = min(e_idx + 1, len(segments) - 1)

    repaired = _repair_non_increasing_starts(cue_rows, total_duration_sec, min_gap_sec=0.2)

    # Keep the very first image on screen from time zero even if ASR starts slightly later.
    if cue_rows:
        cue_rows[0]["start"] = 0.0

    for i, row in enumerate(cue_rows):
        start = row["start"]
        next_start = cue_rows[i + 1]["start"] if i + 1 < len(cue_rows) else total_duration_sec
        duration = max(next_start - start, 0.2)
        draft_para_collect, _ = collector.add_video(
            draft_para_collect=draft_para_collect,
            track_id=video_track_id,
            path=row["material_path"],
            width=int(canvas_cfg.get("width", 1920)),
            height=int(canvas_cfg.get("height", 1080)),
            start=float(start),
            duration=float(duration),
            transform_x=float(image_style.get("transform_x", 0.0)),
            transform_y=float(image_style.get("transform_y", 0.0)),
            scale_x=float(image_style.get("scale_x", 1.0)),
            scale_y=float(image_style.get("scale_y", 1.0)),
        )
        image_timeline.append(
            {
                "index": row["item"].get("index"),
                "item_type": row["item_type"],
                "image_name": row["image_name"],
                "start": start,
                "duration": duration,
                "segment_start_index": row["segment_index"],
                "segment_end_index": row.get("end_segment_index"),
                "matched": row["matched"],
                "timing_repaired": bool(row.get("timing_repaired", False)),
            }
        )

    # dubbing audio
    draft_para_collect, _ = collector.add_audios(
        draft_para_collect=draft_para_collect,
        track_id=audio_track_id,
        start=0.0,
        duration=total_duration_sec,
        material_duration=total_duration_sec,
        path=str(_resolve_existing_path(Path(args.audio_path).resolve())).replace("\\", "/"),
        name=Path(args.audio_path).name,
        volume=1.0,
    )

    # optional extra text overlays (e.g. disclaimer/title strip)
    if extra_text_overlays:
        draft_para_collect, extra_text_track_id, _ = collector.add_track(draft_para_collect, "text")
        tracks_obj = draft_para_collect.get("tracks", {}) or {}
        texts_track = tracks_obj.get("texts_track", []) or []
        if texts_track:
            texts_track[-1]["id"] = extra_text_track_id
            tracks_obj["texts_track"] = texts_track
            draft_para_collect["tracks"] = tracks_obj
        total_duration_sec = float(total_duration_us / 1_000_000.0)
        canvas_w = float(canvas_cfg.get("width", 1920) or 1920)
        canvas_h = float(canvas_cfg.get("height", 1080) or 1080)
        for ov in extra_text_overlays:
            txt = str((ov or {}).get("text", "")).strip()
            if not txt:
                continue
            st = float((ov or {}).get("start", 0.0) or 0.0)
            dur = (ov or {}).get("duration")
            if dur is None:
                dur = max(total_duration_sec - st, 0.2)
            dur = max(float(dur), 0.2)
            tx = (ov or {}).get("transform_x")
            ty = (ov or {}).get("transform_y")
            tx_px = (ov or {}).get("transform_x_px")
            ty_px = (ov or {}).get("transform_y_px")
            if tx_px is not None:
                tx = float(tx_px) / canvas_w
            if ty_px is not None:
                ty = float(ty_px) / canvas_h
            if tx is None:
                tx = 0.0
            if ty is None:
                ty = -0.9259259259259259
            draft_para_collect, _ = collector.add_text(
                draft_para_collect=draft_para_collect,
                track_id=extra_text_track_id,
                content=txt,
                font_path="",
                font_resource_id="",
                fonts_title=str((ov or {}).get("font_title", subtitle_style.get("font_title", "系统"))),
                text_color=str((ov or {}).get("text_color", subtitle_style.get("text_color", "#FFFFFF"))),
                border_color=str((ov or {}).get("border_color", subtitle_style.get("border_color", "#000000"))),
                border_width=float((ov or {}).get("border_width", subtitle_style.get("border_width", 40.0))),
                font_size=float((ov or {}).get("font_size", subtitle_style.get("font_size", 12.0))),
                start=st,
                duration=dur,
                transform_x=float(tx),
                transform_y=float(ty),
                scale_x=float((ov or {}).get("scale_x", 1.0)),
                scale_y=float((ov or {}).get("scale_y", 1.0)),
                text_alpha=float((ov or {}).get("text_alpha", 1.0)),
                background_style=int((ov or {}).get("background_style", 0)),
                background_color=str((ov or {}).get("background_color", "#000000")),
                background_width=float((ov or {}).get("background_width", 0.14)),
                background_height=float((ov or {}).get("background_height", 0.14)),
                background_round_radius=float((ov or {}).get("background_round_radius", 0.0)),
                global_alpha=float((ov or {}).get("global_alpha", 1.0)),
                check_flag=int((ov or {}).get("check_flag", 15)),
            )

    _normalize_material_animations(draft_para_collect)
    _normalize_track_render_index_compat(draft_para_collect)
    draft_para_collect = collector.close_canvas(draft_para_collect)

    # persist params
    save_params = Path(args.save_params).resolve() if args.save_params else (project_root / save_params_default)
    save_params.parent.mkdir(parents=True, exist_ok=True)
    save_params.write_text(json.dumps(draft_para_collect, ensure_ascii=False, indent=2), encoding="utf-8")

    image_timeline_path = project_root / "output" / "image_timeline_from_storyboard.json"
    image_timeline_path.write_text(
        json.dumps(
            {
                "status": "success",
                "total_items": len(image_timeline),
                "timing_repaired": repaired,
                "items": image_timeline,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    subtitle_timeline_path = project_root / "output" / "subtitle_timeline_display.json"
    subtitle_timeline_path.write_text(
        json.dumps(
            {
                "status": "success",
                "total_items": len(display_subtitles),
                "subtitle_max_chars": int(args.subtitle_max_chars),
                "subtitle_min_duration": float(args.subtitle_min_duration),
                "items": display_subtitles,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    draft_path = ""
    if not args.plan_only:
        comb = DraftConfigComb()
        draft_path = comb.execute_draft_composition(draft_para_collect)
        _rewrite_draft_paths_to_existing(Path(draft_path))
    print(str(save_params))
    print(str(image_timeline_path.resolve()))
    print(str(subtitle_timeline_path.resolve()))
    if draft_path:
        print(str(Path(draft_path).resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
