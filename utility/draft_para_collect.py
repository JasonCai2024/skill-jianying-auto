import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .models.draft_collect_models import BaseModel
from .draft_config_utility import DraftConfigUtility


class DraftParaCollect:
    """
    剪辑编排模块：用于构建 draft_para_collect.json
    以“持续填充 JSON 数据”为核心，输出结构与解析结果一致。
    """

    def __init__(self, save_path: Optional[str] = None):
        base_path = Path(__file__).parent.parent
        self.save_path = Path(save_path) if save_path else (base_path / "tests")
        self.save_path.mkdir(parents=True, exist_ok=True)
        self.audio_name_map_path = base_path / "user_data" / "effect" / "audio_name_map.json"

    def get_random_id(self) -> str:
        return BaseModel.get_random_id()

    def _ensure_meta(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        meta = draft_para_collect.get("_meta")
        if not meta:
            meta = {"next_track_render_index": 0, "track_map": {}}
            draft_para_collect["_meta"] = meta
        return meta

    def set_canvas(
        self,
        width: int,
        height: int,
        jianying_folder_path: str = "",
        source_draft_fold_path: str = "",
        output_parent_draft_folder_path: str = ""
    ) -> Dict[str, Any]:
        canvas_id = self.get_random_id()
        draft_para_collect = {
            "canvas": {
                "id": canvas_id,
                "height": height,
                "width": width,
                "duration": 0.0,
                "source_draft_fold_path": source_draft_fold_path,
                "jianying_folder_path": jianying_folder_path,
                "output_parent_draft_folder_path": output_parent_draft_folder_path
            },
            "videos": [],
            "texts": [],
            "audios": [],
            "tracks": {
                "video_track": [],
                "texts_track": [],
                "audios_track": []
            },
            "_meta": {
                "next_track_render_index": 0,
                "track_map": {}
            }
        }
        return draft_para_collect

    def add_track(self, draft_para_collect: Dict[str, Any], track_type: str) -> Tuple[Dict[str, Any], str, int]:
        if track_type not in ("video", "text", "audio"):
            raise ValueError("track_type 必须为 video/text/audio")
        meta = self._ensure_meta(draft_para_collect)
        track_id = self.get_random_id()
        track_render_index = meta["next_track_render_index"]
        meta["next_track_render_index"] += 1
        meta["track_map"][track_id] = track_render_index

        track_item = {
            "track_render_index": track_render_index
        }
        if track_type == "video":
            draft_para_collect["tracks"]["video_track"].append(track_item)
        elif track_type == "text":
            draft_para_collect["tracks"]["texts_track"].append(track_item)
        else:
            draft_para_collect["tracks"]["audios_track"].append(track_item)

        return draft_para_collect, track_id, track_render_index

    def add_video(
        self,
        draft_para_collect: Dict[str, Any],
        track_id: str,
        path: str,
        width: int,
        height: int,
        start: float,
        duration: float,
        transform_x: float,
        transform_y: float,
        scale_x: float,
        scale_y: float
    ) -> Tuple[Dict[str, Any], str]:
        meta = self._ensure_meta(draft_para_collect)
        if track_id not in meta["track_map"]:
            raise ValueError("track_id 不存在，请先 add_track()")

        segment_id = self.get_random_id()
        video_id = self.get_random_id()
        track_render_index = meta["track_map"][track_id]

        video_item = {
            "id": video_id,
            "material_name": os.path.basename(path),
            "path": path,
            "width": width,
            "height": height,
            "tracks": {
                "id": track_id,
                "render_index": 0,
                "track_render_index": track_render_index,
                "segments_id": segment_id,
                "scale_x": scale_x,
                "scale_y": scale_y,
                "transform_x": transform_x,
                "transform_y": transform_y,
                "start": start,
                "duration": duration,
                "common_keyframes": [],
                "material_animations": {}
            }
        }
        draft_para_collect["videos"].append(video_item)
        return draft_para_collect, segment_id

    def add_video_keyframe(
        self,
        draft_para_collect: Dict[str, Any],
        segment_id: str,
        property_type: str,
        time_offset: float,
        values: Any
    ) -> Dict[str, Any]:
        target = self._find_segment_holder(draft_para_collect["videos"], segment_id)
        if not target:
            raise ValueError("segment_id 未找到")
        common_keyframes = target["tracks"].setdefault("common_keyframes", [])
        if not isinstance(common_keyframes, list):
            common_keyframes = []
            target["tracks"]["common_keyframes"] = common_keyframes

        group = next((g for g in common_keyframes if g.get("property_type") == property_type), None)
        if not group:
            group = {"property_type": property_type, "id": self.get_random_id(), "keyframe_list": []}
            common_keyframes.append(group)
        keyframe = {
            "id": self.get_random_id(),
            "time_offset": time_offset,
            "values": values if isinstance(values, list) else [values]
        }
        group["keyframe_list"].append(keyframe)
        return draft_para_collect

    def add_video_animation(
        self,
        draft_para_collect: Dict[str, Any],
        segment_id: str,
        anim_type: str,
        name: str,
        start: float,
        duration: float
    ) -> Dict[str, Any]:
        target = self._find_segment_holder(draft_para_collect["videos"], segment_id)
        if not target:
            raise ValueError("segment_id 未找到")
        animations = target["tracks"].setdefault("material_animations", {})
        if "id" not in animations or not animations["id"]:
            animations["id"] = self.get_random_id()
        animations.setdefault("animations", [])
        animations["animations"].append({
            "type": anim_type,
            "name": name,
            "start": start,
            "duration": duration
        })
        return draft_para_collect

    def add_text(
        self,
        draft_para_collect: Dict[str, Any],
        track_id: str,
        content: str,
        font_path: str,
        font_resource_id: str,
        fonts_title: str,
        text_color: str,
        border_color: str,
        border_width: float,
        font_size: float,
        start: float,
        duration: float,
        transform_x: float,
        transform_y: float,
        scale_x: float,
        scale_y: float,
        text_alpha: float = 1.0,
        background_style: int = 0,
        background_color: str = "#000000",
        background_width: float = 0.14,
        background_height: float = 0.14,
        background_round_radius: float = 0.0,
        global_alpha: float = 1.0,
        check_flag: int = 15
    ) -> Tuple[Dict[str, Any], str]:
        meta = self._ensure_meta(draft_para_collect)
        if track_id not in meta["track_map"]:
            raise ValueError("track_id 不存在，请先 add_track()")

        segment_id = self.get_random_id()
        text_id = self.get_random_id()
        track_render_index = meta["track_map"][track_id]

        if fonts_title:
            canvas_info = draft_para_collect.get("canvas", {}) or {}
            jianying_folder_path = canvas_info.get("jianying_folder_path", "") or ""
            font_info = DraftConfigUtility.resolve_font_by_title(
                fonts_title,
                jianying_folder_path=jianying_folder_path
            )
            if font_info:
                font_path = font_info.get("font_path", "") or font_path
                font_resource_id = font_info.get("font_resource_id", "") or font_resource_id

        text_item = {
            "id": text_id,
            "content": content,
            "text_color": text_color,
            "border_color": border_color,
            "border_width": border_width,
            "font_size": font_size,
            "font_path": font_path,
            "font_resource_id": font_resource_id,
            "fonts_title": fonts_title,
            "background_style": int(background_style),
            "background_color": str(background_color or "#000000"),
            "background_width": float(background_width),
            "background_height": float(background_height),
            "background_round_radius": float(background_round_radius),
            "global_alpha": float(global_alpha),
            "check_flag": int(check_flag),
            "tracks": {
                "id": track_id,
                "track_render_index": track_render_index,
                "segments_id": segment_id,
                "transform_x": transform_x,
                "transform_y": transform_y,
                "scale_x": scale_x,
                "scale_y": scale_y,
                "start": start,
                "duration": duration,
                "text_alpha": text_alpha,
                "common_keyframes": [],
                "material_animations": {}
            }
        }
        draft_para_collect["texts"].append(text_item)
        return draft_para_collect, segment_id

    def add_text_keyframe(
        self,
        draft_para_collect: Dict[str, Any],
        segment_id: str,
        property_type: str,
        time_offset: float,
        values: Any
    ) -> Dict[str, Any]:
        target = self._find_segment_holder(draft_para_collect["texts"], segment_id)
        if not target:
            raise ValueError("segment_id 未找到")
        common_keyframes = target["tracks"].setdefault("common_keyframes", [])
        if not isinstance(common_keyframes, list):
            common_keyframes = []
            target["tracks"]["common_keyframes"] = common_keyframes

        group = next((g for g in common_keyframes if g.get("property_type") == property_type), None)
        if not group:
            group = {"property_type": property_type, "id": self.get_random_id(), "keyframe_list": []}
            common_keyframes.append(group)
        keyframe = {
            "id": self.get_random_id(),
            "time_offset": time_offset,
            "values": values if isinstance(values, list) else [values]
        }
        group["keyframe_list"].append(keyframe)
        return draft_para_collect

    def add_text_animation(
        self,
        draft_para_collect: Dict[str, Any],
        segment_id: str,
        anim_type: str,
        name: str,
        start: float,
        duration: float
    ) -> Dict[str, Any]:
        target = self._find_segment_holder(draft_para_collect["texts"], segment_id)
        if not target:
            raise ValueError("segment_id 未找到")
        animations = target["tracks"].setdefault("material_animations", {})
        if "id" not in animations or not animations["id"]:
            animations["id"] = self.get_random_id()
        animations.setdefault("animations", [])
        animations["animations"].append({
            "type": anim_type,
            "name": name,
            "start": start,
            "duration": duration
        })
        return draft_para_collect

    def add_audios(
        self,
        draft_para_collect: Dict[str, Any],
        track_id: str,
        start: float,
        duration: Optional[float] = None,
        material_duration: Optional[float] = None,
        path: Optional[str] = None,
        name: Optional[str] = None,
        volume: float = 1.0
    ) -> Tuple[Dict[str, Any], str]:
        meta = self._ensure_meta(draft_para_collect)
        if track_id not in meta["track_map"]:
            raise ValueError("track_id 不存在，请先 add_track()")

        path = path or ""
        name = name or ""
        audio_map = self._load_audio_name_map()

        if name and name.lower() in audio_map:
            mapped = audio_map.get(name.lower()) or {}
            if mapped.get("path"):
                path = mapped.get("path")
            if mapped.get("duration") is not None:
                duration = mapped.get("duration")

        if path:
            if not name:
                name = os.path.basename(path)
            if duration is None and name:
                mapped = audio_map.get(name.lower())
                if mapped:
                    duration = mapped.get("duration")
            if duration is None:
                raise ValueError("duration 不能为空")
        else:
            if not name:
                raise ValueError("path/name 至少其一非空")
            mapped = audio_map.get(name.lower())
            if not mapped:
                raise ValueError(f"未找到音频映射: {name}")
            path = mapped.get("path", "")
            duration = mapped.get("duration")
            if not path or duration is None:
                raise ValueError(f"音频映射不完整: {name}")

        path = path.replace("\\", "/")

        segment_id = self.get_random_id()
        audio_id = self.get_random_id()
        track_render_index = meta["track_map"][track_id]

        audio_item = {
            "id": audio_id,
            "name": name,
            "path": path,
            "duration": material_duration,
            "tracks": {
                "id": track_id,
                "segments_id": segment_id,
                "track_render_index": track_render_index,
                "start": start,
                "segment_duration": duration,
                "volume": volume
            }
        }
        draft_para_collect["audios"].append(audio_item)
        return draft_para_collect, segment_id

    def close_canvas(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        canvas = draft_para_collect.get("canvas", {}) or {}
        max_end = 0.0

        for video in draft_para_collect.get("videos", []):
            tracks = video.get("tracks", {}) or {}
            end_time = (tracks.get("start", 0.0) or 0.0) + (tracks.get("duration", 0.0) or 0.0)
            max_end = max(max_end, end_time)

        for text in draft_para_collect.get("texts", []):
            tracks = text.get("tracks", {}) or {}
            end_time = (tracks.get("start", 0.0) or 0.0) + (tracks.get("duration", 0.0) or 0.0)
            max_end = max(max_end, end_time)

        for audio in draft_para_collect.get("audios", []):
            tracks = audio.get("tracks", {}) or {}
            end_time = (tracks.get("start", 0.0) or 0.0) + (tracks.get("segment_duration", 0.0) or 0.0)
            max_end = max(max_end, end_time)

        canvas["duration"] = max_end
        draft_para_collect["canvas"] = canvas

        draft_para_collect.pop("_meta", None)
        output_file = self._get_output_path()
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(draft_para_collect, f, ensure_ascii=False, indent=2)
        return draft_para_collect

    def _get_output_path(self) -> str:
        timestamp = time.strftime("%m%d%H%M")
        filename = f"wkflow_orc_draft_para_collect_{timestamp}.json"
        return str(self.save_path / filename)

    def _load_audio_name_map(self) -> Dict[str, Any]:
        mapping = DraftConfigUtility.load_audio_name_map()
        return {k.lower(): v for k, v in (mapping or {}).items()}

    def _find_segment_holder(self, items: list, segment_id: str) -> Optional[Dict[str, Any]]:
        for item in items:
            tracks = item.get("tracks", {}) or {}
            if tracks.get("segments_id") == segment_id:
                return item
        return None
