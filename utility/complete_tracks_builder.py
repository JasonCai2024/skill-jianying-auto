#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整的tracks和keyframes结构创建器
基于源草稿的精确结构匹配
"""

import json
import uuid
from typing import Dict, Any, List

class CompleteTracksBuilder:
    """完整的tracks结构创建器"""
    
    def __init__(self):
        """初始化tracks构建器"""
        pass

    def _stable_uuid(self, *parts: Any) -> str:
        seed = "|".join(str(part) for part in parts)
        return str(uuid.uuid5(uuid.NAMESPACE_URL, seed)).upper()
    
    def create_complete_keyframes(self, material_id: str, property_type: str) -> List[Dict[str, Any]]:
        """创建完整的common_keyframes结构（匹配参考草稿格式）"""
        return [
            {
                "id": self._stable_uuid(material_id, property_type, "default"),
                "keyframe_list": [
                    {
                        "curveType": "Line",
                        "graphID": "",
                        "id": self._stable_uuid(material_id, property_type, "kf0"),
                        "left_control": {"x": 0.0, "y": 0.0},
                        "right_control": {"x": 0.0, "y": 0.0},
                        "time_offset": 0,
                        "values": [1.0]
                    }
                ],
                "material_id": "",
                "property_type": property_type
            }
        ]
    
    def create_complete_clip(self) -> Dict[str, Any]:
        """创建完整的clip结构"""
        return {
            "alpha": 1.0,
            "flip": {
                "horizontal": False,
                "vertical": False
            },
            "rotation": 0.0,
            "scale": {
                "x": 1.0,
                "y": 1.0
            },
            "transform": {
                "x": -0.37807183364839314,
                "y": 0.0
            }
        }
    
    def create_complete_responsive_layout(self) -> Dict[str, Any]:
        """创建完整的responsive_layout结构"""
        return {
            "enable": False,
            "horizontal_pos_layout": 0,
            "size_layout": 0,
            "target_follow": "",
            "vertical_pos_layout": 0
        }
    
    def create_complete_hdr_settings(self) -> Dict[str, Any]:
        """创建完整的hdr_settings结构"""
        return {
            "intensity": 1.0,
            "mode": 1,
            "nits": 1000
        }
    
    def create_complete_uniform_scale(self) -> Dict[str, Any]:
        """创建完整的uniform_scale结构"""
        return {
            "on": True,
            "value": 1.0
        }

    def _sort_dict_recursive(self, value):
        if isinstance(value, dict):
            return {k: self._sort_dict_recursive(value[k]) for k in sorted(value)}
        if isinstance(value, list):
            return [self._sort_dict_recursive(item) for item in value]
        return value

    def _to_microseconds(self, value: float) -> int:
        if value is None:
            return 0
        if abs(value) < 1000:
            return int(round(value * 1_000_000))
        return int(round(value))

    def _to_relative(self, value: float, size: float) -> float:
        if size <= 0:
            return value
        if abs(value) > 2:
            return value / size
        return value

    def _to_scale_ratio(self, value: float) -> float:
        if value is None:
            return 1.0
        if value > 10:
            return value / 100.0
        return value

    def _build_keyframe_groups(self, segment_id: str, kfd: Dict[str, Any], canvas_width: float, canvas_height: float) -> List[Dict[str, Any]]:
        groups = []
        for kftype, kflist in kfd.items():
            if not isinstance(kflist, list) or not kflist:
                continue
            group_id = None
            if isinstance(kflist[0], dict):
                group_id = kflist[0].get('group_id')
            if not group_id:
                group_id = self._stable_uuid(segment_id, kftype, "group")
            lst = []
            for idx, it in enumerate(kflist):
                raw_value = it.get('values', [0])[0] if it.get('values') else 0
                if kftype == "KFTypePositionX":
                    values = [self._to_relative(raw_value, canvas_width)]
                elif kftype == "KFTypePositionY":
                    values = [self._to_relative(raw_value, canvas_height)]
                elif kftype == "KFTypeScaleX":
                    values = [self._to_scale_ratio(raw_value)]
                elif kftype == "KFTypeScaleY":
                    values = [self._to_scale_ratio(raw_value)]
                else:
                    values = [raw_value]
                kf_id = it.get('id') or self._stable_uuid(segment_id, kftype, idx, it.get('time_offset'), raw_value)
                lst.append({
                    "curveType": "Line",
                    "graphID": "",
                    "id": kf_id,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": 0.0, "y": 0.0},
                    "time_offset": self._to_microseconds(it.get('time_offset', 0)),
                    "values": values
                })
            groups.append({
                "id": group_id,
                "keyframe_list": lst,
                "material_id": "",
                "property_type": kftype
            })
        return groups
    
    def create_complete_segment(self, segment_type: str, material_id: str, render_index: int, 
                           track_render_index: int, source_duration: int, target_start: int) -> Dict[str, Any]:
        """创建完整的segment结构"""
        base_segment = {
            "caption_info": None,
            "cartoon": False,
            "common_keyframes": [],
            "enable_adjust": True,
            "enable_color_correct_adjust": False,
            "enable_color_curves": True,
            "enable_color_match_adjust": False,
            "enable_color_wheels": True,
            "enable_lut": True,
            "enable_smart_color_adjust": False,
            "extra_material_refs": [],
            "group_id": "",
            "hdr_settings": self.create_complete_hdr_settings(),
            "id": str(uuid.uuid4()).upper(),
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 1.0,
            "material_id": material_id,
            "render_index": render_index,
            "responsive_layout": self.create_complete_responsive_layout(),
            "reverse": False,
            "source_timerange": {
                "duration": source_duration,
                "start": 0
            },
            "speed": 1.0,
            "target_timerange": {
                "duration": source_duration,
                "start": target_start
            },
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": track_render_index,
            "uniform_scale": self.create_complete_uniform_scale(),
            "visible": True,
            "volume": 1.0
        }
        
        # 为视频和文本轨道添加clip和keyframes
        if segment_type in ["video", "text"]:
            base_segment["clip"] = self.create_complete_clip()
            base_segment["common_keyframes"] = self.create_complete_keyframes(material_id, "transform")
        
        return base_segment
    
    def create_complete_tracks(self, draft_para_collect: Dict[str, Any]) -> List[Dict[str, Any]]:
        tracks = []
        videos = draft_para_collect.get('videos', []) or []
        texts = draft_para_collect.get('texts', []) or []
        audios = draft_para_collect.get('audios', []) or []
        trinfo = draft_para_collect.get('tracks', {}) or {}
        canvas = draft_para_collect.get('canvas', {}) or {}
        canvas_width = canvas.get('width', 1920)
        canvas_height = canvas.get('height', 1080)
        for info in trinfo.get('video_track', []) or []:
            segs = []
            for p in videos:
                pt = p.get('tracks', {}) or {}
                if pt.get('track_render_index') == info.get('track_render_index'):
                    sd = int((pt.get('duration', 0) or 0) * 1000000)
                    ts = int((pt.get('start', 0) or 0) * 1000000)
                    seg = self.create_complete_segment('video', p.get('id', ''), info.get('track_render_index', 0), info.get('track_render_index', 0), sd, ts)
                    seg['id'] = pt.get('segments_id', seg.get('id'))
                    clip = seg.get('clip', {})
                    clip['scale'] = {"x": pt.get('scale_x', 1.0), "y": pt.get('scale_y', 1.0)}
                    clip['transform'] = {
                        "x": self._to_relative(pt.get('transform_x', 0.0), canvas_width),
                        "y": self._to_relative(pt.get('transform_y', 0.0), canvas_height)
                    }
                    kfd = pt.get('common_keyframes', {}) or {}
                    ckfs = self._build_keyframe_groups(seg.get('id', ''), kfd, canvas_width, canvas_height)
                    if ckfs:
                        seg['common_keyframes'] = ckfs
                    seg['extra_material_refs'] = [
                        p.get('speeds_id', ''),
                        p.get('canvases_id', ''),
                        (pt.get('material_animations', {}) or {}).get('id', ''),
                        p.get('sound_channel_mappings_id', ''),
                        p.get('vocal_separations_id', '')
                    ]
                    segs.append(seg)
            if segs:
                tracks.append({
                    "attribute": 0,
                    "flag": 0,
                    "id": info.get('id', ''),
                    "is_default_name": True,
                    "name": "",
                    "segments": segs,
                    "type": "video"
                })
        for info in trinfo.get('texts_track', []) or []:
            segs = []
            for t in texts:
                tt = t.get('tracks', {}) or {}
                if tt.get('track_render_index') == info.get('track_render_index'):
                    sd = int((tt.get('duration', 0) or 0) * 1000000)
                    ts = int((tt.get('start', 0) or 0) * 1000000)
                    seg = self.create_complete_segment('text', t.get('id', ''), info.get('track_render_index', 0), info.get('track_render_index', 0), sd, ts)
                    clip = seg.get('clip', {})
                    clip['scale'] = {"x": tt.get('scale_x', 1.0), "y": tt.get('scale_y', 1.0)}
                    clip['transform'] = {"x": tt.get('transform_x', 0.0), "y": tt.get('transform_y', 0.0)}
                    kfd = tt.get('common_keyframes', {}) or {}
                    ckfs = []
                    for kftype, kflist in kfd.items():
                        if isinstance(kflist, list) and kflist:
                            lst = []
                            for it in kflist:
                                lst.append({
                                    "time_offset": int(round(it.get('time_offset', 0) * 1000000)),
                                    "x": it.get('values', [0])[0] if it.get('values') else 0,
                                    "y": 0,
                                    "left_control": {"x": 0, "y": 0},
                                    "right_control": {"x": 0, "y": 0}
                                })
                            ckfs.append({"property_type": kftype, "keyframe_list": lst})
                    if ckfs:
                        seg['common_keyframes'] = ckfs
                    manims = tt.get('material_animations') or {}
                    anim_id = manims.get('id', '')
                    if anim_id:
                        seg['extra_material_refs'] = [anim_id]
                    segs.append(seg)
            if segs:
                tracks.append({
                    "attribute": 0,
                    "flag": 0,
                    "id": info.get('id', ''),
                    "is_default_name": True,
                    "name": "",
                    "segments": segs,
                    "type": "text"
                })
        audio_indices = sorted(set((a.get('tracks', {}) or {}).get('track_render_index') for a in audios))
        for idx in audio_indices:
            if idx is None:
                continue
            segs = []
            for a in audios:
                at = a.get('tracks', {}) or {}
                if at.get('track_render_index') == idx:
                    start_us = int((at.get('start', 0) or 0) * 1000000)
                    dur_us = int((at.get('segment_duration', a.get('duration', 0)) or 0) * 1000000)
                    if dur_us <= 0:
                        fallback = int((a.get('duration', 0) or 0) * 1000000)
                        dur_us = fallback if fallback > 0 else int(0.1 * 1000000)
                    seg = self.create_complete_segment('audio', a.get('id', ''), idx, idx, dur_us, start_us)
                    seg['extra_material_refs'] = [
                        a.get('speeds_id', ''),
                        a.get('beats_id', ''),
                        a.get('sound_channel_mappings_id', ''),
                        a.get('vocal_separations_id', '')
                    ]
                    segs.append(seg)
            if segs:
                match = None
                for it in trinfo.get('audios_track', []) or []:
                    if it.get('track_render_index') == idx:
                        match = it
                        break
                tracks.append({
                    "attribute": 0,
                    "flag": 0,
                    "id": (match or {}).get('id', ''),
                    "is_default_name": True,
                    "name": "",
                    "segments": segs,
                    "type": "audio"
                })
        return [self._sort_dict_recursive(track) for track in tracks]

class CompletePlatformBuilder:
    """完整的platform结构创建器"""
    
    def create_complete_platform(self) -> Dict[str, Any]:
        """创建完整的platform结构（8个字段）"""
        return {
            "app_id": 3704,
            "bundle_id": "",
            "device_id": "",
            "install_id": "",
            "language": "zh",
            "platform": "windows",
            "version": "26.2.0",
            "version_code": 260200
        }
    
    def create_complete_last_modified_platform(self) -> Dict[str, Any]:
        """创建完整的last_modified_platform结构（8个字段）"""
        return {
            "app_id": 3704,
            "bundle_id": "",
            "device_id": "",
            "install_id": "",
            "language": "zh",
            "platform": "windows",
            "version": "26.2.0",
            "version_code": 260200
        }
