#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
草稿合成数据模型 - 修复版本
基于参考草稿的实际结构，提供类型安全的数据模型

主要修复：
1. 添加缺失的重要字段
2. 修正字段类型和默认值
3. 确保与参考草稿完全一致

作者: AutoCut 项目开发组
版本: 3.0 (修复版本)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum


class CurveType(Enum):
    """关键帧曲线类型"""
    LINE = "Line"
    EASE_IN = "EaseIn"
    EASE_OUT = "EaseOut"
    EASE_IN_OUT = "EaseInOut"
    STEP = "Step"
    CUSTOM = "Custom"


class PropertyType(Enum):
    """动画属性类型"""
    POSITION_X = "KFTypePositionX"
    POSITION_Y = "KFTypePositionY"
    SCALE_X = "KFTypeScaleX"
    SCALE_Y = "KFTypeScaleY"
    ROTATION = "KFTypeRotation"
    ALPHA = "KFTypeAlpha"


class TrackType(Enum):
    """轨道类型"""
    VIDEO = "video"
    TEXT = "text"
    AUDIO = "audio"


@dataclass
class ClipModel:
    """Clip模型 - 基于参考草稿的实际结构"""
    alpha: float = 1.0
    flip: Dict[str, bool] = field(default_factory=lambda: {"horizontal": False, "vertical": False})
    rotation: float = 0.0
    scale: Dict[str, float] = field(default_factory=lambda: {"x": 1.0, "y": 1.0})
    transform: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})


@dataclass
class ControlPoint:
    """贝塞尔控制点"""
    x: float = 0.0
    y: float = 0.0


@dataclass
class KeyframePoint:
    """关键帧点 - 基于参考草稿的完整结构"""
    curve_type: str = "Line"
    graph_id: str = ""
    id: str = ""
    time_offset: int = 0
    values: List[float] = field(default_factory=list)
    left_control: ControlPoint = field(default_factory=ControlPoint)
    right_control: ControlPoint = field(default_factory=ControlPoint)
    
    def __post_init__(self):
        """后处理：确保字段类型正确"""
        if isinstance(self.curve_type, CurveType):
            self.curve_type = self.curve_type.value
        if isinstance(self.values, (int, float)):
            self.values = [float(self.values)]


@dataclass
class CommonKeyframe:
    """关键帧组 - 基于参考草稿的实际结构"""
    id: str = ""
    property_type: str = ""
    material_id: str = ""  # 🚨 重要：参考草稿中为空字符串
    keyframe_list: List[KeyframePoint] = field(default_factory=list)
    
    def __post_init__(self):
        """后处理：确保属性类型正确"""
        if isinstance(self.property_type, PropertyType):
            self.property_type = self.property_type.value


@dataclass
class HDRSettings:
    """HDR设置 - 基于参考草稿的实际结构"""
    intensity: float = 1.0
    mode: int = 1
    nits: int = 1000


@dataclass
class ResponsiveLayout:
    """响应式布局 - 基于参考草稿的实际结构"""
    enable: bool = False
    horizontal_pos_layout: int = 0
    size_layout: int = 0
    target_follow: str = ""
    vertical_pos_layout: int = 0


@dataclass
class UniformScale:
    """统一缩放 - 基于参考草稿的实际结构"""
    on: bool = True  # 🚨 重要：字段名是"on"不是"enabled"
    value: float = 1.0


@dataclass
class TimeRange:
    """时间范围"""
    duration: int = 0
    start: int = 0


@dataclass
class SegmentModel:
    """Segment模型 - 基于参考草稿的完整结构"""
    # 🔑 基础标识字段
    id: str = ""
    material_id: str = ""
    render_index: int = 0
    track_render_index: int = 0
    
    # 🎬 视觉控制字段
    clip: Optional[ClipModel] = None
    common_keyframes: List[CommonKeyframe] = field(default_factory=list)
    
    # 🎵 音频特有字段
    audio_type: int = 0
    fade_in: int = 0
    fade_out: int = 0
    audio_gain_type: int = 0
    
    # ⚙️ 系统控制字段 - 与参考草稿完全一致
    caption_info: Optional[Dict[str, Any]] = None
    cartoon: bool = False
    enable_adjust: bool = True
    enable_color_correct_adjust: bool = False
    enable_color_curves: bool = True
    enable_color_match_adjust: bool = False
    enable_color_wheels: bool = True
    enable_lut: bool = True
    enable_smart_color_adjust: bool = False
    
    # 🔗 资源引用字段
    extra_material_refs: List[str] = field(default_factory=list)
    group_id: str = ""
    
    # 🎨 HDR和布局字段
    hdr_settings: HDRSettings = field(default_factory=HDRSettings)
    responsive_layout: ResponsiveLayout = field(default_factory=ResponsiveLayout)
    uniform_scale: UniformScale = field(default_factory=UniformScale)
    
    # 🏷️ 其他重要字段
    intensifies_audio: bool = False
    is_placeholder: bool = False
    is_tone_modify: bool = False
    keyframe_refs: List[str] = field(default_factory=list)
    last_nonzero_volume: float = 1.0
    reverse: bool = False
    speed: float = 1.0
    template_id: str = ""
    template_scene: str = "default"
    track_attribute: int = 0
    visible: bool = True
    volume: float = 1.0
    
    # ⏱️ 时间控制字段
    source_timerange: TimeRange = field(default_factory=TimeRange)
    target_timerange: TimeRange = field(default_factory=TimeRange)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        
        # 处理基础字段
        for field_name, field_value in self.__dataclass_fields__.items():
            if field_name in ['clip', 'common_keyframes', 'hdr_settings', 
                            'responsive_layout', 'uniform_scale', 
                            'source_timerange', 'target_timerange']:
                if field_value:
                    if hasattr(field_value, 'to_dict'):
                        result[field_name] = field_value.to_dict()
                    elif isinstance(field_value, list):
                        result[field_name] = [item.to_dict() if hasattr(item, 'to_dict') else item 
                                           for item in field_value]
                    else:
                        result[field_name] = field_value
            else:
                result[field_name] = field_value
        
        return result
    
    @classmethod
    def __dataclass_fields__(cls):
        """获取数据类字段"""
        import inspect
        return {name: getattr(cls, name) 
                for name, _ in inspect.getmembers(cls) 
                if not name.startswith('_') and not inspect.ismethod(getattr(cls, name))}


