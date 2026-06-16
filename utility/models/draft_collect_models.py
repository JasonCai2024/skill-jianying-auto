"""
剪辑参数收集模块数据模型
定义用于draft_para_collect模块的数据结构模型
"""

import uuid
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class BaseModel:
    id: str = field(default_factory=lambda: BaseModel.get_random_id())
    @staticmethod
    def get_random_id() -> str:
        return str(uuid.uuid4()).upper()
    def to_dict(self) -> Dict[str, Any]:
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
        return bool(self.id)

@dataclass
class CanvasModel(BaseModel):
    height: int = 1080
    width: int = 1920
    duration: Optional[float] = None
    text_content_split_words: int = 0
    def validate(self) -> bool:
        if not super().validate(): return False
        if not isinstance(self.height, int) or self.height <= 0: return False
        if not isinstance(self.width, int) or self.width <= 0: return False
        if self.duration is not None and (not isinstance(self.duration, (int, float)) or self.duration <= 0): return False
        if not isinstance(self.text_content_split_words, int) or self.text_content_split_words < 0: return False
        return True

@dataclass
class VideoInfoModel(BaseModel):
    """
    视频信息模型类
    定义视频文件的基本信息
    """
    material_name: str = ""
    path: str = ""
    width: int = 0
    height: int = 0
    
    def validate(self) -> bool:
        """
        验证视频信息数据的有效性
        
        Returns:
            bool: 验证结果
        """
        if not super().validate(): return False
        if not isinstance(self.width, int) or self.width <= 0: return False
        if not isinstance(self.height, int) or self.height <= 0: return False
        if not self.material_name: self.material_name = os.path.basename(self.path)
        return True

@dataclass
class PicAnimationModel(BaseModel):
    type: str = ""
    name: str = ""
    start: float = 0.0
    duration: float = 0.0
    def validate(self) -> bool:
        if not super().validate(): return False
        if self.type not in ["in", "out", "loop"]: return False
        if not isinstance(self.start, (int, float)) or self.start < 0: return False
        if not isinstance(self.duration, (int, float)) or self.duration <= 0: return False
        return True

@dataclass 
class KeyframePointModel(BaseModel):
    time_offset: float = 0.0
    values: float = 0.0
    def validate(self) -> bool:
        if not super().validate(): return False
        if not isinstance(self.time_offset, (int, float)) or self.time_offset < 0: return False
        if not isinstance(self.values, (int, float)): return False
        return True

@dataclass
class PicKeyframeModel(BaseModel):
    KFTypePositionX_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    KFTypePositionX: List[KeyframePointModel] = field(default_factory=list)
    KFTypePositionY_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    KFTypePositionY: List[KeyframePointModel] = field(default_factory=list)
    KFTypePositionZ_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    KFTypePositionZ: List[KeyframePointModel] = field(default_factory=list)
    KFTypePositionR_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    KFTypePositionR: List[KeyframePointModel] = field(default_factory=list)
    def validate(self) -> bool:
        if not super().validate(): return False
        for keyframe_list in [self.KFTypePositionX, self.KFTypePositionY, self.KFTypePositionZ, self.KFTypePositionR]:
            for keyframe_point in keyframe_list:
                if not keyframe_point.validate(): return False
        return True

@dataclass
class TrackInfoModel(BaseModel):
    render_index: int = 0
    track_render_index: int = 0
    segments_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    scale_x: float = 1.0
    scale_y: float = 1.0
    transform_x: float = 0.0
    transform_y: float = 0.0
    start: float = 0.0
    duration: float = 0.0
    common_keyframes: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    def validate(self) -> bool:
        if not super().validate(): return False
        for param in [self.scale_x, self.scale_y, self.transform_x, self.transform_y]:
            if not isinstance(param, (int, float)): return False
        if not isinstance(self.start, (int, float)) or self.start < 0: return False
        if not isinstance(self.duration, (int, float)) or self.duration < 0: return False
        if not isinstance(self.common_keyframes, dict): return False
        for keyframe_list in self.common_keyframes.values():
            if not isinstance(keyframe_list, list): return False
            for point in keyframe_list:
                if not isinstance(point, dict): return False
                if "time_offset" not in point or "values" not in point: return False
                if not isinstance(point["time_offset"], (int, float)) or point["time_offset"] < 0: return False
                if not isinstance(point["values"], list): return False
        return True

@dataclass
class PicAnimationModel(BaseModel):
    type: str = ""
    name: str = ""
    start: int = 0
    duration: int = 0
    def validate(self) -> bool:
        if not super().validate(): return False
        if not isinstance(self.type, str): return False
        if not isinstance(self.name, str): return False
        if not isinstance(self.start, int) or self.start < 0: return False
        if not isinstance(self.duration, int) or self.duration <= 0: return False
        return True

@dataclass
class MaterialAnimationModel(BaseModel):
    animations: List[PicAnimationModel] = field(default_factory=list)
    def validate(self) -> bool:
        if not super().validate(): return False
        for animation in self.animations:
            if not animation.validate(): return False
        return True

