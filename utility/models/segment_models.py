"""
剪辑合成模块片段模型
用于按片段类型生成标准 segment 结构
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List


def _deepcopy(data: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(data)


@dataclass
class VideoSegmentModel:
    """视频片段模型（默认字段来自参考结构）"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "id": "",
        "material_id": "",
        "render_index": 0,
        "track_render_index": 0,
        "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": 0.0}
        },
        "common_keyframes": [],
        "caption_info": None,
        "cartoon": False,
        "enable_adjust": True,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_lut": True,
        "enable_smart_color_adjust": False,
        "extra_material_refs": [],
        "group_id": "",
        "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
        "responsive_layout": {
            "enable": False,
            "horizontal_pos_layout": 0,
            "size_layout": 0,
            "target_follow": "",
            "vertical_pos_layout": 0
        },
        "uniform_scale": {"on": True, "value": 1.0},
        "intensifies_audio": False,
        "is_placeholder": False,
        "is_tone_modify": False,
        "keyframe_refs": [],
        "last_nonzero_volume": 1.0,
        "reverse": False,
        "speed": 1.0,
        "template_id": "",
        "template_scene": "default",
        "track_attribute": 0,
        "visible": True,
        "volume": 1.0,
        "source_timerange": {"duration": 0, "start": 0},
        "target_timerange": {"duration": 0, "start": 0}
    })

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class TextSegmentModel:
    """文字片段模型（结构与视频一致，引用逻辑不同）"""
    data: Dict[str, Any] = field(default_factory=lambda: VideoSegmentModel().to_dict())

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class AudioSegmentModel:
    """音频片段模型"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "caption_info": None,
        "cartoon": False,
        "clip": None,
        "common_keyframes": [],
        "enable_adjust": False,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_lut": False,
        "enable_smart_color_adjust": False,
        "extra_material_refs": [],
        "group_id": "",
        "hdr_settings": None,
        "id": "",
        "intensifies_audio": False,
        "is_placeholder": False,
        "is_tone_modify": False,
        "keyframe_refs": [],
        "last_nonzero_volume": 1.0,
        "material_id": "",
        "render_index": 0,
        "responsive_layout": {
            "enable": False,
            "horizontal_pos_layout": 0,
            "size_layout": 0,
            "target_follow": "",
            "vertical_pos_layout": 0
        },
        "uniform_scale": None,
        "reverse": False,
        "source_timerange": {"duration": 0, "start": 0},
        "speed": 1.0,
        "target_timerange": {"duration": 0, "start": 0},
        "template_id": "",
        "template_scene": "default",
        "track_attribute": 0,
        "track_render_index": 0,
        "visible": True,
        "volume": 1.0
    })

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)