@dataclass
class TrackModel:
    """轨道模型 - 基于参考草稿的实际结构"""
    attribute: int = 0
    flag: int = 0
    id: str = ""
    is_default_name: bool = True
    name: str = ""
    segments: List[Union[SegmentModel, Dict[str, Any]]] = field(default_factory=list)
    type: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "attribute": self.attribute,
            "flag": self.flag,
            "id": self.id,
            "is_default_name": self.is_default_name,
            "name": self.name,
            "segments": [seg.to_dict() if hasattr(seg, 'to_dict') else seg 
                       for seg in self.segments],
            "type": self.type
        }


@dataclass
class CanvasConfigModel:
    """画布配置模型"""
    width: int = 1920
    height: int = 1080
    ratio: str = "16:9"
    color_space: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "width": self.width,
            "height": self.height,
            "ratio": self.ratio,
            "color_space": self.color_space
        }


@dataclass
class DraftContentModel:
    """草稿内容模型"""
    canvas_config: CanvasConfigModel
    tracks: List[TrackModel] = field(default_factory=list)
    materials: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    keyframes: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    duration: int = 0
    fps: float = 30.0
    id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "canvas_config": self.canvas_config.to_dict(),
            "tracks": [track.to_dict() for track in self.tracks],
            "materials": self.materials,
            "keyframes": self.keyframes,
            "duration": self.duration,
            "fps": self.fps,
            "id": self.id
        }


# 便捷创建函数
def create_clip_from_params(scale_x: float = 1.0, scale_y: float = 1.0,
                       transform_x: float = 0.0, transform_y: float = 0.0,
                       rotation: float = 0.0, alpha: float = 1.0) -> ClipModel:
    """从参数创建Clip模型"""
    return ClipModel(
        alpha=alpha,
        rotation=rotation,
        scale={"x": scale_x, "y": scale_y},
        transform={"x": transform_x, "y": transform_y}
    )


def create_keyframe_from_params(property_type: str, keyframe_data: List[Dict[str, Any]], 
                           material_id: str = "") -> CommonKeyframe:
    """从参数创建关键帧模型"""
    keyframe_list = []
    for kf in keyframe_data:
        keyframe_point = KeyframePoint(
            curve_type=kf.get('curve_type', 'Line'),
            graph_id=kf.get('graph_id', ''),
            id=kf.get('id', ''),
            time_offset=kf.get('time_offset', 0),
            values=kf.get('values', [0.0]),
            left_control=ControlPoint(**kf.get('left_control', {'x': 0.0, 'y': 0.0})),
            right_control=ControlPoint(**kf.get('right_control', {'x': 0.0, 'y': 0.0}))
        )
        keyframe_list.append(keyframe_point)
    
    return CommonKeyframe(
        id=str(uuid.uuid4()).upper(),
        property_type=property_type,
        material_id=material_id,  # 通常是空字符串
        keyframe_list=keyframe_list
    )


def main():
    """测试函数"""
    import uuid
    import json
    
    # 测试Clip模型
    clip = create_clip_from_params(scale_x=1.5, transform_x=-100.5)
    print("Clip模型:")
    print(json.dumps(clip.__dict__, indent=2, ensure_ascii=False))
    
    # 测试关键帧模型
    kf_data = [
        {"time_offset": 1000000, "values": [0.0]},
        {"time_offset": 3000000, "values": [100.0]}
    ]
    keyframe = create_keyframe_from_params("KFTypePositionX", kf_data)
    print("\n关键帧模型:")
    print(json.dumps(keyframe.__dict__, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()