@dataclass
class AudioTrackModel(BaseModel):
    volume: float = 0.0
    start: float = 0.0
    duration: float = 0.0
    def validate(self) -> bool:
        if not super().validate(): return False
        if not isinstance(self.volume, (int, float)): return False
        if not isinstance(self.start, (int, float)) or self.start < 0: return False
        if not isinstance(self.duration, (int, float)) or self.duration <= 0: return False
        return True

@dataclass
class BaseAudioModel(BaseModel):
    beats_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    sound_channel_mappings_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    speeds_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    vocal_separations_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    duration: float = 0.0
    name: str = ""
    path: str = ""
    tracks: AudioTrackModel = field(default_factory=AudioTrackModel)
    def validate(self) -> bool:
        if not super().validate(): return False
        if not self.path: return False
        if not isinstance(self.duration, (int, float)) or self.duration <= 0: return False
        if not self.name: self.name = os.path.basename(self.path)
        if not self.tracks.validate(): return False
        return True

@dataclass
class BGMModel(BaseAudioModel): pass
@dataclass
class VoiceModel(BaseAudioModel): pass
@dataclass
class SoundModel(BaseAudioModel): pass

@dataclass
class TrackItemModel(BaseModel):
    track_render_index: int = 0
    id: str = field(default_factory=lambda: BaseModel.get_random_id())
    def validate(self) -> bool:
        if not super().validate(): return False
        if not isinstance(self.track_render_index, int) or self.track_render_index < 0: return False
        return True

@dataclass
class TracksModel:
    pics_track: List[TrackItemModel] = field(default_factory=list)
    texts_track: List[TrackItemModel] = field(default_factory=list)
    bgms_track_id: str = ""
    voices_track_id: str = ""
    sounds_track_id: str = ""
    def to_dict(self) -> Dict[str, Any]:
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
        for track_item in self.pics_track:
            if not track_item.validate(): return False
        for track_item in self.texts_track:
            if not track_item.validate(): return False
        return True

@dataclass
class PicModel(BaseModel):
    canvases_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    material_animations: MaterialAnimationModel = field(default_factory=MaterialAnimationModel)
    sound_channel_mappings_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    speeds_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    vocal_separations_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    material_name: str = ""
    path: str = ""
    width: int = 0
    height: int = 0
    tracks: TrackInfoModel = field(default_factory=TrackInfoModel)
    def validate(self) -> bool:
        if not super().validate(): return False
        if not self.path: return False
        if not isinstance(self.width, int) or self.width <= 0: return False
        if not isinstance(self.height, int) or self.height <= 0: return False
        if not self.material_name: self.material_name = os.path.basename(self.path)
        if not self.material_animations.validate(): return False
        if not self.tracks.validate(): return False
        return True

@dataclass
class TextAnimationModel(BaseModel):
    type: str = ""
    name: str = ""
    start: float = 0.0
    duration: float = 0.0
    def validate(self) -> bool:
        if not super().validate(): return False
        if self.type not in ["in", "out", "loop"]: return False
        if not isinstance(self.start, (int, float)) or self.start < 0: return False
        if not isinstance(self.duration, (int, float)) or self.duration <= 0: return False
        return True

@dataclass
class TextMaterialAnimationModel(BaseModel):
    animations: List[TextAnimationModel] = field(default_factory=list)
    def validate(self) -> bool:
        if not super().validate(): return False
        for animation in self.animations:
            if not animation.validate(): return False
        return True

@dataclass
class TextTrackModel(BaseModel):
    render_index: int = 0
    track_render_index: int = 0
    segments_id: str = field(default_factory=lambda: BaseModel.get_random_id())
    scale_x: float = 1.0
    scale_y: float = 1.0
    transform_x: float = 0.0
    transform_y: float = 0.0
    start: float = 0.0
    duration: float = 0.0
    def validate(self) -> bool:
        if not super().validate(): return False
        for param in [self.scale_x, self.scale_y, self.transform_x, self.transform_y]:
            if not isinstance(param, (int, float)): return False
        if not isinstance(self.start, (int, float)) or self.start < 0: return False
        if not isinstance(self.duration, (int, float)) or self.duration < 0: return False
        return True

@dataclass
class TextModel(BaseModel):
    content: str = ""
    text_color: str = "white"
    text_size: int = 20
    border_color: str = "black"
    border_width: float = 0.1
    font_name: str = ""
    font_size: int = 20
    letter_spacing: float = 0.0
    line_spacing: float = 0.0
    material_animations: TextMaterialAnimationModel = field(default_factory=TextMaterialAnimationModel)
    tracks: TextTrackModel = field(default_factory=TextTrackModel)
    def validate(self) -> bool:
        if not super().validate(): return False
        if not self.content: return False
        if not isinstance(self.text_size, int) or self.text_size <= 0: return False
        if not isinstance(self.font_size, int) or self.font_size <= 0: return False
        if not isinstance(self.border_width, (int, float)) or self.border_width < 0: return False
        if not isinstance(self.letter_spacing, (int, float)): return False
        if not isinstance(self.line_spacing, (int, float)): return False
        if not self.material_animations.validate(): return False
        if not self.tracks.validate(): return False
        return True 

