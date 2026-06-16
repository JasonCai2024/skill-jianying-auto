"""
剪辑合成模块数据模型
定义用于draft_config_comb模块的数据结构模型
"""

import uuid
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class AnimationPathModel:
    """动画路径模型，包含路径和验证信息"""
    animation_path: str
    content_path: str
    prefab_path: str
    script_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "animation_path": self.animation_path,
            "content_path": self.content_path,
            "prefab_path": self.prefab_path,
            "script_path": self.script_path
        }
    
    def validate(self) -> bool:
        """验证动画路径是否有效"""
        return bool(self.animation_path and self.content_path and self.prefab_path)

@dataclass
class BaseCombModel:
    @staticmethod
    def get_random_id() -> str:
        return str(uuid.uuid4()).upper()
    def ensure_id(self) -> str:
        if not hasattr(self, 'id') or not self.id:
            self.id = self.get_random_id()
        return self.id
    def to_dict(self) -> Dict[str, Any]:
        self.ensure_id()
        result = {}
        for key, value in self.__dict__.items():
            if hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in value]
            else:
                result[key] = value
        return result
    def validate(self) -> bool:
        self.ensure_id()
        return bool(getattr(self, 'id', None))

@dataclass
class CanvasConfigModel(BaseCombModel):
    height: int = 1080
    ratio: str = "original"
    width: int = 1920
    def validate(self) -> bool:
        if not super().validate(): return False
        if self.height <= 0 or self.width <= 0: return False
        return True

@dataclass
class TrackModel(BaseCombModel):
    attribute: int = 0
    flag: int = 0
    id: str = field(default_factory=lambda: BaseCombModel.get_random_id())
    is_default_name: bool = True
    name: str = ""
    segments: List[Dict[str, Any]] = field(default_factory=list)
    track_type: str = ""
    def validate(self) -> bool:
        if not super().validate(): return False
        if self.track_type not in ["video", "text", "audio"]: return False
        return True
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if 'track_type' in result:
            result['type'] = result.pop('track_type')
        return result

@dataclass
class MaterialsMainModel:
    """
    materials 一级子字段默认结构（对应 materials_main_structure.json）
    仅定义字段与默认空列表，避免依赖 json 模板文件
    """
    ai_translates: List[Any] = field(default_factory=list)
    audio_balances: List[Any] = field(default_factory=list)
    audio_effects: List[Any] = field(default_factory=list)
    audio_fades: List[Any] = field(default_factory=list)
    audio_track_indexes: List[Any] = field(default_factory=list)
    audios: List[Any] = field(default_factory=list)
    beats: List[Any] = field(default_factory=list)
    canvases: List[Any] = field(default_factory=list)
    chromas: List[Any] = field(default_factory=list)
    color_curves: List[Any] = field(default_factory=list)
    digital_humans: List[Any] = field(default_factory=list)
    drafts: List[Any] = field(default_factory=list)
    effects: List[Any] = field(default_factory=list)
    flowers: List[Any] = field(default_factory=list)
    green_screens: List[Any] = field(default_factory=list)
    handwrites: List[Any] = field(default_factory=list)
    hsl: List[Any] = field(default_factory=list)
    images: List[Any] = field(default_factory=list)
    log_color_wheels: List[Any] = field(default_factory=list)
    loudnesses: List[Any] = field(default_factory=list)
    manual_deformations: List[Any] = field(default_factory=list)
    masks: List[Any] = field(default_factory=list)
    material_animations: List[Any] = field(default_factory=list)
    material_colors: List[Any] = field(default_factory=list)
    multi_language_refs: List[Any] = field(default_factory=list)
    placeholders: List[Any] = field(default_factory=list)
    plugin_effects: List[Any] = field(default_factory=list)
    primary_color_wheels: List[Any] = field(default_factory=list)
    realtime_denoises: List[Any] = field(default_factory=list)
    shapes: List[Any] = field(default_factory=list)
    smart_crops: List[Any] = field(default_factory=list)
    smart_relights: List[Any] = field(default_factory=list)
    sound_channel_mappings: List[Any] = field(default_factory=list)
    speeds: List[Any] = field(default_factory=list)
    stickers: List[Any] = field(default_factory=list)
    tail_leaders: List[Any] = field(default_factory=list)
    text_templates: List[Any] = field(default_factory=list)
    texts: List[Any] = field(default_factory=list)
    time_marks: List[Any] = field(default_factory=list)
    transitions: List[Any] = field(default_factory=list)
    video_effects: List[Any] = field(default_factory=list)
    video_trackings: List[Any] = field(default_factory=list)
    videos: List[Any] = field(default_factory=list)
    vocal_beautifys: List[Any] = field(default_factory=list)
    vocal_separations: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ai_translates": self.ai_translates,
            "audio_balances": self.audio_balances,
            "audio_effects": self.audio_effects,
            "audio_fades": self.audio_fades,
            "audio_track_indexes": self.audio_track_indexes,
            "audios": self.audios,
            "beats": self.beats,
            "canvases": self.canvases,
            "chromas": self.chromas,
            "color_curves": self.color_curves,
            "digital_humans": self.digital_humans,
            "drafts": self.drafts,
            "effects": self.effects,
            "flowers": self.flowers,
            "green_screens": self.green_screens,
            "handwrites": self.handwrites,
            "hsl": self.hsl,
            "images": self.images,
            "log_color_wheels": self.log_color_wheels,
            "loudnesses": self.loudnesses,
            "manual_deformations": self.manual_deformations,
            "masks": self.masks,
            "material_animations": self.material_animations,
            "material_colors": self.material_colors,
            "multi_language_refs": self.multi_language_refs,
            "placeholders": self.placeholders,
            "plugin_effects": self.plugin_effects,
            "primary_color_wheels": self.primary_color_wheels,
            "realtime_denoises": self.realtime_denoises,
            "shapes": self.shapes,
            "smart_crops": self.smart_crops,
            "smart_relights": self.smart_relights,
            "sound_channel_mappings": self.sound_channel_mappings,
            "speeds": self.speeds,
            "stickers": self.stickers,
            "tail_leaders": self.tail_leaders,
            "text_templates": self.text_templates,
            "texts": self.texts,
            "time_marks": self.time_marks,
            "transitions": self.transitions,
            "video_effects": self.video_effects,
            "video_trackings": self.video_trackings,
            "videos": self.videos,
            "vocal_beautifys": self.vocal_beautifys,
            "vocal_separations": self.vocal_separations
        }

@dataclass
class DraftContentModel(BaseCombModel):
    canvas_config: CanvasConfigModel = field(default_factory=CanvasConfigModel)
    tracks: List[TrackModel] = field(default_factory=list)
    materials: MaterialsMainModel = field(default_factory=MaterialsMainModel)
    name: str = ""
    version: int = 1
    def validate(self) -> bool:
        if not super().validate(): return False
        if not self.canvas_config.validate(): return False
        for track in self.tracks:
            if not track.validate(): return False
        return True

