#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整结构创建器 - 处理config、keyframes、platform等非materials字段
"""

import json
import os
from typing import Dict, Any, List

class CompleteStructureBuilder:
    """完整结构创建器类"""
    
    def __init__(self):
        """初始化完整结构创建器"""
        self.source_template = self._load_source_template()
    
    def _load_source_template(self) -> Dict[str, Any]:
        """加载源模板结构"""
        template_path = os.path.join(os.path.dirname(__file__), 'source_materials_structure.json')
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def create_complete_config(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建完整的config结构（24个子字段）
        匹配源草稿的config字段
        """
        config = {
            "adjust_max_index": 1,
            "attachment_info": [],
            "combination_max_index": 1,
            "export_range": None,
            "extract_audio_last_index": 1,
            "lyrics_recognition_id": "",
            "lyrics_sync": True,
            "lyrics_taskinfo": [],
            "maintrack_adsorb": False,
            "material_save_mode": 0,
            "multi_language_current": "none",
            "multi_language_list": [],
            "multi_language_main": "none",
            "multi_language_mode": "none",
            "original_sound_last_index": 1,
            "record_audio_last_index": 1,
            "sticker_max_index": 1,
            "subtitle_keywords_config": None,
            "subtitle_recognition_id": "",
            "subtitle_sync": True,
            "subtitle_taskinfo": [],
            "system_font_list": [],
            "video_mute": False,
            "zoom_info_params": None
        }
        
        print("  ✅ config: 24个字段创建成功")
        return config
    
    def create_complete_keyframes(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建完整的keyframes结构（8个子字段）
        匹配源草稿的keyframes字段
        """
        keyframes = {
            "adjusts": [],
            "audios": [],
            "effects": [],
            "filters": [],
            "handwrites": [],
            "stickers": [],
            "texts": [],  # 参考草稿模板中为空
            "videos": []   # 参考草稿模板中为空
        }
        
        print("  ✅ keyframes: 8个字段创建成功")
        return keyframes
    
    def create_complete_platform(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建完整的platform结构（8个子字段）
        匹配源草稿的platform字段
        """
        platform = {
            "app_id": 3704,  # 参考草稿模板中的固定值
            "app_source": "lv",  # 参考草稿模板中的固定值
            "app_version": "5.9.0",  # 参考草稿模板中的固定值
            "device_id": "3ed8b66f5ac1c0f2cbe5644f6ec6c024",  # 参考草稿模板中的固定值
            "hard_disk_id": "dcd82461a72e6598ad89d94df6641c57",  # 参考草稿模板中的固定值
            "mac_address": "f32f89242f5557310e627241e488ea71,6349be23a2792cd8ea69df2eee0406c7",  # 参考草稿模板中的固定值
            "os": "windows",  # 参考草稿模板中的固定值
            "os_version": "10.0.19045"  # 参考草稿模板中的固定值
        }
        
        print("  ✅ platform: 8个字段创建成功")
        return platform
    
    def create_complete_last_modified_platform(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建完整的last_modified_platform结构（8个子字段）
        匹配源草稿的last_modified_platform字段
        """
        last_modified_platform = {
            "app_id": 3704,  # 参考草稿模板中的固定值
            "app_source": "lv",  # 参考草稿模板中的固定值
            "app_version": "5.9.0",  # 参考草稿模板中的固定值
            "device_id": "3ed8b66f5ac1c0f2cbe5644f6ec6c024",  # 参考草稿模板中的固定值
            "hard_disk_id": "dcd82461a72e6598ad89d94df6641c57",  # 参考草稿模板中的固定值
            "mac_address": "f32f89242f5557310e627241e488ea71,6349be23a2792cd8ea69df2eee0406c7",  # 参考草稿模板中的固定值
            "os": "windows",  # 参考草稿模板中的固定值
            "os_version": "10.0.19045"  # 参考草稿模板中的固定值
        }
        
        print("  ✅ last_modified_platform: 8个字段创建成功")
        return last_modified_platform
    
    def create_complete_tracks(self, draft_para_collect: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        创建完整的tracks结构（5个轨道，完整keyframes和segments）
        匹配源草稿的tracks字段
        """
        from .complete_tracks_builder import CompleteTracksBuilder
        
        builder = CompleteTracksBuilder()
        tracks = builder.create_complete_tracks(draft_para_collect)
        
        print(f"  ✅ 完整tracks创建成功：{len(tracks)}个轨道，总计{sum(len(track.get('segments', [])) for track in tracks)}个segments")
        return tracks
    
    def create_complete_platform(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建完整的platform结构（8个子字段）
        匹配源草稿的platform字段
        """
        from .complete_tracks_builder import CompletePlatformBuilder
        
        builder = CompletePlatformBuilder()
        platform = builder.create_complete_platform()
        
        print("  ✅ platform: 8个字段创建成功")
        return platform
    
    def create_complete_last_modified_platform(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建完整的last_modified_platform结构（8个子字段）
        匹配源草稿的last_modified_platform字段
        """
        from .complete_tracks_builder import CompletePlatformBuilder
        
        builder = CompletePlatformBuilder()
        last_modified_platform = builder.create_complete_last_modified_platform()
        
        print("  ✅ last_modified_platform: 8个字段创建成功")
        return last_modified_platform
    
    def create_missing_top_level_fields(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建缺失的顶级字段
        """
        missing_fields = {}
        
        # 添加缺失的顶级字段
        missing_fields.update({
            "mutable_config": None,
            "new_version": "110.0.0",  # 参考草稿模板中的固定值
            "relationships": [],
            "render_index_track_mode_on": True,  # 参考草稿模板中的固定值
            "retouch_cover": None,
            "source": "default",  # 参考草稿模板中的固定值
            "static_cover_image_path": "",
            "time_marks": None,
            "update_time": 0,  # 参考草稿模板中的固定值
            "version": 360000  # 参考草稿模板中的固定值
        })
        
        print(f"  ✅ 缺失顶级字段: {len(missing_fields)}个字段创建成功")
        return missing_fields
