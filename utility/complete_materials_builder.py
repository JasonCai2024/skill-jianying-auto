#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于源草稿结构的完整materials创建器
"""

import json
import uuid
from typing import Dict, List, Any

from .models.material_models import (
    VideoMaterialModel,
    TextMaterialModel,
    AudioMaterialModel,
    SpeedMaterialModel,
    SoundChannelMappingModel,
    VocalSeparationModel,
    BeatMaterialModel,
    CanvasMaterialModel,
    AnimationGroupModel,
    AnimationModel
)
from .draft_config_utility import DraftConfigUtility

class CompleteMaterialsBuilder:
    """完整的materials结构创建器"""
    
    def __init__(self):
        self.source_template = {}
        self._animation_mapping_table = DraftConfigUtility.load_animation_map()
    
    def load_source_template(self):
        """保留为兼容方法：当前不再读取JSON模板"""
        self.source_template = {}
    
    def generate_beat_id(self) -> str:
        """
        生成beat对象的唯一ID
        使用与原项目一致的UUID4生成方法
        
        Returns:
            str: UUID格式的ID，如"D43BF249-E1A9-4c60-8DC4-D7B52B5F249D"
        """
        return str(uuid.uuid4()).upper()
    
    def create_complete_materials(self, draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        """创建完整的materials结构"""
        print("🔧 创建完整materials结构...")
        
        materials = {}
        
        # 创建所有45个字段
        field_creators = {
            # 基础字段
            "ai_translates": self._create_empty_list,
            "audio_balances": self._create_empty_list,
            "audio_effects": self._create_empty_list,
            "audio_fades": self._create_empty_list,
            "audio_track_indexes": self._create_empty_list,
            
            # 核心素材字段
            "audios": self._create_audios,
            "beats": self._create_beats,
            "canvases": self._create_canvases,
            "chromas": self._create_empty_list,
            "color_curves": self._create_empty_list,
            
            # 动画和效果
            "digital_humans": self._create_empty_list,
            "drafts": self._create_empty_list,
            "effects": self._create_empty_list,
            "flowers": self._create_empty_list,
            "green_screens": self._create_empty_list,
            "handwrites": self._create_empty_list,
            "hsl": self._create_empty_list,
            "images": self._create_empty_list,
            "log_color_wheels": self._create_empty_list,
            "loudnesses": self._create_empty_list,
            "manual_deformations": self._create_empty_list,
            "masks": self._create_empty_list,
            "material_animations": self._create_material_animations,
            "material_colors": self._create_empty_list,
            "multi_language_refs": self._create_empty_list,
            "placeholders": self._create_empty_list,
            "plugin_effects": self._create_empty_list,
            "primary_color_wheels": self._create_empty_list,
            "realtime_denoises": self._create_empty_list,
            "shapes": self._create_empty_list,
            "smart_crops": self._create_empty_list,
            "smart_relights": self._create_empty_list,
            
            # 音频和视频处理
            "sound_channel_mappings": self._create_sound_channel_mappings,
            "speeds": self._create_speeds,
            "stickers": self._create_empty_list,
            "tail_leaders": self._create_empty_list,
            "text_templates": self._create_empty_list,
            "texts": self._create_texts,
            "time_marks": self._create_empty_list,
            "transitions": self._create_empty_list,
            "video_effects": self._create_empty_list,
            "video_trackings": self._create_empty_list,
            "videos": self._create_videos,
            "vocal_beautifys": self._create_empty_list,
            "vocal_separations": self._create_vocal_separations
        }
        
        # 逐个创建字段
        for field_name, creator in field_creators.items():
            try:
                materials[field_name] = creator(draft_para_collect)
                print(f"  ✅ {field_name}: 创建成功")
            except Exception as e:
                print(f"  ❌ {field_name}: 创建失败 - {e}")
                materials[field_name] = []
        
        print(f"📦 materials结构创建完成，共{len(materials)}个字段")
        return materials
    
    def _create_empty_list(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建空列表"""
        return []
    
    def _get_input_audios(self, draft_para_collect: Dict[str, Any]) -> List:
        audios = draft_para_collect.get('audios', []) or []
        if audios:
            return audios
        legacy = []
        for key in ('bgms', 'voices', 'sounds'):
            legacy.extend(draft_para_collect.get(key, []) or [])
        return legacy

    def _get_input_videos(self, draft_para_collect: Dict[str, Any]) -> List:
        return draft_para_collect.get('videos', []) or []

    def _create_audios(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建音频素材，数量与输入audios一致"""
        source_audios = []
        input_audios = self._get_input_audios(draft_para_collect)
        if not input_audios:
            return []

        audio_map = DraftConfigUtility.load_audio_name_map()
        audios = []
        for i, input_audio in enumerate(input_audios):
            audio_name = (input_audio.get("name") or "").lower()
            mapped = audio_map.get(audio_name) if audio_name else None
            resolved_path = input_audio.get("path", "")
            resolved_duration = input_audio.get("duration")
            if mapped:
                if mapped.get("path"):
                    resolved_path = mapped.get("path")
                if mapped.get("duration") is not None:
                    resolved_duration = mapped.get("duration")

            template = source_audios[i % len(source_audios)].copy() if source_audios else {}
            audio_model = AudioMaterialModel.from_template(template)
            audio_model.apply({
                "id": input_audio.get('id', template.get('id', '')),
                "name": input_audio.get("name", ""),
                "path": resolved_path,
                "duration": resolved_duration
            })
            audios.append(audio_model.to_dict())
        return audios
        
    def _create_beats(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建beats结构，生成随机ID"""
        # 使用参考草稿的固定值模板，按字母排序字段
        template_beat = {
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
            "id": "placeholder",  # ID将在循环中被替换
            "mode": "404",
            "type": "beats",
            "user_beats": [],
            "user_delete_ai_beats": None
        }
        
        input_audios = self._get_input_audios(draft_para_collect)
        beats_count = len(input_audios)
        beats = []
        for i in range(beats_count):
            beat_model = BeatMaterialModel.from_template(template_beat)
            beat_model.apply({"id": self.generate_beat_id()})
            beats.append(beat_model.to_dict())
        
        return beats
    
    def _create_canvases(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建canvases结构，按视频数量生成并建立一一对应关系"""
        source_canvases = []
        input_videos = self._get_input_videos(draft_para_collect)
        canvas_info = draft_para_collect.get('canvas', {})
        input_canvas_id = canvas_info.get('id', '')

        count = len(input_videos)
        if count <= 0:
            return []

        canvases = []
        for i in range(count):
            canvas_model = CanvasMaterialModel()
            video = input_videos[i]
            video_canvas_id = video.get('canvases_id', '')
            if video_canvas_id:
                canvas_model.apply({'id': video_canvas_id})
            elif input_canvas_id:
                canvas_model.apply({'id': input_canvas_id})
            else:
                canvas_model.apply({'id': 'XXXYYYZZZ'})
            canvases.append(canvas_model.to_dict())

        return canvases
    
    def _create_material_animations(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建material_animations结构"""
        input_animations = []
        
        # 1. 从videos中提取material_animations
        for pic in draft_para_collect.get('videos', []):
            if 'tracks' in pic and 'material_animations' in pic['tracks']:
                material_animations = pic['tracks']['material_animations']
                if isinstance(material_animations, dict):
                    anim_group = material_animations.copy()
                    anim_group['source_type'] = 'picture'
                    input_animations.append(anim_group)
        
        # 2. 从texts中提取material_animations
        for text in draft_para_collect.get('texts', []):
            if 'tracks' in text and 'material_animations' in text['tracks']:
                material_animations = text['tracks']['material_animations']
                if isinstance(material_animations, dict):
                    anim_group = material_animations.copy()
                    anim_group['source_type'] = 'text'
                    input_animations.append(anim_group)
        
        # 3. 构建完整的material_animations结构
        output_animations = []
        
        for anim_group in input_animations:
            material_type = 'video' if anim_group['source_type'] == 'picture' else 'sticker'
            material_type = 'video' if anim_group['source_type'] == 'picture' else 'sticker'
            
            # 构建完整的动画数组
            completed_animations = []
            for animation in anim_group['animations']:
                completed_anim = self._complete_animation_fields(animation, material_type)
                anim_model = AnimationModel.from_template(completed_anim)
                completed_animations.append(anim_model.to_dict())
            
            # 确定最终ID
            final_id = self._determine_animation_id(anim_group, anim_group['source_type'])
            
            # 构建最终的material_animations元素
            group_model = AnimationGroupModel()
            group_model.apply({
                "animations": completed_animations,
                "id": final_id
            })
            
            output_animations.append(group_model.to_dict())
        
        return output_animations
    
    def _get_animation_mapping(self, material_type: str, category_id: str, name: str) -> Dict[str, Any]:
        """根据动画属性获取映射信息"""
        for mapping in self._animation_mapping_table:
            if (mapping["material_type"] == material_type and 
                mapping["category_id"] == category_id and 
                mapping["name"] == name):
                return mapping
        return None
    
    def _extract_id_from_path(self, path: str) -> str:
        """从路径中提取ID"""
        # 路径格式: C:/Users/pc/AppData/Local/JianyingPro/User Data/Cache/effect/{id}/{hash}
        import re
        match = re.search(r'/effect/([^/]+)/', path)
        if match:
            return match.group(1)
        return None
    
    def _generate_animation_path(self, material_type: str, category_id: str, name: str) -> str:
        """生成动画路径"""
        mapping = self._get_animation_mapping(material_type, category_id, name)
        if mapping:
            return f"C:/Users/pc/AppData/Local/JianyingPro/User Data/Cache/effect/{mapping['id']}/{mapping['path_hash']}"
        return ""
    
    def _complete_animation_fields(self, animation: Dict[str, Any], material_type: str) -> Dict[str, Any]:
        """补全动画字段，按字母顺序排列"""
        # 优先使用category_id，如果没有则根据type推断
        category_id = animation.get('category_id')
        name = animation.get('name', '')
        anim_type = animation.get('type', '')
        
        if not category_id:
            # 根据type推断category_id
            if anim_type == 'in':
                category_id = 'in' if material_type == 'video' else 'ruchang'
            elif anim_type == 'out':
                category_id = 'out' if material_type == 'video' else 'chuchang'
            else:
                # 根据名称推断
                if '入' in name:
                    category_id = 'in' if material_type == 'video' else 'ruchang'
                elif '出' in name:
                    category_id = 'out' if material_type == 'video' else 'chuchang'
        
        # 确定分类名称
        category_name_map = {
            'in': '入场',
            'out': '出场', 
            'ruchang': '入场',
            'chuchang': '出场'
        }
        category_name = category_name_map.get(category_id, name)
        
        # 转换时间单位（秒转微秒）
        start = animation.get('start', 0)
        if isinstance(start, (int, float)) and start < 1000:  # 如果是秒级单位
            start = int(start * 1000000)
        else:
            start = int(start) if start else 0
            
        duration = animation.get('duration', 0)
        if isinstance(duration, (int, float)) and duration < 10000:  # 如果是秒级单位
            duration = int(duration * 1000000)
        else:
            duration = int(duration) if duration else 0
        
        # 获取映射信息（直接使用原始category_id）
        mapping = self._get_animation_mapping(material_type, category_id, name)
        
        # 确定type字段
        if category_id in ['in', 'out']:
            type_field = category_id
        else:
            type_field = 'in' if category_id == 'ruchang' else 'out'
        
        # 使用映射表获取正确的值
        if mapping:
            resource_id = mapping["resource_id"]
            animation_id = mapping["id"]
            path = f"C:/Users/pc/AppData/Local/JianyingPro/User Data/Cache/effect/{animation_id}/{mapping['path_hash']}"
        else:
            resource_id = animation.get('resource_id', '')
            animation_id = animation.get('id', '') or self._extract_id_from_path(animation.get('path', '')) or ''
            path = animation.get('path', '') or self._generate_animation_path(material_type, category_id, name)
        
        # 按字母顺序排列字段
        completed_animation = {
            'anim_adjust_params': None,
            'category_id': category_id,
            'category_name': category_name,
            'duration': duration,
            'id': animation_id,
            'material_type': material_type,
            'name': name,
            'panel': material_type if material_type == 'video' else '',
            'path': path,
            'platform': 'all',
            'request_id': '',
            'resource_id': resource_id,
            'start': start,
            'type': type_field
        }
        
        return completed_animation
    
    
    
    def _determine_animation_id(self, anim_group: Dict[str, Any], source_type: str) -> str:
        """确定动画ID"""
        input_id = anim_group.get('id', '')
        # 使用输入文件的动画ID（图片与文字一致）
        return input_id
    
    def _create_sound_channel_mappings(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建sound_channel_mappings结构，使用UUID生成ID"""
        source_mappings = []
        input_audios = self._get_input_audios(draft_para_collect)
        input_videos = self._get_input_videos(draft_para_collect)
        mappings_count = len(input_audios) + len(input_videos)
        
        if mappings_count == 0:
            return []
        
        # 使用UUID生成真实ID
        mappings = []
        for i in range(mappings_count):
            mapping_model = SoundChannelMappingModel()
            mapping_model.apply({"id": self.generate_beat_id()})
            mappings.append(mapping_model.to_dict())
        
        return mappings
    
    def _create_speeds(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建speeds结构，使用UUID生成ID"""
        source_speeds = []
        input_audios = self._get_input_audios(draft_para_collect)
        input_videos = self._get_input_videos(draft_para_collect)
        speeds_count = len(input_audios) + len(input_videos)
        
        if speeds_count == 0:
            return []
        
        # 使用UUID生成真实ID
        speeds = []
        for i in range(speeds_count):
            speed_model = SpeedMaterialModel()
            speed_model.apply({"id": self.generate_beat_id()})
            speeds.append(speed_model.to_dict())
        
        return speeds
    
    def _create_texts(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建texts结构（基于模型 + 输入参数覆盖）"""
        input_texts = draft_para_collect.get('texts', []) or []
        if not input_texts:
            return []

        def _normalize_hex(value: str, default: str) -> str:
            if not value:
                return default
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

        def _build_rich_content(text: str,
                                font_path: str,
                                font_id: str,
                                font_size: float,
                                text_color: str,
                                border_color: str,
                                border_width: float) -> str:
            fill_color = _hex_to_rgb01(text_color)
            stroke_color = _hex_to_rgb01(border_color)
            text_len = len(text or "")
            content_obj = {
                "text": text or "",
                "styles": [
                    {
                        "fill": {"content": {"solid": {"color": fill_color}}},
                        "font": {"path": font_path or "", "id": font_id or ""},
                        "strokes": [
                            {"content": {"solid": {"color": stroke_color}}, "width": border_width}
                        ],
                        "size": font_size,
                        "useLetterColor": True,
                        "range": [0, text_len]
                    }
                ]
            }
            return json.dumps(content_obj, ensure_ascii=False, separators=(',', ':'))

        font_title_map = {
            "6740435892441190919": "新青年体",
        }

        results = []
        canvas_info = draft_para_collect.get('canvas', {}) or {}
        jianying_folder_path = canvas_info.get('jianying_folder_path', '') or ''
        for input_text in input_texts:
            text_model = TextMaterialModel()

            content_text = input_text.get('content', '') or ''
            input_font_title = input_text.get('fonts_title') or input_text.get('font_title') or ''
            font_path = input_text.get('font_path', '') or ''
            font_resource_id = input_text.get('font_resource_id', '') or ''
            if input_font_title:
                mapped_font = DraftConfigUtility.resolve_font_by_title(
                    input_font_title,
                    jianying_folder_path=jianying_folder_path
                )
                if mapped_font:
                    font_path = mapped_font.get('font_path', '') or font_path
                    font_resource_id = mapped_font.get('font_resource_id', '') or font_resource_id
            font_size = input_text.get('font_size', text_model.data.get('font_size', 12.0))

            text_color = _normalize_hex(input_text.get('text_color', ''), text_model.data.get('text_color', '#ffffff'))
            border_color = _normalize_hex(input_text.get('border_color', ''), text_model.data.get('border_color', '#000000'))

            border_width_ui = input_text.get('border_width')
            if border_width_ui is None:
                border_width = text_model.data.get('border_width', 0.08)
            elif border_width_ui > 1:
                border_width = border_width_ui / 500
            else:
                border_width = border_width_ui

            text_model.apply({
                "id": input_text.get('id', text_model.data.get('id', '')),
                "font_name": "",
                "font_path": font_path,
                "font_resource_id": font_resource_id,
                "font_size": font_size,
                "text_color": text_color,
                "border_color": border_color,
                "border_width": border_width,
                "background_style": int(input_text.get('background_style', text_model.data.get('background_style', 0))),
                "background_color": _normalize_hex(input_text.get('background_color', ''), text_model.data.get('background_color', '#000000')),
                "background_width": float(input_text.get('background_width', text_model.data.get('background_width', 0.14))),
                "background_height": float(input_text.get('background_height', text_model.data.get('background_height', 0.14))),
                "background_round_radius": float(input_text.get('background_round_radius', text_model.data.get('background_round_radius', 0.0))),
                "global_alpha": float(input_text.get('global_alpha', text_model.data.get('global_alpha', 1.0))),
                "check_flag": int(input_text.get('check_flag', text_model.data.get('check_flag', 15))),
            })

            if input_text.get('tracks', {}).get('text_alpha') is not None:
                text_model.apply({"text_alpha": input_text.get('tracks', {}).get('text_alpha')})

            rich_content = _build_rich_content(
                content_text,
                font_path,
                font_resource_id,
                font_size,
                text_color,
                border_color,
                border_width
            )
            text_model.apply({"content": rich_content})

            # fonts[].title 使用输入值优先，其次使用映射
            resolved_title = input_font_title or font_title_map.get(font_resource_id, "")
            fonts_list = text_model.data.get('fonts', []) or []
            if fonts_list and isinstance(fonts_list, list):
                fonts_list[0]['title'] = resolved_title
                if font_resource_id:
                    if 'resource_id' in fonts_list[0]:
                        fonts_list[0]['resource_id'] = font_resource_id
                    if 'effect_id' in fonts_list[0]:
                        fonts_list[0]['effect_id'] = font_resource_id
                if font_path:
                    fonts_list[0]['path'] = font_path
                text_model.apply({"fonts": fonts_list})

            results.append(text_model.to_dict())

        return results
    
    def _create_videos(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建videos结构 - 完整的复合结构（参考剪映草稿标准）
        优先级：用户数据 > 模板数据 > 系统默认值
        """
        print("    🔍 DEBUG: _create_videos 被调用")
        input_videos = self._get_input_videos(draft_para_collect)
        print(f"    🔍 DEBUG: input_videos = {input_videos}")
        
        if not input_videos:
            print("    🔍 DEBUG: 没有videos数据，返回空列表")
            return []
        
        def _sort_dict_recursive(value):
            if isinstance(value, dict):
                return {k: _sort_dict_recursive(value[k]) for k in sorted(value)}
            if isinstance(value, list):
                return [_sort_dict_recursive(item) for item in value]
            return value
        results = []
        for input_pic in input_videos:
            video_model = VideoMaterialModel()
            video_model.apply({
                "id": input_pic.get('id', str(uuid.uuid4()).upper()),
                "material_name": input_pic.get('material_name', input_pic.get('name', '')),
                "path": input_pic.get('path', ''),
                "width": input_pic.get('width', 2048),
                "height": input_pic.get('height', 2048)
            })
            video_result = _sort_dict_recursive(video_model.to_dict())
            results.append(video_result)
        return results
    
    def _create_vocal_separations(self, draft_para_collect: Dict[str, Any]) -> List:
        """创建vocal_separations结构，数量与输入audios+pics一致"""
        source_vocals = []
        input_audios = self._get_input_audios(draft_para_collect)
        input_videos = self._get_input_videos(draft_para_collect)
        vocals_count = len(input_audios) + len(input_videos)

        if vocals_count == 0:
            return []

        vocals = []
        for i in range(vocals_count):
            vocal_model = VocalSeparationModel()
            vocal_model.apply({"id": self.generate_beat_id()})
            vocals.append(vocal_model.to_dict())
        return vocals

def main():
    """测试完整的materials创建"""
    print("🧪 测试完整materials结构创建...")
    
    builder = CompleteMaterialsBuilder()
    test_draft_para = {
        "canvas": {"duration": 12, "width": 1920, "height": 1080}
    }
    
    complete_materials = builder.create_complete_materials(test_draft_para)
    
    print(f"\n📊 创建结果:")
    print(f"   总字段数: {len(complete_materials)}")
    
    # 保存结果
    with open("complete_materials_test.json", 'w', encoding='utf-8') as f:
        json.dump(complete_materials, f, ensure_ascii=False, indent=2)
    
    print("✅ 完整materials结构已保存到 complete_materials_test.json")

if __name__ == "__main__":
    main()
