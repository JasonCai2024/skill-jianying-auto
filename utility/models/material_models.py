"""
剪辑合成模块素材模型
用于按素材类型生成标准 materials 结构
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict


def _deepcopy(data: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(data)


@dataclass
class VideoMaterialModel:
    """视频素材模型（默认字段来自当前固定模板值）"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "aigc_type": "none",
        "audio_fade": None,
        "cartoon_path": "",
        "category_id": "",
        "category_name": "local",
        "check_flag": 63487,
        "crop": {
            "lower_left_x": 0.0,
            "lower_left_y": 1.0,
            "lower_right_x": 1.0,
            "lower_right_y": 1.0,
            "upper_left_x": 0.0,
            "upper_left_y": 0.0,
            "upper_right_x": 1.0,
            "upper_right_y": 0.0
        },
        "crop_ratio": "free",
        "crop_scale": 1.0,
        "duration": 10800000000,
        "extra_type_option": 0,
        "formula_id": "",
        "freeze": None,
        "has_audio": False,
        "height": 0,
        "id": "",
        "intensifies_audio_path": "",
        "intensifies_path": "",
        "is_ai_generate_content": False,
        "is_copyright": False,
        "is_text_edit_overdub": False,
        "is_unified_beauty_mode": False,
        "local_id": "",
        "local_material_id": "",
        "material_id": "",
        "material_name": "",
        "material_url": "",
        "matting": {
            "flag": 0,
            "has_use_quick_brush": False,
            "has_use_quick_eraser": False,
            "interactiveTime": [],
            "path": "",
            "strokes": []
        },
        "media_path": "",
        "object_locked": None,
        "origin_material_id": "",
        "path": "",
        "picture_from": "none",
        "picture_set_category_id": "",
        "picture_set_category_name": "",
        "request_id": "",
        "reverse_intensifies_path": "",
        "reverse_path": "",
        "smart_motion": None,
        "source": 0,
        "source_platform": 0,
        "stable": {
            "matrix_path": "",
            "stable_level": 0,
            "time_range": {"duration": 0, "start": 0}
        },
        "team_id": "",
        "type": "photo",
        "video_algorithm": {
            "algorithms": [],
            "complement_frame_config": None,
            "deflicker": None,
            "gameplay_configs": [],
            "motion_blur_config": None,
            "noise_reduction": None,
            "path": "",
            "quality_enhance": None,
            "time_range": None
        },
        "width": 0
    })

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class TextMaterialModel:
    """文字素材模型（默认字段来自固定结构）"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "add_type": 0,
        "alignment": 1,
        "background_alpha": 1.0,
        "background_color": "#000000",
        "background_height": 0.14,
        "background_horizontal_offset": 0.0,
        "background_round_radius": 0.0,
        "background_style": 0,
        "background_vertical_offset": 0.0,
        "background_width": 0.14,
        "base_content": "",
        "bold_width": 0.0,
        "border_alpha": 1.0,
        "border_color": "#000000",
        "border_width": 0.08,
        "caption_template_info": {
            "category_id": "",
            "category_name": "",
            "effect_id": "",
            "is_new": False,
            "path": "",
            "request_id": "",
            "resource_id": "",
            "resource_name": "",
            "source_platform": 0
        },
        "check_flag": 15,
        "combo_info": {"text_templates": []},
        "content": "{\"text\":\"test1\",\"styles\":[{\"fill\":{\"content\":{\"solid\":{\"color\":[1,1,1]}}},\"font\":{\"path\":\"F:/剪映5.9版本免激活/JianyingPro/5.9.0.11632/Resources/Font/新青年体.ttf\",\"id\":\"6740435892441190919\"},\"strokes\":[{\"content\":{\"solid\":{\"color\":[0,0,0]}},\"width\":0.079999998211860657}],\"size\":12,\"useLetterColor\":true,\"range\":[0,5]}]}",
        "fixed_height": -1.0,
        "fixed_width": -1.0,
        "font_category_id": "",
        "font_category_name": "",
        "font_id": "",
        "font_name": "",
        "font_path": "F:/剪映5.9版本免激活/JianyingPro/5.9.0.11632/Resources/Font/新青年体.ttf",
        "font_resource_id": "6740435892441190919",
        "font_size": 12.0,
        "font_source_platform": 0,
        "font_team_id": "",
        "font_title": "none",
        "font_url": "",
        "fonts": [
            {
                "category_id": "",
                "category_name": "",
                "effect_id": "6740435892441190919",
                "file_uri": "",
                "id": "7A95A7E1-CE74-4aca-AF58-82F415A09922",
                "path": "F:/剪映5.9版本免激活/JianyingPro/5.9.0.11632/Resources/Font/新青年体.ttf",
                "request_id": "",
                "resource_id": "6740435892441190919",
                "source_platform": 0,
                "team_id": "",
                "title": "新青年体"
            }
        ],
        "force_apply_line_max_width": False,
        "global_alpha": 1.0,
        "group_id": "",
        "has_shadow": False,
        "id": "007B7E7A-6A18-4165-8EA5-E53120C42FDF",
        "initial_scale": 1.0,
        "inner_padding": -1.0,
        "is_rich_text": False,
        "italic_degree": 0,
        "ktv_color": "",
        "language": "",
        "layer_weight": 1,
        "letter_spacing": 0.0,
        "line_feed": 1,
        "line_max_width": 0.82,
        "line_spacing": 0.02,
        "multi_language_current": "none",
        "name": "",
        "original_size": [],
        "preset_category": "",
        "preset_category_id": "",
        "preset_has_set_alignment": False,
        "preset_id": "",
        "preset_index": 0,
        "preset_name": "",
        "recognize_task_id": "",
        "recognize_type": 0,
        "relevance_segment": [],
        "shadow_alpha": 0.9,
        "shadow_angle": -45.0,
        "shadow_color": "",
        "shadow_distance": 5.0,
        "shadow_point": {"x": 0.6363961030678928, "y": -0.6363961030678928},
        "shadow_smoothing": 0.45,
        "shape_clip_x": False,
        "shape_clip_y": False,
        "source_from": "",
        "style_name": "",
        "sub_type": 0,
        "subtitle_keywords": None,
        "subtitle_template_original_fontsize": 0.0,
        "text_alpha": 1.0,
        "text_color": "#ffffff",
        "text_curve": None,
        "text_preset_resource_id": "",
        "text_size": 30,
        "text_to_audio_ids": [],
        "tts_auto_update": False,
        "type": "text",
        "typesetting": 0,
        "underline": False,
        "underline_offset": 0.22,
        "underline_width": 0.05,
        "use_effect_default_color": True,
        "words": {"end_time": [], "start_time": [], "text": []}
    })

    @classmethod
    def from_template(cls, template: Dict[str, Any]) -> "TextMaterialModel":
        model = cls()
        model.apply(template or {})
        return model

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class AudioMaterialModel:
    """音频素材模型（基于模板作为默认结构）"""
    data: Dict[str, Any]

    @classmethod
    def from_template(cls, template: Dict[str, Any]) -> "AudioMaterialModel":
        return cls(_deepcopy(template))

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class SpeedMaterialModel:
    """速度素材模型（基于模板作为默认结构）"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "curve_speed": None,
        "id": "",
        "mode": 0,
        "speed": 1.0,
        "type": "speed"
    })

    @classmethod
    def from_template(cls, template: Dict[str, Any]) -> "SpeedMaterialModel":
        model = cls()
        model.apply(template or {})
        return model

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class SoundChannelMappingModel:
    """声道映射素材模型（基于模板作为默认结构）"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "audio_channel_mapping": 0,
        "id": "",
        "is_config_open": False,
        "type": "none"
    })

    @classmethod
    def from_template(cls, template: Dict[str, Any]) -> "SoundChannelMappingModel":
        model = cls()
        model.apply(template or {})
        return model

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class VocalSeparationModel:
    """人声分离素材模型（基于模板作为默认结构）"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "choice": 0,
        "id": "",
        "production_path": "",
        "time_range": None,
        "type": "vocal_separation"
    })

    @classmethod
    def from_template(cls, template: Dict[str, Any]) -> "VocalSeparationModel":
        model = cls()
        model.apply(template or {})
        return model

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class BeatMaterialModel:
    """节拍素材模型（基于模板作为默认结构）"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "ai_beats": {
            "beat_speed_infos": [],
            "beats_path": "",
            "beats_url": "",
            "melody_path": "",
            "melody_percents": [0.0],
            "melody_url": ""
        },
        "enable_ai_beats": False,
        "gear": 404,
        "gear_count": 0,
        "id": "",
        "mode": "404",
        "type": "beats",
        "user_beats": [],
        "user_delete_ai_beats": None
    })

    @classmethod
    def from_template(cls, template: Dict[str, Any]) -> "BeatMaterialModel":
        model = cls()
        model.apply(template or {})
        return model

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class CanvasMaterialModel:
    """画布素材模型（基于模板作为默认结构）"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "album_image": "",
        "blur": 0.0,
        "color": "",
        "id": "",
        "image": "",
        "image_id": "",
        "image_name": "",
        "source_platform": 0,
        "team_id": "",
        "type": "canvas_color"
    })

    @classmethod
    def from_template(cls, template: Dict[str, Any]) -> "CanvasMaterialModel":
        model = cls()
        model.apply(template or {})
        return model

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class AnimationModel:
    """动画素材模型（单条动画）"""
    data: Dict[str, Any]

    @classmethod
    def from_template(cls, template: Dict[str, Any]) -> "AnimationModel":
        return cls(_deepcopy(template))

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)


@dataclass
class AnimationGroupModel:
    """动画组模型（包含动画列表）"""
    data: Dict[str, Any] = field(default_factory=lambda: {
        "animations": [],
        "id": "",
        "multi_language_current": "none",
        "type": "sticker_animation"
    })

    def apply(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    def to_dict(self) -> Dict[str, Any]:
        return _deepcopy(self.data)

