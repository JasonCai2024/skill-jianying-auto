"""
剪辑合成模块检查器：用于校验生成草稿配置文件的根键修改是否符合输入参数
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .draft_config_utility import DraftConfigUtility


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_duration(duration: Any) -> Optional[int]:
    if duration is None:
        return None
    if isinstance(duration, (int, float)):
        return int(duration * 1000000)
    return None


def _check_canvas_fields(
    input_params: Dict[str, Any],
    draft_content: Dict[str, Any],
    issues: List[str]
) -> None:
    canvas = input_params.get("canvas", {}) or {}
    if not canvas:
        return

    expected_id = canvas.get("id")
    if expected_id is not None:
        actual_id = draft_content.get("id")
        if actual_id != expected_id:
            issues.append(f"draft_content.id 不一致: expected={expected_id} actual={actual_id}")

    canvas_config = draft_content.get("canvas_config", {}) or {}
    expected_height = canvas.get("height")
    expected_width = canvas.get("width")
    if expected_height is not None:
        actual_height = canvas_config.get("height")
        if actual_height != expected_height:
            issues.append(f"canvas_config.height 不一致: expected={expected_height} actual={actual_height}")
    if expected_width is not None:
        actual_width = canvas_config.get("width")
        if actual_width != expected_width:
            issues.append(f"canvas_config.width 不一致: expected={expected_width} actual={actual_width}")

    expected_duration = _normalize_duration(canvas.get("duration"))
    if expected_duration is not None:
        actual_duration = draft_content.get("duration")
        if actual_duration != expected_duration:
            issues.append(f"draft_content.duration 不一致: expected={expected_duration} actual={actual_duration}")


def _normalize_path(value: str) -> str:
    return (value or "").replace("\\", "/")


def _normalize_hex_color(value: str, default: str) -> str:
    if not value:
        value = default
    value = value.strip()
    if not value.startswith("#"):
        value = f"#{value}"
    return value.lower()


def _hex_to_rgb01(value: str) -> List[float]:
    value = (value or "").lstrip("#")
    if len(value) != 6:
        return [1.0, 1.0, 1.0]
    r = int(value[0:2], 16) / 255.0
    g = int(value[2:4], 16) / 255.0
    b = int(value[4:6], 16) / 255.0
    return [r, g, b]


def _expected_border_width(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value > 1:
        return value / 500
    return value


def _normalize_anim_time(value: Any, threshold: int) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)) and value < threshold:
        return int(value * 1_000_000)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _expected_sticker_category_id(anim_type: str, name: str) -> str:
    if anim_type == "in":
        return "ruchang"
    if anim_type == "out":
        return "chuchang"
    if "入" in (name or ""):
        return "ruchang"
    if "出" in (name or ""):
        return "chuchang"
    return ""


def _check_draft_meta_info(
    input_params: Dict[str, Any],
    draft_meta_info: Dict[str, Any],
    issues: List[str]
) -> None:
    canvas = input_params.get("canvas", {}) or {}
    draft_fold_path = canvas.get("source_draft_fold_path") or ""
    if draft_fold_path:
        expected_fold = _normalize_path(draft_fold_path)
        actual_fold = _normalize_path(draft_meta_info.get("draft_fold_path", ""))
        if actual_fold != expected_fold:
            issues.append(f"draft_meta_info.draft_fold_path 不一致: expected={expected_fold} actual={actual_fold}")

        expected_name = Path(expected_fold).name
        actual_name = draft_meta_info.get("draft_name", "")
        if expected_name and actual_name != expected_name:
            issues.append(f"draft_meta_info.draft_name 不一致: expected={expected_name} actual={actual_name}")

        expected_drive = Path(expected_fold).drive
        actual_drive = draft_meta_info.get("draft_removable_storage_device", "")
        if expected_drive and actual_drive != expected_drive:
            issues.append(
                f"draft_meta_info.draft_removable_storage_device 不一致: expected={expected_drive} actual={actual_drive}"
            )

        expected_root = _normalize_path(str(Path(expected_fold).parent))
        actual_root = _normalize_path(draft_meta_info.get("draft_root_path", ""))
        if expected_root and actual_root != expected_root:
            issues.append(f"draft_meta_info.draft_root_path 不一致: expected={expected_root} actual={actual_root}")

    draft_id = draft_meta_info.get("draft_id", "")
    if not draft_id or not isinstance(draft_id, str):
        issues.append("draft_meta_info.draft_id 为空或类型不正确")

    now_us = int(time.time() * 1000000)
    for key in ("tm_draft_create", "tm_draft_modified"):
        value = draft_meta_info.get(key)
        if not isinstance(value, int):
            issues.append(f"draft_meta_info.{key} 不是整数: actual={value}")
            continue
        # 允许时间偏差 120 秒
        if abs(now_us - value) > 120 * 1000000:
            issues.append(f"draft_meta_info.{key} 时间偏差过大: actual={value}")

    expected_tm_duration = _normalize_duration(canvas.get("duration"))
    if expected_tm_duration is not None:
        actual_tm_duration = draft_meta_info.get("tm_duration")
        if actual_tm_duration != expected_tm_duration:
            issues.append(
                f"draft_meta_info.tm_duration 不一致: expected={expected_tm_duration} actual={actual_tm_duration}"
            )


def _check_tracks(
    input_params: Dict[str, Any],
    draft_content: Dict[str, Any],
    issues: List[str]
) -> None:
    input_tracks = input_params.get("tracks", {}) or {}
    expected_video_ids = [t.get("id") for t in input_tracks.get("video_track", []) or []]
    expected_text_ids = [t.get("id") for t in input_tracks.get("texts_track", []) or []]
    expected_audio_ids = [t.get("id") for t in input_tracks.get("audios_track", []) or []]

    tracks = draft_content.get("tracks", []) or []
    actual_video_ids = [t.get("id") for t in tracks if t.get("type") == "video"]
    actual_text_ids = [t.get("id") for t in tracks if t.get("type") == "text"]
    actual_audio_ids = [t.get("id") for t in tracks if t.get("type") == "audio"]

    if len(actual_video_ids) != len(expected_video_ids):
        issues.append(
            f"tracks.video 数量不一致: expected={len(expected_video_ids)} actual={len(actual_video_ids)}"
        )
    if len(actual_text_ids) != len(expected_text_ids):
        issues.append(
            f"tracks.text 数量不一致: expected={len(expected_text_ids)} actual={len(actual_text_ids)}"
        )
    if len(actual_audio_ids) != len(expected_audio_ids):
        issues.append(
            f"tracks.audio 数量不一致: expected={len(expected_audio_ids)} actual={len(actual_audio_ids)}"
        )

    for track_id in expected_video_ids:
        if track_id and track_id not in actual_video_ids:
            issues.append(f"tracks.video 缺少轨道ID: {track_id}")
    for track_id in expected_text_ids:
        if track_id and track_id not in actual_text_ids:
            issues.append(f"tracks.text 缺少轨道ID: {track_id}")
    for track_id in expected_audio_ids:
        if track_id and track_id not in actual_audio_ids:
            issues.append(f"tracks.audio 缺少轨道ID: {track_id}")

def _approx_equal(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol

def _to_relative(value: float, size: float) -> float:
    if size <= 0:
        return value
    if abs(value) > 2:
        return value / size
    return value

def _to_scale_ratio(value: float) -> float:
    if value is None:
        return 1.0
    if value > 10:
        return value / 100.0
    return value

def _check_video_segments_and_materials(
    input_params: Dict[str, Any],
    draft_content: Dict[str, Any],
    issues: List[str]
) -> None:
    input_videos = input_params.get("videos", []) or []
    canvas = input_params.get("canvas", {}) or {}
    canvas_width = canvas.get("width", 1920)
    canvas_height = canvas.get("height", 1080)
    jianying_folder_path = canvas.get("jianying_folder_path", "") or ""
    materials = draft_content.get("materials", {}) or {}
    materials_videos = materials.get("videos", []) or []
    materials_anims = materials.get("material_animations", []) or []
    materials_speeds = materials.get("speeds", []) or []
    materials_sound = materials.get("sound_channel_mappings", []) or []
    materials_vocal = materials.get("vocal_separations", []) or []

    tracks = draft_content.get("tracks", []) or []
    video_tracks = [t for t in tracks if t.get("type") == "video"]
    segments = []
    for t in video_tracks:
        segments.extend(t.get("segments", []) or [])

    if len(materials_videos) != len(input_videos):
        issues.append(
            f"materials.videos 数量不一致: expected={len(input_videos)} actual={len(materials_videos)}"
        )
    if len(segments) != len(input_videos):
        issues.append(
            f"tracks.video.segments 数量不一致: expected={len(input_videos)} actual={len(segments)}"
        )

    material_video_ids = {m.get("id") for m in materials_videos}
    segment_ids = {s.get("id") for s in segments}
    track_ids = {t.get("id") for t in video_tracks}
    anim_group_ids = {a.get("id") for a in materials_anims}

    for v in input_videos:
        vid = v.get("id")
        track_info = v.get("tracks", {}) or {}
        track_id = track_info.get("id")
        segment_id = track_info.get("segments_id")
        anim_group_id = (track_info.get("material_animations", {}) or {}).get("id")

        if vid and vid not in material_video_ids:
            issues.append(f"materials.videos 缺少素材ID: {vid}")
        if track_id and track_id not in track_ids:
            issues.append(f"tracks.video 缺少轨道ID: {track_id}")
        if segment_id and segment_id not in segment_ids:
            issues.append(f"tracks.video.segments 缺少片段ID: {segment_id}")
        if anim_group_id and anim_group_id not in anim_group_ids:
            issues.append(f"materials.material_animations 缺少动画组ID: {anim_group_id}")

        # 素材字段一致性
        if vid:
            mat = next((m for m in materials_videos if m.get("id") == vid), None)
            if mat:
                if mat.get("path") != v.get("path"):
                    issues.append(f"materials.videos.path 不一致: id={vid}")
                if mat.get("width") != v.get("width"):
                    issues.append(f"materials.videos.width 不一致: id={vid}")
                if mat.get("height") != v.get("height"):
                    issues.append(f"materials.videos.height 不一致: id={vid}")

        # 片段字段一致性
        if segment_id:
            seg = next((s for s in segments if s.get("id") == segment_id), None)
            if seg:
                if seg.get("track_render_index") != track_info.get("track_render_index"):
                    issues.append(f"segment.track_render_index 不一致: id={segment_id}")

                clip = seg.get("clip", {}) or {}
                scale = clip.get("scale", {}) or {}
                transform = clip.get("transform", {}) or {}
                expected_scale_x = _to_scale_ratio(track_info.get("scale_x", 1.0))
                expected_scale_y = _to_scale_ratio(track_info.get("scale_y", 1.0))
                expected_tx = _to_relative(track_info.get("transform_x", 0.0), canvas_width)
                expected_ty = _to_relative(track_info.get("transform_y", 0.0), canvas_height)
                if not _approx_equal(scale.get("x", 0.0), expected_scale_x):
                    issues.append(f"segment.clip.scale.x 不一致: id={segment_id}")
                if not _approx_equal(scale.get("y", 0.0), expected_scale_y):
                    issues.append(f"segment.clip.scale.y 不一致: id={segment_id}")
                if not _approx_equal(transform.get("x", 0.0), expected_tx):
                    issues.append(f"segment.clip.transform.x 不一致: id={segment_id}")
                if not _approx_equal(transform.get("y", 0.0), expected_ty):
                    issues.append(f"segment.clip.transform.y 不一致: id={segment_id}")

                target_timerange = seg.get("target_timerange", {}) or {}
                expected_start = int(round((track_info.get("start", 0) or 0) * 1000000))
                expected_duration = int(round((track_info.get("duration", 0) or 0) * 1000000))
                if target_timerange.get("start") != expected_start:
                    issues.append(f"segment.target_timerange.start 不一致: id={segment_id}")
                if target_timerange.get("duration") != expected_duration:
                    issues.append(f"segment.target_timerange.duration 不一致: id={segment_id}")

                # 引用关系检查
                refs = seg.get("extra_material_refs", []) or []
                if refs:
                    expected_anim_id = anim_group_id or ""
                    speeds_ids = {m.get("id") for m in materials_speeds}
                    sound_ids = {m.get("id") for m in materials_sound}
                    vocal_ids = {m.get("id") for m in materials_vocal}

                    # 只校验顺序结构：0=speed,2=anim,3=sound,4=vocal；不校验 canvases_id 对齐
                    if len(refs) >= 5:
                        if refs[0] not in speeds_ids:
                            issues.append(f"segment.extra_material_refs[0] 非 speeds_id: id={segment_id}")
                        if expected_anim_id and refs[2] != expected_anim_id:
                            issues.append(f"segment.extra_material_refs[2] 动画组ID不一致: id={segment_id}")
                        if refs[3] not in sound_ids:
                            issues.append(f"segment.extra_material_refs[3] 非 sound_channel_mappings_id: id={segment_id}")
                        if refs[4] not in vocal_ids:
                            issues.append(f"segment.extra_material_refs[4] 非 vocal_separations_id: id={segment_id}")
                    else:
                        issues.append(f"segment.extra_material_refs 长度不足: id={segment_id}")

                    if expected_anim_id and expected_anim_id not in anim_group_ids:
                        issues.append(f"segment.extra_material_refs 动画组ID不存在: id={segment_id}")

                # 关键帧一致性
                expected_kf = track_info.get("common_keyframes", {}) or {}
                if isinstance(expected_kf, list):
                    expected_kf_map = {g.get("property_type"): g.get("keyframe_list", []) for g in expected_kf}
                else:
                    expected_kf_map = expected_kf
                actual_kf_groups = seg.get("common_keyframes", []) or []
                actual_kf_map = {g.get("property_type"): g.get("keyframe_list", []) for g in actual_kf_groups}
                for prop, kfs in expected_kf_map.items():
                    actual_list = actual_kf_map.get(prop, [])
                    if len(actual_list) != len(kfs):
                        issues.append(f"segment.common_keyframes 数量不一致: id={segment_id} prop={prop}")
                        continue
                    for idx, kf in enumerate(kfs):
                        expected_time = int(round((kf.get("time_offset", 0) or 0) * 1000000))
                        actual_time = actual_list[idx].get("time_offset")
                        if actual_time != expected_time:
                            issues.append(f"segment.common_keyframes.time_offset 不一致: id={segment_id} prop={prop}")
                        expected_values = kf.get("values", [])
                        actual_values = actual_list[idx].get("values", [])
                        if len(expected_values) != len(actual_values):
                            issues.append(f"segment.common_keyframes.values 长度不一致: id={segment_id} prop={prop}")
                        else:
                            for vi, ev in enumerate(expected_values):
                                av = actual_values[vi]
                                expected_value = ev
                                if prop == "KFTypePositionX":
                                    expected_value = _to_relative(ev, canvas_width)
                                elif prop == "KFTypePositionY":
                                    expected_value = _to_relative(ev, canvas_height)
                                elif prop == "KFTypeScaleX":
                                    expected_value = _to_scale_ratio(ev)
                                elif prop == "KFTypeScaleY":
                                    expected_value = _to_scale_ratio(ev)
                                if not _approx_equal(float(expected_value), float(av), tol=1e-3):
                                    issues.append(f"segment.common_keyframes.values 不一致: id={segment_id} prop={prop}")


def _find_text_segments(draft_content: Dict[str, Any]) -> List[Dict[str, Any]]:
    tracks = draft_content.get("tracks", []) or []
    text_tracks = [t for t in tracks if t.get("type") == "text"]
    segments: List[Dict[str, Any]] = []
    for t in text_tracks:
        segments.extend(t.get("segments", []) or [])
    return segments


def _build_animation_mapping_table():
    table = DraftConfigUtility.load_animation_map()
    return {(m["material_type"], m["category_id"], m["name"]): m for m in table}


def _check_text_segments_and_materials(
    input_params: Dict[str, Any],
    draft_content: Dict[str, Any],
    issues: List[str]
) -> None:
    input_texts = input_params.get("texts", []) or []
    if not input_texts:
        return

    canvas = input_params.get("canvas", {}) or {}
    canvas_width = canvas.get("width", 1920)
    canvas_height = canvas.get("height", 1080)
    jianying_folder_path = canvas.get("jianying_folder_path", "") or ""

    materials = draft_content.get("materials", {}) or {}
    materials_texts = materials.get("texts", []) or []
    materials_anims = materials.get("material_animations", []) or []
    segments = _find_text_segments(draft_content)

    if len(materials_texts) != len(input_texts):
        issues.append(
            f"materials.texts 数量不一致: expected={len(input_texts)} actual={len(materials_texts)}"
        )
    if len(segments) != len(input_texts):
        issues.append(
            f"tracks.text.segments 数量不一致: expected={len(input_texts)} actual={len(segments)}"
        )

    material_text_map = {m.get("id"): m for m in materials_texts if m.get("id")}
    segment_by_material = {s.get("material_id"): s for s in segments if s.get("material_id")}
    anim_group_map = {a.get("id"): a for a in materials_anims if a.get("id")}

    mapping_table = _build_animation_mapping_table()
    font_title_map = {
        "6740435892441190919": "新青年体",
    }

    for text in input_texts:
        text_id = text.get("id")
        track_info = text.get("tracks", {}) or {}
        material = material_text_map.get(text_id)
        segment = segment_by_material.get(text_id)

        if not material:
            issues.append(f"materials.texts 缺少素材ID: {text_id}")
            continue
        if not segment:
            issues.append(f"tracks.text.segments 缺少 material_id: {text_id}")
            continue

        # 文本素材字段
        if material.get("id") != text_id:
            issues.append(f"materials.texts.id 不一致: id={text_id}")

        expected_font_path = text.get("font_path", "") or ""
        expected_font_res_id = text.get("font_resource_id", "") or ""
        input_font_title = text.get("fonts_title") or text.get("font_title") or ""
        if input_font_title:
            mapped_font = DraftConfigUtility.resolve_font_by_title(
                input_font_title,
                jianying_folder_path=jianying_folder_path
            )
            if mapped_font:
                expected_font_path = mapped_font.get("font_path", "") or expected_font_path
                expected_font_res_id = mapped_font.get("font_resource_id", "") or expected_font_res_id
        expected_font_size = text.get("font_size")
        expected_font_size = expected_font_size if expected_font_size is not None else material.get("font_size")

        if material.get("font_name") != "":
            issues.append(f"materials.texts.font_name 非空: id={text_id}")
        if material.get("font_path") != expected_font_path:
            issues.append(f"materials.texts.font_path 不一致: id={text_id}")
        if material.get("font_resource_id") != expected_font_res_id:
            issues.append(f"materials.texts.font_resource_id 不一致: id={text_id}")
        if expected_font_size is not None and material.get("font_size") != expected_font_size:
            issues.append(f"materials.texts.font_size 不一致: id={text_id}")

        expected_text_color = _normalize_hex_color(text.get("text_color"), material.get("text_color", "#ffffff"))
        expected_border_color = _normalize_hex_color(text.get("border_color"), material.get("border_color", "#000000"))
        if material.get("text_color", "").lower() != expected_text_color:
            issues.append(f"materials.texts.text_color 不一致: id={text_id}")
        if material.get("border_color", "").lower() != expected_border_color:
            issues.append(f"materials.texts.border_color 不一致: id={text_id}")

        expected_border_width = _expected_border_width(text.get("border_width"))
        if expected_border_width is not None and not _approx_equal(
            material.get("border_width", 0.0), expected_border_width, tol=1e-6
        ):
            issues.append(f"materials.texts.border_width 不一致: id={text_id}")

        if track_info.get("text_alpha") is not None:
            if not _approx_equal(material.get("text_alpha", 0.0), track_info.get("text_alpha"), tol=1e-6):
                issues.append(f"materials.texts.text_alpha 不一致: id={text_id}")

        # fonts 映射
        fonts_list = material.get("fonts", []) or []
        if not fonts_list:
            issues.append(f"materials.texts.fonts 为空: id={text_id}")
        else:
            font_title_input = input_font_title
            expected_title = font_title_input or font_title_map.get(expected_font_res_id, "")
            font0 = fonts_list[0]
            if font0.get("title") != expected_title:
                issues.append(f"materials.texts.fonts[0].title 不一致: id={text_id}")
            if expected_font_res_id:
                if font0.get("resource_id") != expected_font_res_id:
                    issues.append(f"materials.texts.fonts[0].resource_id 不一致: id={text_id}")
                if font0.get("effect_id") != expected_font_res_id:
                    issues.append(f"materials.texts.fonts[0].effect_id 不一致: id={text_id}")
            if expected_font_path and font0.get("path") != expected_font_path:
                issues.append(f"materials.texts.fonts[0].path 不一致: id={text_id}")

        # content 结构校验
        content_raw = material.get("content", "")
        try:
            content_obj = json.loads(content_raw) if isinstance(content_raw, str) else content_raw
        except json.JSONDecodeError:
            issues.append(f"materials.texts.content 不是合法JSON: id={text_id}")
            content_obj = {}
        input_text_content = text.get("content", "") or ""
        if content_obj.get("text", "") != input_text_content:
            issues.append(f"materials.texts.content.text 不一致: id={text_id}")
        styles = content_obj.get("styles", []) or []
        if not styles:
            issues.append(f"materials.texts.content.styles 为空: id={text_id}")
        else:
            style0 = styles[0]
            font_info = style0.get("font", {}) or {}
            if font_info.get("path") != expected_font_path:
                issues.append(f"materials.texts.content.font.path 不一致: id={text_id}")
            if font_info.get("id") != expected_font_res_id:
                issues.append(f"materials.texts.content.font.id 不一致: id={text_id}")
            if expected_font_size is not None and style0.get("size") != expected_font_size:
                issues.append(f"materials.texts.content.size 不一致: id={text_id}")

            fill_color = style0.get("fill", {}).get("content", {}).get("solid", {}).get("color", [])
            expected_fill = _hex_to_rgb01(expected_text_color)
            if len(fill_color) != 3 or any(not _approx_equal(float(fill_color[i]), expected_fill[i], tol=1e-6) for i in range(3)):
                issues.append(f"materials.texts.content.fill.color 不一致: id={text_id}")

            strokes = style0.get("strokes", []) or []
            if not strokes:
                issues.append(f"materials.texts.content.strokes 为空: id={text_id}")
            else:
                stroke0 = strokes[0]
                stroke_color = stroke0.get("content", {}).get("solid", {}).get("color", [])
                expected_stroke = _hex_to_rgb01(expected_border_color)
                if len(stroke_color) != 3 or any(not _approx_equal(float(stroke_color[i]), expected_stroke[i], tol=1e-6) for i in range(3)):
                    issues.append(f"materials.texts.content.strokes.color 不一致: id={text_id}")
                if expected_border_width is not None:
                    if not _approx_equal(float(stroke0.get("width", 0.0)), expected_border_width, tol=1e-6):
                        issues.append(f"materials.texts.content.strokes.width 不一致: id={text_id}")

            expected_range = [0, len(input_text_content)]
            if style0.get("range") != expected_range:
                issues.append(f"materials.texts.content.range 不一致: id={text_id}")

        # 片段字段
        if segment.get("material_id") != text_id:
            issues.append(f"segment.material_id 不一致: id={text_id}")
        if segment.get("track_render_index") != track_info.get("track_render_index"):
            issues.append(f"segment.track_render_index 不一致: id={text_id}")

        clip = segment.get("clip", {}) or {}
        scale = clip.get("scale", {}) or {}
        transform = clip.get("transform", {}) or {}
        expected_scale_x = _to_scale_ratio(track_info.get("scale_x", 1.0))
        expected_scale_y = _to_scale_ratio(track_info.get("scale_y", 1.0))
        expected_tx = _to_relative(track_info.get("transform_x", 0.0), canvas_width)
        expected_ty = _to_relative(track_info.get("transform_y", 0.0), canvas_height)
        if not _approx_equal(scale.get("x", 0.0), expected_scale_x):
            issues.append(f"segment.clip.scale.x 不一致: id={text_id}")
        if not _approx_equal(scale.get("y", 0.0), expected_scale_y):
            issues.append(f"segment.clip.scale.y 不一致: id={text_id}")
        if not _approx_equal(transform.get("x", 0.0), expected_tx):
            issues.append(f"segment.clip.transform.x 不一致: id={text_id}")
        if not _approx_equal(transform.get("y", 0.0), expected_ty):
            issues.append(f"segment.clip.transform.y 不一致: id={text_id}")

        target_timerange = segment.get("target_timerange", {}) or {}
        expected_start = int(round((track_info.get("start", 0) or 0) * 1000000))
        expected_duration = int(round((track_info.get("duration", 0) or 0) * 1000000))
        if target_timerange.get("start") != expected_start:
            issues.append(f"segment.target_timerange.start 不一致: id={text_id}")
        if target_timerange.get("duration") != expected_duration:
            issues.append(f"segment.target_timerange.duration 不一致: id={text_id}")

        # 动画引用与动画字段校验
        anim_group = track_info.get("material_animations", {}) or {}
        anim_group_id = anim_group.get("id", "")
        refs = segment.get("extra_material_refs", []) or []
        if anim_group_id:
            if refs != [anim_group_id]:
                issues.append(f"segment.extra_material_refs 不一致: id={text_id}")
            if anim_group_id not in anim_group_map:
                issues.append(f"materials.material_animations 缺少动画组ID: {anim_group_id}")
        else:
            if refs:
                issues.append(f"segment.extra_material_refs 应为空: id={text_id}")

        if anim_group_id and anim_group_id in anim_group_map:
            output_group = anim_group_map[anim_group_id]
            output_anims = output_group.get("animations", []) or []
            input_anims = anim_group.get("animations", []) or []
            if len(output_anims) != len(input_anims):
                issues.append(f"materials.material_animations.animations 数量不一致: id={text_id}")
            for input_anim in input_anims:
                name = input_anim.get("name", "")
                anim_type = input_anim.get("type", "")
                expected_category_id = input_anim.get("category_id") or _expected_sticker_category_id(anim_type, name)
                expected_category_name = "入场" if expected_category_id in ("ruchang", "in") else "出场"
                expected_start = _normalize_anim_time(input_anim.get("start", 0), 1000)
                expected_duration = _normalize_anim_time(input_anim.get("duration", 0), 10000)

                mapping_key = ("sticker", expected_category_id, name)
                mapping = mapping_table.get(mapping_key)
                expected_resource_id = mapping["resource_id"] if mapping else input_anim.get("resource_id", "")
                expected_anim_id = mapping["id"] if mapping else input_anim.get("id", "")
                expected_path = (
                    f"C:/Users/pc/AppData/Local/JianyingPro/User Data/Cache/effect/"
                    f"{expected_anim_id}/{mapping['path_hash']}"
                ) if mapping else input_anim.get("path", "")

                output_anim = next(
                    (a for a in output_anims if a.get("name") == name and a.get("type") == anim_type),
                    None
                )
                if not output_anim:
                    issues.append(f"materials.material_animations.animations 缺少动画: id={text_id} name={name}")
                    continue

                if output_anim.get("category_id") != expected_category_id:
                    issues.append(f"materials.material_animations.category_id 不一致: id={text_id} name={name}")
                if output_anim.get("category_name") != expected_category_name:
                    issues.append(f"materials.material_animations.category_name 不一致: id={text_id} name={name}")
                if output_anim.get("start") != expected_start:
                    issues.append(f"materials.material_animations.start 不一致: id={text_id} name={name}")
                if output_anim.get("duration") != expected_duration:
                    issues.append(f"materials.material_animations.duration 不一致: id={text_id} name={name}")
                if output_anim.get("resource_id") != expected_resource_id:
                    issues.append(f"materials.material_animations.resource_id 不一致: id={text_id} name={name}")
                if output_anim.get("id") != expected_anim_id:
                    issues.append(f"materials.material_animations.id 不一致: id={text_id} name={name}")
                if output_anim.get("path") != expected_path:
                    issues.append(f"materials.material_animations.path 不一致: id={text_id} name={name}")

        # 关键帧一致性
        expected_kf = track_info.get("common_keyframes", {}) or {}
        if isinstance(expected_kf, list):
            expected_kf_map = {g.get("property_type"): g.get("keyframe_list", []) for g in expected_kf}
        else:
            expected_kf_map = expected_kf
        actual_kf_groups = segment.get("common_keyframes", []) or []
        actual_kf_map = {g.get("property_type"): g.get("keyframe_list", []) for g in actual_kf_groups}
        for prop, kfs in expected_kf_map.items():
            actual_list = actual_kf_map.get(prop, [])
            if len(actual_list) != len(kfs):
                issues.append(f"segment.common_keyframes 数量不一致: id={text_id} prop={prop}")
                continue
            for idx, kf in enumerate(kfs):
                expected_time = int(round((kf.get("time_offset", 0) or 0) * 1000000))
                actual_time = actual_list[idx].get("time_offset")
                if actual_time != expected_time:
                    issues.append(f"segment.common_keyframes.time_offset 不一致: id={text_id} prop={prop}")
                expected_values = kf.get("values", [])
                actual_values = actual_list[idx].get("values", [])
                if len(expected_values) != len(actual_values):
                    issues.append(f"segment.common_keyframes.values 长度不一致: id={text_id} prop={prop}")
                else:
                    for vi, ev in enumerate(expected_values):
                        av = actual_values[vi]
                        expected_value = ev
                        if prop == "KFTypePositionX":
                            expected_value = _to_relative(ev, canvas_width)
                        elif prop == "KFTypePositionY":
                            expected_value = _to_relative(ev, canvas_height)
                        elif prop == "KFTypeScaleX":
                            expected_value = _to_scale_ratio(ev)
                        elif prop == "KFTypeScaleY":
                            expected_value = _to_scale_ratio(ev)
                        if not _approx_equal(float(expected_value), float(av), tol=1e-3):
                            issues.append(f"segment.common_keyframes.values 不一致: id={text_id} prop={prop}")


def _get_input_audios(input_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    audios = input_params.get("audios", []) or []
    if audios:
        return audios
    legacy = []
    for key in ("bgms", "voices", "sounds"):
        legacy.extend(input_params.get(key, []) or [])
    return legacy


def _check_audio_segments_and_materials(
    input_params: Dict[str, Any],
    draft_content: Dict[str, Any],
    issues: List[str]
) -> None:
    input_audios = _get_input_audios(input_params)
    if not input_audios:
        return

    materials = draft_content.get("materials", {}) or {}
    materials_audios = materials.get("audios", []) or []
    materials_speeds = materials.get("speeds", []) or []
    materials_sound = materials.get("sound_channel_mappings", []) or []
    materials_vocal = materials.get("vocal_separations", []) or []
    materials_beats = materials.get("beats", []) or []

    tracks = draft_content.get("tracks", []) or []
    audio_tracks = [t for t in tracks if t.get("type") == "audio"]
    segments = []
    for t in audio_tracks:
        segments.extend(t.get("segments", []) or [])

    if len(materials_audios) != len(input_audios):
        issues.append(
            f"materials.audios 数量不一致: expected={len(input_audios)} actual={len(materials_audios)}"
        )
    if len(segments) != len(input_audios):
        issues.append(
            f"tracks.audio.segments 数量不一致: expected={len(input_audios)} actual={len(segments)}"
        )

    material_audio_map = {m.get("id"): m for m in materials_audios if m.get("id")}
    segment_by_material = {s.get("material_id"): s for s in segments if s.get("material_id")}
    track_ids = {t.get("id") for t in audio_tracks}

    speeds_ids = {m.get("id") for m in materials_speeds}
    sound_ids = {m.get("id") for m in materials_sound}
    vocal_ids = {m.get("id") for m in materials_vocal}
    beats_ids = {m.get("id") for m in materials_beats}

    input_tracks = input_params.get("tracks", {}) or {}
    audios_track_list = input_tracks.get("audios_track", []) or []
    audios_track_sorted = sorted(
        audios_track_list,
        key=lambda x: x.get("track_render_index", 0)
    )

    for audio in input_audios:
        audio_id = audio.get("id")
        track_info = audio.get("tracks", {}) or {}
        material = material_audio_map.get(audio_id)
        segment = segment_by_material.get(audio_id)

        if audio_id and audio_id not in material_audio_map:
            issues.append(f"materials.audios 缺少素材ID: {audio_id}")
        if audio_id and audio_id not in segment_by_material:
            issues.append(f"tracks.audio.segments 缺少 material_id: {audio_id}")

        track_id = track_info.get("id")
        segment_id = track_info.get("segments_id")
        if track_id and track_id not in track_ids:
            issues.append(f"tracks.audio 缺少轨道ID: {track_id}")
        if segment_id and segment_id not in {s.get("id") for s in segments}:
            issues.append(f"tracks.audio.segments 缺少片段ID: {segment_id}")

        # materials.audios 字段一致性
        if material:
            if material.get("id") != audio_id:
                issues.append(f"materials.audios.id 不一致: id={audio_id}")
            if material.get("name") != audio.get("name", ""):
                issues.append(f"materials.audios.name 不一致: id={audio_id}")
            if material.get("path") != audio.get("path", ""):
                issues.append(f"materials.audios.path 不一致: id={audio_id}")
            expected_duration = _normalize_duration(audio.get("duration"))
            if expected_duration is not None and material.get("duration") != expected_duration:
                issues.append(f"materials.audios.duration 不一致: id={audio_id}")

        # segments 字段一致性
        if segment:
            if segment_id and segment.get("id") != segment_id:
                issues.append(f"segment.id 不一致: id={audio_id}")
            if segment.get("material_id") != audio_id:
                issues.append(f"segment.material_id 不一致: id={audio_id}")
            expected_track_idx = track_info.get("track_render_index", 0)
            if expected_track_idx < len(audios_track_sorted):
                expected_track_idx = audios_track_sorted[expected_track_idx].get(
                    "track_render_index", expected_track_idx
                )
            if segment.get("track_render_index") != expected_track_idx:
                issues.append(f"segment.track_render_index 不一致: id={audio_id}")
            if segment.get("volume") != track_info.get("volume", 1.0):
                issues.append(f"segment.volume 不一致: id={audio_id}")

            expected_start = int(round((track_info.get("start", 0) or 0) * 1000000))
            expected_duration = int(round((track_info.get("segment_duration", audio.get("duration", 0)) or 0) * 1000000))
            source_start = int(round((track_info.get("source_start", 0) or 0) * 1000000))
            target_timerange = segment.get("target_timerange", {}) or {}
            source_timerange = segment.get("source_timerange", {}) or {}
            if target_timerange.get("start") != expected_start:
                issues.append(f"segment.target_timerange.start 不一致: id={audio_id}")
            if target_timerange.get("duration") != expected_duration:
                issues.append(f"segment.target_timerange.duration 不一致: id={audio_id}")
            if source_timerange.get("start") != source_start:
                issues.append(f"segment.source_timerange.start 不一致: id={audio_id}")
            if source_timerange.get("duration") != expected_duration:
                issues.append(f"segment.source_timerange.duration 不一致: id={audio_id}")

            # 引用关系检查
            refs = segment.get("extra_material_refs", []) or []
            if refs:
                if len(refs) < 4:
                    issues.append(f"segment.extra_material_refs 长度不足: id={audio_id}")
                else:
                    if refs[0] not in speeds_ids:
                        issues.append(f"segment.extra_material_refs[0] 非 speeds_id: id={audio_id}")
                    if refs[1] not in beats_ids:
                        issues.append(f"segment.extra_material_refs[1] 非 beats_id: id={audio_id}")
                    if refs[2] not in sound_ids:
                        issues.append(f"segment.extra_material_refs[2] 非 sound_channel_mappings_id: id={audio_id}")
                    if refs[3] not in vocal_ids:
                        issues.append(f"segment.extra_material_refs[3] 非 vocal_separations_id: id={audio_id}")
            else:
                issues.append(f"segment.extra_material_refs 为空: id={audio_id}")
def check_draft_output(
    input_param_path: str,
    draft_folder: str,
    raise_on_error: bool = True
) -> Dict[str, Any]:
    """
    校验生成草稿文件的根键修改内容。

    当前检查：
    - draft_content.json: id / canvas_config.height / canvas_config.width / duration
    - draft_meta_info.json: 仅校验文件可读取
    """
    issues: List[str] = []

    draft_content_path = os.path.join(draft_folder, "draft_content.json")
    draft_meta_path = os.path.join(draft_folder, "draft_meta_info.json")

    if not os.path.exists(draft_content_path):
        issues.append("缺少 draft_content.json")
    if not os.path.exists(draft_meta_path):
        issues.append("缺少 draft_meta_info.json")

    draft_content: Dict[str, Any] = {}
    if os.path.exists(draft_content_path):
        draft_content = _load_json(draft_content_path)

    if os.path.exists(draft_meta_path):
        draft_meta_info = _load_json(draft_meta_path)
    else:
        draft_meta_info = {}

    input_params = _load_json(input_param_path)
    _check_canvas_fields(input_params, draft_content, issues)
    _check_draft_meta_info(input_params, draft_meta_info, issues)
    _check_tracks(input_params, draft_content, issues)
    _check_video_segments_and_materials(input_params, draft_content, issues)
    _check_text_segments_and_materials(input_params, draft_content, issues)
    _check_audio_segments_and_materials(input_params, draft_content, issues)

    result = {
        "ok": len(issues) == 0,
        "issues": issues
    }
    if raise_on_error and issues:
        raise AssertionError("; ".join(issues))
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="剪辑合成模块检查器")
    parser.add_argument("input_param_path", help="输入参数文件路径")
    parser.add_argument("draft_folder", help="生成草稿文件夹路径")
    args = parser.parse_args()

    check_draft_output(args.input_param_path, args.draft_folder, raise_on_error=True)
    print("✅ 检查通过")
