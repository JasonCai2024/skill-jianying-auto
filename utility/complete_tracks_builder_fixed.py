#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整轨道构建器 - 修复版本
根据参考草稿的实际结构，生成完全符合剪映标准的tracks字段

主要修复：
1. 修正uniform_scale、hdr_settings、responsive_layout的实际字段结构
2. 修正关键帧的完整格式（包含所有必需字段）
3. 添加缺失的重要字段
4. 确保所有UUID生成和字段值与参考草稿一致

作者: AutoCut 项目开发组
版本: 3.0 (修复版本)
"""

import uuid
from typing import Dict, List, Any, Optional

from .models.draft_comb_models import TrackModel
from .models.segment_models import VideoSegmentModel, TextSegmentModel, AudioSegmentModel


class CompleteTracksBuilderFixed:
    """
    完整轨道构建器 - 修复版本
    
    基于参考草稿 D:\\JianyingPro Drafts\\test1\\draft_content.json
    的实际结构，生成完全符合剪映标准的tracks字段
    """
    
    def __init__(self):
        self.logger = None  # 可选的日志记录器
    
    def log_info(self, message: str):
        """记录信息日志"""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"[INFO] {message}")
    
    def log_error(self, message: str):
        """记录错误日志"""
        if self.logger:
            self.logger.error(message)
        else:
            print(f"[ERROR] {message}")
    
    def get_random_id(self) -> str:
        """生成随机ID"""
        return str(uuid.uuid4()).upper()

    def _stable_uuid(self, *parts: Any) -> str:
        seed = "|".join(str(part) for part in parts)
        return str(uuid.uuid5(uuid.NAMESPACE_URL, seed)).upper()

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
    
    def create_complete_tracks(self, draft_para_collect: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        创建完整的tracks结构
        
        Args:
            draft_para_collect (Dict[str, Any]): 参数收集字典
            
        Returns:
            List[Dict[str, Any]]: 完整的tracks数组
        """
        try:
            tracks = []
            
            # 获取各类型素材（仅使用 videos）
            pics = draft_para_collect.get('videos') or []
            texts = draft_para_collect.get('texts') or []
            # ext 将音频统一在 audios，原项目可能分 bgms/voices/sounds
            audios_unified = draft_para_collect.get('audios') or []
            if not audios_unified:
                audios_unified = []
                for k in ('bgms', 'voices', 'sounds'):
                    audios_unified.extend(draft_para_collect.get(k, []) or [])
            
            canvas = draft_para_collect.get('canvas', {}) or {}
            canvas_width = canvas.get('width', 1920)
            canvas_height = canvas.get('height', 1080)

            # 处理视频轨道（图片）
            if pics:
                # 获取轨道信息
                tracks_info = draft_para_collect.get('tracks', {}).get('video_track', [])
                for track_info in tracks_info:
                    track_render_index = track_info.get('track_render_index', 0)
                    segments = []
                    
                    # 收集该轨道的所有图片
                    track_pics = [pic for pic in pics 
                               if (pic.get('tracks', {}) or {}).get('track_render_index') == track_render_index]
                    
                    for pic_idx, pic in enumerate(track_pics):
                        pic_tracks = pic.get('tracks', {})
                        segment = self._create_video_segment(pic, pic_idx, canvas_width, canvas_height)
                        segments.append(segment)
                    
                    if segments:
                        if not track_info.get("id"):
                            raise ValueError(f"视频轨道缺少 id: track_render_index={track_render_index}")
                        track = self._create_video_track(track_info, segments)
                        tracks.append(track)
            
            # 处理文字轨道
            if texts:
                tracks_info = draft_para_collect.get('tracks', {}).get('texts_track', [])
                for track_info in tracks_info:
                    track_render_index = track_info.get('track_render_index', 0)
                    segments = []
                    
                    # 收集该轨道的所有文字
                    track_texts = [text for text in texts 
                                if (text.get('tracks', {}) or {}).get('track_render_index') == track_render_index]
                    
                    for text_idx, text in enumerate(track_texts):
                        segment = self._create_text_segment(text, text_idx, canvas_width, canvas_height)
                        segments.append(segment)
                    
                    if segments:
                        if not track_info.get("id"):
                            raise ValueError(f"文字轨道缺少 id: track_render_index={track_render_index}")
                        track = self._create_text_track(track_info, segments)
                        tracks.append(track)
            
            # 处理音频轨道（统一 audio 类型，按 track_render_index 分组）
            audio_tracks_by_index: Dict[int, Dict[str, Any]] = {}
            audios_track_list = draft_para_collect.get('tracks', {}).get('audios_track', []) or []
            sorted_audios_track = sorted(
                audios_track_list,
                key=lambda x: x.get('track_render_index', 0)
            )
            index_map = [
                {
                    "track_render_index": it.get("track_render_index", 0),
                    "id": it.get("id")
                }
                for it in sorted_audios_track
            ]

            for audio in audios_unified:
                at = audio.get('tracks', {}) or {}
                idx = at.get('track_render_index', 0)
                if idx >= len(index_map):
                    raise ValueError(f"音频轨道索引超出范围: track_render_index={idx}")
                mapped_track = index_map[idx]
                mapped_render_index = mapped_track.get("track_render_index", idx)
                mapped_id = mapped_track.get("id")
                if not mapped_id:
                    raise ValueError(f"音频轨道缺少 id: track_render_index={mapped_render_index}")

                audio_copy = dict(audio)
                audio_copy_tracks = dict(at)
                audio_copy_tracks["track_render_index"] = mapped_render_index
                audio_copy["tracks"] = audio_copy_tracks

                if mapped_render_index not in audio_tracks_by_index:
                    audio_tracks_by_index[mapped_render_index] = {
                        'track_info': {
                            'id': mapped_id,
                            'track_render_index': mapped_render_index
                        },
                        'segments': []
                    }
                seg = self._create_audio_segment(audio_copy, len(audio_tracks_by_index[mapped_render_index]['segments']))
                audio_tracks_by_index[mapped_render_index]['segments'].append(seg)

            for idx, track_data in audio_tracks_by_index.items():
                track_info = track_data['track_info']
                if not track_info.get('id'):
                    raise ValueError(f"音频轨道缺少 id: track_render_index={idx}")
                tracks.append(self._create_audio_track(track_info, track_data['segments']))
            
            self.log_info(f"创建完成 {len(tracks)} 个轨道")
            return [self._sort_dict_recursive(track) for track in tracks]
            
        except Exception as e:
            self.log_error(f"创建tracks失败: {e}")
            raise
    
    def _create_video_track(self, track_info: Dict[str, Any], segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建视频轨道"""
        track = TrackModel(
            id=track_info.get('id', self.get_random_id()),
            segments=segments,
            track_type="video"
        )
        return track.to_dict()
    
    def _create_text_track(self, track_info: Dict[str, Any], segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建文字轨道"""
        track = TrackModel(
            id=track_info.get('id', self.get_random_id()),
            segments=segments,
            track_type="text"
        )
        return track.to_dict()
    
    def _create_audio_track(self, track_info: Dict[str, Any], segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建音频轨道"""
        track = TrackModel(
            id=track_info.get('id', self.get_random_id()),
            segments=segments,
            track_type="audio"
        )
        return track.to_dict()
    
    def _create_video_segment(self, pic: Dict[str, Any], render_index: int, canvas_width: float, canvas_height: float) -> Dict[str, Any]:
        """
        创建视频segment - 基于参考草稿的完整结构
        
        Args:
            pic (Dict[str, Any]): 图片数据
            render_index (int): segment在轨道中的渲染索引
            
        Returns:
            Dict[str, Any]: 完整的segment结构
        """
        pic_tracks = pic.get('tracks', {})
        material_id = pic.get('id', '')
        start_us = int((pic_tracks.get('start', 0) or 0) * 1000000)
        duration_us = int((pic_tracks.get('duration', 0) or 0) * 1000000)
        
        # 创建完整的segment结构
        segment_id = pic_tracks.get('segments_id') or f"seg_{material_id}"
        segment_model = VideoSegmentModel()
        segment_model.apply({
            "id": segment_id,
            "material_id": material_id,
            "render_index": render_index,
            "track_render_index": pic_tracks.get('track_render_index', 0),
            "clip": {
                "alpha": 1.0,
                "flip": {"horizontal": False, "vertical": False},
                "rotation": 0.0,
                "scale": {
                    "x": self._to_scale_ratio(pic_tracks.get('scale_x', 1.0)),
                    "y": self._to_scale_ratio(pic_tracks.get('scale_y', 1.0))
                },
                "transform": {
                    "x": self._to_relative(pic_tracks.get('transform_x', 0.0), canvas_width),
                    "y": self._to_relative(pic_tracks.get('transform_y', 0.0), canvas_height)
                }
            },
            "common_keyframes": self._create_complete_keyframes(
                pic_tracks.get('common_keyframes', []), segment_id, canvas_width, canvas_height
            ),
            "extra_material_refs": [
                ref for ref in [
                    pic.get('speeds_id', ''),
                    pic.get('canvases_id', ''),
                    (pic_tracks.get('material_animations', {}) or {}).get('id', ''),
                    pic.get('sound_channel_mappings_id', ''),
                    pic.get('vocal_separations_id', '')
                ] if ref
            ],
            "source_timerange": {"duration": duration_us, "start": 0},
            "target_timerange": {"duration": duration_us, "start": start_us}
        })
        
        return segment_model.to_dict()
    
    def _create_text_segment(self, text: Dict[str, Any], render_index: int, canvas_width: float, canvas_height: float) -> Dict[str, Any]:
        """创建文字segment"""
        text_tracks = text.get('tracks', {})
        material_id = text.get('id', '')
        start_us = int((text_tracks.get('start', 0) or 0) * 1000000)
        duration_us = int((text_tracks.get('duration', 0) or 0) * 1000000)
        
        segment_id = text_tracks.get('segments_id') or f"seg_{material_id}"
        base_segment = self._create_video_segment({
            'id': material_id,
            'tracks': text_tracks
        }, render_index, canvas_width, canvas_height)
        segment_model = TextSegmentModel()
        segment_model.apply(base_segment)
        segment_model.apply({
            "id": segment_id,
            "source_timerange": {"duration": duration_us, "start": 0},
            "target_timerange": {"duration": duration_us, "start": start_us}
        })
        manims = text_tracks.get('material_animations') or {}
        anim_id = manims.get('id', '')
        segment_model.apply({"extra_material_refs": [anim_id] if anim_id else []})
        
        # 可以根据需要调整文字特定的默认值
        return segment_model.to_dict()
    
    def _create_audio_segment(self, audio: Dict[str, Any], render_index: int) -> Dict[str, Any]:
        """创建音频segment"""
        audio_tracks = audio.get('tracks', {})
        material_id = audio.get('id', '')
        start_us = int((audio_tracks.get('start', 0) or 0) * 1000000)
        duration_us = int((audio_tracks.get('segment_duration', audio.get('duration', 0)) or 0) * 1000000)
        
        segment_id = audio_tracks.get('segments_id') or f"seg_{material_id}"
        segment_model = AudioSegmentModel()
        segment_model.apply({
            "id": segment_id,
            "material_id": material_id,
            "render_index": render_index,
            "track_render_index": audio_tracks.get('track_render_index', 0),
            "extra_material_refs": [
                ref for ref in [
                    audio.get('speeds_id', ''),
                    audio.get('beats_id', ''),
                    audio.get('sound_channel_mappings_id', ''),
                    audio.get('vocal_separations_id', '')
                ] if ref
            ],
            "volume": audio_tracks.get('volume', 1.0),
            "source_timerange": {
                "duration": duration_us,
                "start": int((audio_tracks.get('source_start', 0) or 0) * 1000000)
            },
            "target_timerange": {
                "duration": duration_us,
                "start": start_us
            }
        })
        
        return segment_model.to_dict()
    
    def _create_complete_keyframes(self, param_keyframes: Dict[str, Any], segment_id: str, canvas_width: float, canvas_height: float) -> List[Dict[str, Any]]:
        """
        创建完整的关键帧结构 - 修复版本
        
        Args:
            param_keyframes (Dict[str, Any]): 参数中的关键帧数据
            material_id (str): 素材ID
            
        Returns:
            List[Dict[str, Any]]: 完整的关键帧数组
        """
        complete_keyframes = []
        
        keyframe_groups = []
        if isinstance(param_keyframes, list):
            keyframe_groups = param_keyframes
        elif isinstance(param_keyframes, dict):
            for property_type, keyframe_list in param_keyframes.items():
                keyframe_groups.append({
                    "property_type": property_type,
                    "keyframe_list": keyframe_list
                })

        for group in keyframe_groups:
            property_type = group.get("property_type", "")
            keyframe_list = group.get("keyframe_list", [])
            if not keyframe_list or not isinstance(keyframe_list, list):
                continue
            
            # 创建该类型的完整keyframe_list
            complete_keyframe_points = []
            group_id = group.get("id") or ""
            if not group_id and isinstance(keyframe_list[0], dict):
                group_id = keyframe_list[0].get('group_id') or ""
            if not group_id:
                group_id = self._stable_uuid(segment_id, property_type, "group")
            for idx, kf in enumerate(keyframe_list):
                raw_value = kf.get('values', [0.0])[0] if kf.get('values') else 0.0
                if property_type == 'KFTypePositionX':
                    values = [self._to_relative(raw_value, canvas_width)]
                elif property_type == 'KFTypePositionY':
                    values = [self._to_relative(raw_value, canvas_height)]
                elif property_type == 'KFTypeScaleX':
                    values = [self._to_scale_ratio(raw_value)]
                elif property_type == 'KFTypeScaleY':
                    values = [self._to_scale_ratio(raw_value)]
                else:
                    values = [raw_value]
                kf_id = kf.get('id') or self._stable_uuid(segment_id, property_type, idx, kf.get('time_offset'), raw_value)
                keyframe_point = {
                    # 🔑 必需字段
                    "curveType": "Line",                    # 曲线类型
                    "graphID": "",                          # 图形ID
                    "id": kf_id,                             # 关键帧点ID
                    "time_offset": self._to_microseconds(kf.get('time_offset', 0)),  # 微秒时间
                    "values": values,                       # 数组值
                    "left_control": {"x": 0.0, "y": 0.0},   # 贝塞尔控制点
                    "right_control": {"x": 0.0, "y": 0.0}
                }
                complete_keyframe_points.append(keyframe_point)
            
            # 创建完整的关键帧对象 - 注意material_id为空字符串
            complete_keyframe = {
                "id": group_id,                          # 关键帧组ID
                "property_type": property_type,            # 动画类型
                "material_id": "",                      # 🚨 重要：参考草稿中为空字符串
                "keyframe_list": complete_keyframe_points
            }
            complete_keyframes.append(complete_keyframe)
        
        return complete_keyframes
    
    def _create_extra_material_refs(self, anims: List[Dict[str, Any]]) -> List[str]:
        """
        创建额外的材料引用 - 修复版本
        
        Args:
            anims (List[Dict[str, Any]]): 动画列表
            
        Returns:
            List[str]: 直接的UUID字符串数组
        """
        extra_refs = []
        for anim in anims:
            anim_id = anim.get('id', '')
            if anim_id:
                extra_refs.append(anim_id)  # 🚨 直接使用UUID，不加前缀
        return extra_refs


def main():
    """测试函数"""
    # 测试数据
    test_data = {
        'pics': [
            {
                'id': 'TEST-PIC-ID',
                'tracks': {
                    'track_render_index': 0,
                    'scale_x': 1.0,
                    'scale_y': 1.0,
                    'transform_x': -0.378072,
                    'transform_y': 0.0,
                    'start': 2.333,
                    'duration': 5.0,
                    'common_keyframes': {
                        'KFTypePositionX': [{'time_offset': 1.133333, 'values': [0.0]}],
                        'KFTypePositionY': [{'time_offset': 1.133333, 'values': [0.0]}],
                        'KFTypeScaleX': [{'time_offset': 1.133333, 'values': [1.0]}]
                    },
                    'anims': [{'id': 'TEST-ANIM-ID'}]
                }
            }
        ],
        'tracks': {
            'video_track': [{'track_render_index': 0}]
        }
    }
    
    builder = CompleteTracksBuilderFixed()
    tracks = builder.create_complete_tracks(test_data)
    
    import json
    print(json.dumps(tracks, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
