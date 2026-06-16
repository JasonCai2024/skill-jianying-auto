import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

try:
    from ..utils.logger import get_logger
except ImportError:
    import sys
    from pathlib import Path as _Path
    sys.path.insert(0, str(_Path(__file__).parent.parent.parent))
    from utils.logger import get_logger


logger = get_logger(__name__)


def _norm_text(s: str) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", (s or ""))


def _strip_punc_keep_text(s: str) -> str:
    return re.sub(r"[，。！？；：、,.!?;:\s\r\n\t]+", "", (s or ""))


@dataclass
class WordSeg:
    text: str
    start: float
    end: float


class ServiceHubASRProcessor:
    def __init__(self, config: Dict[str, Any], project_root: Path) -> None:
        self.config = config
        self.project_root = project_root
        self.local_credentials = self._load_local_credentials()
        self.mid_dir = project_root / "output" / "asr_mid"
        self.mid_dir.mkdir(parents=True, exist_ok=True)
        self.oss_url = ""

    def _load_local_credentials(self) -> Dict[str, Any]:
        p = self.project_root / "data" / "credentials.json"
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            return {}

    def _dump_mid(self, name: str, data: Any) -> None:
        fp = self.mid_dir / name
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _get_skill_cfg(self, key: str) -> Dict[str, Any]:
        v = self.config.get(key)
        return v if isinstance(v, dict) else {}

    def _get_local_cfg(self, key: str) -> Dict[str, Any]:
        v = self.local_credentials.get(key)
        return v if isinstance(v, dict) else {}

    def _servicehub_url(self, path: str) -> str:
        c = self._get_skill_cfg("servicehub")
        l = self._get_local_cfg("servicehub")
        wp = self.local_credentials.get("wechat_proxy") or {}
        base = str(c.get("base_url") or l.get("base_url") or wp.get("remote_service_url") or "https://www.ccailab.top").rstrip("/")
        if not base.startswith("http"):
            base = "https://" + base
        return f"{base}{path}"

    def _servicehub_auth(self) -> Tuple[str, str]:
        c = self._get_skill_cfg("servicehub")
        l = self._get_local_cfg("servicehub")
        wp = self.local_credentials.get("wechat_proxy") or {}
        username = str(c.get("username") or l.get("username") or wp.get("username") or "").strip()
        passtoken = str(c.get("passtoken") or l.get("passtoken") or wp.get("passtoken") or "").strip()
        return username, passtoken

    def _upload_to_oss(self, local_audio: Path) -> str:
        username, passtoken = self._servicehub_auth()
        if not username or not passtoken:
            raise ValueError("缺少 ServiceHub 账号: 请通过命令行参数、环境变量/.env 或 data/credentials.json 提供。")

        url = self._servicehub_url("/api/oss/upload-audio")
        with local_audio.open("rb") as fh:
            files = {
                "audio_file": (local_audio.name, fh, "application/octet-stream"),
            }
            data = {
                "username": username,
                "passtoken": passtoken,
                "filename": local_audio.name,
            }
            resp = requests.post(url, data=data, files=files, timeout=300)
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success"):
            raise RuntimeError(f"OSS 上传失败: {payload.get('message') or payload}")

        result = payload.get("data") or {}
        oss_url = str(result.get("oss_url") or "").strip()
        object_name = str(result.get("object_name") or "").strip()
        if not oss_url:
            raise RuntimeError(f"OSS 上传返回缺少 oss_url: {payload}")

        self._dump_mid(
            "01_oss_upload.json",
            {
                "local_audio": str(local_audio),
                "oss_url": oss_url,
                "object_name": object_name,
                "servicehub_url": url,
            },
        )
        return oss_url

    def _delete_oss(self, oss_url: str) -> None:
        if not oss_url:
            return
        try:
            username, passtoken = self._servicehub_auth()
            if not username or not passtoken:
                raise ValueError("缺少 ServiceHub 账号，无法删除 OSS 临时音频。")

            url = self._servicehub_url("/api/oss/delete-audio")
            payload = {
                "username": username,
                "passtoken": passtoken,
                "oss_url": oss_url,
            }
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                raise RuntimeError(f"OSS 删除失败: {data.get('message') or data}")
            self._dump_mid(
                "99_oss_delete.json",
                {
                    "oss_url": oss_url,
                    "deleted": bool(((data.get("data") or {}).get("deleted"))),
                    "object_name": (data.get("data") or {}).get("object_name"),
                    "servicehub_url": url,
                },
            )
        except Exception as e:
            self._dump_mid("99_oss_delete.json", {"oss_url": oss_url, "deleted": False, "error": str(e)})

    def _call_servicehub(self, path: str, payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        url = self._servicehub_url(path)
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _call_asr_word_timestamps(self, oss_url: str) -> Dict[str, Any]:
        username, passtoken = self._servicehub_auth()
        if not username or not passtoken:
            raise ValueError("缺少 ServiceHub 账号: 请通过命令行参数、环境变量/.env 或 data/credentials.json 提供。")

        sh = self._get_skill_cfg("servicehub")
        payload = {
            "username": username,
            "passtoken": passtoken,
            "provider": str(sh.get("asr_provider") or "aliyun"),
            "model": str(sh.get("asr_model") or "paraformer-v2"),
            "transcript_format": "word_timestamps",
            "media_url": oss_url,
            "deduct_points": bool(sh.get("deduct_points", True)),
        }
        data = self._call_servicehub("/api/asr/paid-rotation", payload, timeout=900)
        self._dump_mid("02_asr_word_raw.json", data)
        if int(data.get("code", 0)) != 200:
            raise RuntimeError(f"ASR调用失败: {data.get('message')}")
        return data

    def _extract_word_segments(self, asr_response: Dict[str, Any]) -> List[WordSeg]:
        data = asr_response.get("data") or {}
        segs = data.get("transcript_segments") or []
        out: List[WordSeg] = []
        raw_times: List[float] = []

        for seg in segs:
            if not isinstance(seg, dict):
                continue
            for k in ("start", "start_time", "begin_time", "end", "end_time", "finish_time"):
                v = seg.get(k)
                if isinstance(v, (int, float)):
                    raw_times.append(float(v))
        use_ms = max(raw_times) > 1000 if raw_times else False

        def push(text: str, st: Any, ed: Any) -> None:
            t = str(text or "").strip()
            if not t:
                return
            try:
                s = float(st) / 1000.0 if use_ms else float(st)
                e = float(ed) / 1000.0 if use_ms else float(ed)
            except Exception:
                return
            if e <= s:
                return
            out.append(WordSeg(text=t, start=s, end=e))

        for seg in segs:
            if isinstance(seg, dict):
                if isinstance(seg.get("words"), list):
                    for w in seg.get("words") or []:
                        push(w.get("text") or w.get("word"), w.get("start") or w.get("start_time") or w.get("begin_time"), w.get("end") or w.get("end_time") or w.get("finish_time"))
                else:
                    push(seg.get("text") or seg.get("word"), seg.get("start") or seg.get("start_time") or seg.get("begin_time"), seg.get("end") or seg.get("end_time") or seg.get("finish_time"))

        if not out:
            raise RuntimeError("ASR返回中未解析到 word_timestamps 片段")
        self._dump_mid("03_word_segments.json", [x.__dict__ for x in out])
        return out

    def _call_llm_correct(self, asr_text: str, script_text: str) -> str:
        username, passtoken = self._servicehub_auth()
        sh = self._get_skill_cfg("servicehub")
        payload = {
            "username": username,
            "passtoken": passtoken,
            "task_type": "text_arrange",
            "provider": str(sh.get("llm_provider") or "aliyun"),
            "model": str(sh.get("llm_model") or "qwen-flash"),
            "deduct_points": bool(sh.get("deduct_points", True)),
            "user_prompt": (
                "你是字幕纠错器。给你ASR文本与原始口播文案，请输出纠错后的完整文本。"
                "要求：1) 以原始口播文案为准；2) 仅做错别字与同音误识修正；3) 不扩写。"
                "4) 严禁添加或删除任何标点符号、换行符。5) 输出必须是连续文本。"
                "严格输出JSON: {\"corrected_text\":\"...\"}\n\n"
                f"【ASR文本】\n{asr_text}\n\n【原始口播文案】\n{script_text}"
            ),
        }
        self._dump_mid("04_llm_correct_request.json", payload)
        data = self._call_servicehub("/api/llm/paid-rotation", payload, timeout=300)
        self._dump_mid("05_llm_correct_response.json", data)
        if int(data.get("code", 0)) != 200:
            return script_text
        processed = str(((data.get("data") or {}).get("processed_text") or "")).strip()
        m = re.search(r"\{[\s\S]*\}", processed)
        text = m.group(0) if m else processed
        try:
            obj = json.loads(text)
            corrected = str(obj.get("corrected_text") or "").strip()
            if corrected:
                corrected = _strip_punc_keep_text(corrected)
                ln_script = max(len(_norm_text(script_text)), 1)
                ln_corr = len(_norm_text(corrected))
                if abs(ln_corr - ln_script) / ln_script > 0.15:
                    return _strip_punc_keep_text(script_text)
                return corrected
        except Exception:
            pass
        return _strip_punc_keep_text(script_text)

    def _symbol_split_by_script(self, script_text: str) -> List[str]:
        blocks = re.split(r"[\r\n]+", script_text or "")
        out: List[str] = []
        for b in blocks:
            parts = re.split(r"[，、。！？；!?;,]+", b)
            for p in parts:
                seg = _strip_punc_keep_text(p)
                if seg:
                    out.append(seg)
        return out

    def _call_llm_split_long_line(self, text: str, max_chars: int) -> List[str]:
        username, passtoken = self._servicehub_auth()
        sh = self._get_skill_cfg("servicehub")
        payload = {
            "username": username,
            "passtoken": passtoken,
            "task_type": "text_arrange",
            "provider": str(sh.get("llm_provider") or "aliyun"),
            "model": str(sh.get("llm_model") or "qwen-flash"),
            "deduct_points": bool(sh.get("deduct_points", True)),
            "user_prompt": (
                "请将下列单句长字幕按语义切分为2到3句。"
                f"每句不超过{max_chars}个汉字；不得改变字词顺序；不得增删字词；不得添加标点。"
                "严格输出JSON: {\"lines\":[\"...\",\"...\"]}\n\n"
                f"{text}"
            ),
        }
        self._dump_mid("07b_llm_longline_request.json", payload)
        data = self._call_servicehub("/api/llm/paid-rotation", payload, timeout=300)
        self._dump_mid("07c_llm_longline_response.json", data)
        if int(data.get("code", 0)) != 200:
            return self._fallback_rechunk(text, max_chars)

        processed = str(((data.get("data") or {}).get("processed_text") or "")).strip()
        m = re.search(r"\{[\s\S]*\}", processed)
        raw = m.group(0) if m else processed
        try:
            obj = json.loads(raw)
            lines = [_strip_punc_keep_text(str(x)) for x in (obj.get("lines") or []) if str(x).strip()]
            lines = [x for x in lines if x]
            if lines:
                # 强校验：仅允许“切分”，不允许丢字/改序/增字
                src = _norm_text(text)
                merged = _norm_text("".join(lines))
                bad_len = any(len(_norm_text(x)) > max_chars for x in lines)
                if merged == src and not bad_len:
                    return lines
        except Exception:
            pass
        return self._fallback_rechunk(text, max_chars)

    def _fallback_rechunk(self, text: str, max_chars: int) -> List[str]:
        pieces = re.split(r"(?<=[。！？；!?;])", text)
        pieces = [p.strip() for p in pieces if p.strip()]
        out: List[str] = []
        for p in pieces:
            if len(_norm_text(p)) <= max_chars:
                out.append(p)
                continue
            i = 0
            while i < len(p):
                out.append(p[i:i + max_chars])
                i += max_chars
        return out

    def _build_asr_char_timeline(self, words: List[WordSeg]) -> List[Dict[str, Any]]:
        timeline: List[Dict[str, Any]] = []
        for w in words:
            chars = [c for c in w.text if c.strip()]
            if not chars:
                continue
            dur = max(w.end - w.start, 0.001)
            step = dur / len(chars)
            cur = w.start
            for c in chars:
                timeline.append({"char": c, "norm": _norm_text(c), "start": cur, "end": cur + step})
                cur += step
        timeline = [x for x in timeline if x["norm"]]
        self._dump_mid("09_asr_char_timeline.json", timeline[:5000])
        return timeline

    def _lcs_pairs(self, a: str, b: str) -> List[Tuple[int, int]]:
        n, m = len(a), len(b)
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            ai = a[i - 1]
            row = dp[i]
            prow = dp[i - 1]
            for j in range(1, m + 1):
                if ai == b[j - 1]:
                    row[j] = prow[j - 1] + 1
                else:
                    row[j] = row[j - 1] if row[j - 1] >= prow[j] else prow[j]
        i, j = n, m
        pairs: List[Tuple[int, int]] = []
        while i > 0 and j > 0:
            if a[i - 1] == b[j - 1]:
                pairs.append((i - 1, j - 1))
                i -= 1
                j -= 1
            elif dp[i - 1][j] >= dp[i][j - 1]:
                i -= 1
            else:
                j -= 1
        pairs.reverse()
        return pairs

    def _map_text_to_timing(self, target_text: str, asr_timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        asr_norm = "".join(x["norm"] for x in asr_timeline)
        target_chars = [c for c in target_text if _norm_text(c)]
        target_norm = "".join(_norm_text(c) for c in target_chars)

        pairs = self._lcs_pairs(target_norm, asr_norm)
        self._dump_mid("10_lcs_pairs.json", {"pair_count": len(pairs), "target_len": len(target_norm), "asr_len": len(asr_norm)})

        target_time: List[Dict[str, Any]] = [{"char": c, "start": None, "end": None} for c in target_chars]
        for ti, ai in pairs:
            target_time[ti]["start"] = asr_timeline[ai]["start"]
            target_time[ti]["end"] = asr_timeline[ai]["end"]

        # fill gaps by nearest interpolation
        valid_idx = [i for i, x in enumerate(target_time) if x["start"] is not None]
        if not valid_idx:
            raise RuntimeError("文本对齐失败：LCS无匹配")

        first = valid_idx[0]
        for i in range(0, first):
            target_time[i]["start"] = target_time[first]["start"]
            target_time[i]["end"] = target_time[first]["end"]

        last = valid_idx[-1]
        for i in range(last + 1, len(target_time)):
            target_time[i]["start"] = target_time[last]["start"]
            target_time[i]["end"] = target_time[last]["end"]

        prev = first
        for idx in valid_idx[1:]:
            if idx - prev > 1:
                s0 = target_time[prev]["start"]
                s1 = target_time[idx]["start"]
                step = (s1 - s0) / (idx - prev)
                for k in range(prev + 1, idx):
                    ss = s0 + step * (k - prev)
                    target_time[k]["start"] = ss
                    target_time[k]["end"] = ss + max(step * 0.9, 0.03)
            prev = idx

        self._dump_mid("11_target_char_timing.json", target_time[:5000])
        return target_time

    def _segments_from_lines(self, lines: List[str], target_char_timing: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        segments: List[Dict[str, Any]] = []
        cursor = 0
        for i, line in enumerate(lines):
            nline = [c for c in line if _norm_text(c)]
            if not nline:
                continue
            need = len(nline)
            if cursor >= len(target_char_timing):
                break
            end_idx = min(cursor + need - 1, len(target_char_timing) - 1)
            st = float(target_char_timing[cursor]["start"])
            ed = float(target_char_timing[end_idx]["end"])
            if ed <= st:
                ed = st + 0.2
            duration = ed - st

            disp_chars = [c for c in line if c.strip()]
            step = duration / max(len(disp_chars), 1)
            starts = [int(step * j * 1000) for j in range(len(disp_chars))]
            ends = [int(step * (j + 1) * 1000) for j in range(len(disp_chars))]

            segments.append({
                "text": line,
                "start": int(st * 1_000_000),
                "end": int(ed * 1_000_000),
                "duration": int(duration * 1_000_000),
                "words": {
                    "group_id": f"ASR_{i}",
                    "text": disp_chars,
                    "start_time": starts,
                    "end_time": ends,
                },
            })
            cursor = end_idx + 1

        if not segments:
            raise RuntimeError("未生成有效字幕段")
        self._dump_mid("12_aligned_segments.json", segments)
        return segments

    def process(self, audio_path: Path, script_text: str, max_chars: int = 18) -> List[Dict[str, Any]]:
        try:
            self.oss_url = self._upload_to_oss(audio_path)
            asr = self._call_asr_word_timestamps(self.oss_url)
            words = self._extract_word_segments(asr)
            asr_text = "".join(w.text for w in words)
            corrected_text = self._call_llm_correct(asr_text, script_text)
            self._dump_mid("04b_corrected_text.json", {"asr_text": asr_text, "corrected_text": corrected_text})
            symbol_lines = self._symbol_split_by_script(script_text)
            symbol_lines = [_strip_punc_keep_text(x) for x in symbol_lines if _strip_punc_keep_text(x)]
            corrected_plain = _strip_punc_keep_text(corrected_text)
            # 使用“文案符号边界”切分“纠错后文本”
            symbol_lengths = [len(x) for x in symbol_lines]
            symbol_lines_from_corrected: List[str] = []
            pos = 0
            for ln in symbol_lengths:
                if ln <= 0:
                    continue
                symbol_lines_from_corrected.append(corrected_plain[pos:pos + ln])
                pos += ln
            if pos < len(corrected_plain):
                tail = corrected_plain[pos:]
                if tail:
                    symbol_lines_from_corrected.append(tail)
            self._dump_mid(
                "06_symbol_split_lines.json",
                {
                    "lines_by_script_punc": symbol_lines,
                    "lines_on_corrected": symbol_lines_from_corrected,
                },
            )

            final_lines: List[str] = []
            for line in symbol_lines_from_corrected:
                if len(_norm_text(line)) <= max_chars:
                    final_lines.append(line)
                    continue
                sub_lines = self._call_llm_split_long_line(line, max_chars=max_chars)
                if not sub_lines:
                    sub_lines = self._fallback_rechunk(line, max_chars=max_chars)
                final_lines.extend(sub_lines)
            self._dump_mid("08_rechunk_lines.json", {"lines": final_lines})

            char_timeline = self._build_asr_char_timeline(words)
            target_timing = self._map_text_to_timing(corrected_text, char_timeline)
            return self._segments_from_lines(final_lines, target_timing)
        finally:
            self._delete_oss(self.oss_url)
