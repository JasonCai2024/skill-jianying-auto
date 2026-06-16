"""
剪映草稿反向解析器
从已生成的剪映草稿文件夹反向解析出draft_para_collect.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DraftParser:
    """剪映草稿反向解析器"""
    
    def __init__(self, draft_folder_path: str):
        """
        初始化解析器
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
        """
        self.draft_folder_path = Path(draft_folder_path)
        self.draft_content_path = self.draft_folder_path / "draft_content.json"
        self.draft_meta_info_path = self.draft_folder_path / "draft_meta_info.json"
        
        # 验证文件存在性
        self._validate_files()
        
        # 存储解析的中间数据
        self.canvas_id = None
        self.tracks_info = {}
        
    def _validate_files(self) -> None:
        """验证必要文件是否存在"""
        if not self.draft_folder_path.exists():
            raise FileNotFoundError(f"草稿文件夹不存在: {self.draft_folder_path}")
            
        if not self.draft_content_path.exists():
            raise FileNotFoundError(f"draft_content.json不存在: {self.draft_content_path}")
            
        if not self.draft_meta_info_path.exists():
            raise FileNotFoundError(f"draft_meta_info.json不存在: {self.draft_meta_info_path}")
    
    def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """读取JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            raise ValueError(f"读取文件失败 {file_path}: {e}")

    def _normalize_path(self, value: str) -> str:
        return (value or "").replace("\\", "/")

    def _extract_jianying_folder_path(self, draft_content: Dict[str, Any]) -> str:
        materials = draft_content.get("materials", {}) or {}
        texts = materials.get("texts", []) or []
        for text in texts:
            font_path = text.get("font_path", "") or ""
            if not font_path:
                fonts_list = text.get("fonts", []) or []
                if fonts_list:
                    font_path = fonts_list[0].get("path", "") or ""
            if not font_path:
                content_raw = text.get("content", "")
                try:
                    content_obj = json.loads(content_raw) if isinstance(content_raw, str) else content_raw
                except json.JSONDecodeError:
                    content_obj = {}
                font_path = (
                    content_obj.get("styles", [{}])[0]
                    .get("font", {})
                    .get("path", "")
                    or ""
                )
            font_path = self._normalize_path(font_path)
            marker = "/Resources/Font/"
            if marker in font_path:
                prefix = font_path.split(marker)[0]
                if prefix and not prefix.endswith("/"):
                    prefix = f"{prefix}/"
                return prefix
        return ""
    
    def parse_draft_content(self) -> Dict[str, Any]:
        """
        解析draft_content.json为draft_para_collect格式
        
        Returns:
            Dict: 解析后的draft_para_collect结构
        """
        try:
            logger.info(f"开始解析草稿文件夹: {self.draft_folder_path}")
            
            # 读取draft_content.json
            draft_content = self._read_json_file(self.draft_content_path)
            
            # 初始化结果结构
            draft_para_collect = {
                "canvas": {},
                "videos": [],
                "texts": [],
                "audios": [],
                "tracks": {}
            }
            
            # 逐层解析
            draft_meta_info = self._read_json_file(self.draft_meta_info_path)
            draft_para_collect["canvas"] = self.extract_canvas_info(draft_content, draft_meta_info)
            # 先提取轨道信息（建立track_id_mapping）
            draft_para_collect["tracks"] = self.extract_tracks_info(draft_content)
            draft_para_collect["videos"] = self.extract_pics_info(draft_content)
            draft_para_collect["texts"] = self.extract_texts_info(draft_content)
            draft_para_collect["audios"] = self.extract_audio_info(draft_content)
            
            logger.info("草稿解析完成")
            return draft_para_collect
            
        except Exception as e:
            logger.error(f"解析草稿失败: {e}")
            raise ValueError(f"解析草稿失败: {e}")
    
    def extract_canvas_info(self, draft_content: Dict, draft_meta_info: Dict) -> Dict[str, Any]:
        """提取画布信息"""
        try:
            # 尝试两种画布信息位置
            canvas = None
            
            # 方式1: 从timeline.canvas获取（我们项目生成的格式）
            timeline = draft_content.get("timeline", {})
            canvas = timeline.get("canvas", {})
            
            # 方式2: 从canvas_config获取（其他格式）
            if not canvas:
                canvas = draft_content.get("canvas_config", {})
            
            if not canvas:
                raise ValueError("未找到画布信息")
            
            # 构建画布信息，兼容不同格式
            canvas_info = {
                "id": canvas.get("id", draft_content.get("id", "")),  # 如果canvas没有id，从draft_content获取
                "height": canvas.get("height", 1080),
                "width": canvas.get("width", 1920),
                "duration": canvas.get("duration", draft_content.get("duration", 0.0)) / 1000000.0,  # 如果canvas没有duration，从draft_content获取，微秒转秒
                "source_draft_fold_path": draft_meta_info.get("draft_fold_path", ""),
                "jianying_folder_path": self._extract_jianying_folder_path(draft_content),
                "output_parent_draft_folder_path": ""
            }
            
            # 保存canvas_id供其他方法使用
            self.canvas_id = canvas_info["id"]
            
            logger.info(f"提取画布信息成功: {canvas_info['width']}x{canvas_info['height']}")
            return canvas_info
            
        except Exception as e:
            logger.error(f"提取画布信息失败: {e}")
            raise ValueError(f"提取画布信息失败: {e}")
    
    def extract_pics_info(self, draft_content: Dict) -> List[Dict]:
        """提取图片信息"""
        try:
            # 尝试多种图片数据位置
            videos = []
            
            # 方式1: 从materials.videos获取（我们项目生成的格式）
            materials = draft_content.get("materials", {})
            videos = materials.get("videos", [])
            
            # 方式2: 从assets获取（其他格式）
            if not videos:
                assets = draft_content.get("assets", {})
                videos = assets.get("videos", [])
            
            # 方式3: 从images获取（其他格式）
            if not videos:
                videos = materials.get("images", [])
            
            # 获取tracks信息（支持多种格式）
            tracks = draft_content.get("tracks", [])
            if not tracks:
                timeline = draft_content.get("timeline", {})
                tracks = timeline.get("tracks", {})
            
            # 获取所有视频轨道（用于时间轴处理）
            video_tracks = []
            if isinstance(tracks, list) and len(tracks) > 0:
                for track in tracks:
                    if track.get("type") == "video" and "segments" in track:
                        video_tracks.append(track)
            elif isinstance(tracks, dict):
                for track_type, track_list in tracks.items():
                    for track in track_list:
                        if track.get("type") == "video" and "segments" in track:
                            video_tracks.append(track)
            
            pics = []
            for i, video in enumerate(videos):
                # 从segments中提取时间信息
                start_time = 0.0
                duration = video.get("duration", 0) / 1000000.0  # 默认时长
                
                if video_tracks:
                    # 在所有视频轨道中查找对应的segment
                    video_id = video.get("id")
                    found_segment = False
                    
                    for track in video_tracks:
                        for segment in track.get("segments", []):
                            if segment.get("material_id") == video_id:
                                # 从target_timerange获取时间信息
                                target_timerange = segment.get("target_timerange", {})
                                start_time = target_timerange.get("start", 0) / 1000000.0  # 微秒转秒
                                segment_duration = target_timerange.get("duration", 0) / 1000000.0  # 微秒转秒
                                if segment_duration > 0:
                                    duration = segment_duration
                                
                                # 从clip中提取变换信息
                                clip = segment.get("clip", {})
                                scale_info = clip.get("scale", {"x": 1.0, "y": 1.0})
                                transform_info = clip.get("transform", {"x": 0.0, "y": 0.0})
                                
                                scale_x = round(scale_info.get("x", 1.0), 6)
                                scale_y = round(scale_info.get("y", 1.0), 6)
                                # transform值需要转换为绝对像素值（与关键帧转换逻辑一致）
                                transform_x_raw = transform_info.get("x", 0.0)
                                transform_y_raw = transform_info.get("y", 0.0)
                                canvas = draft_content.get('canvas', {})
                                canvas_width = canvas.get('width', 1920)
                                canvas_height = canvas.get('height', 1080)
                                transform_x = round(transform_x_raw * canvas_width) if transform_x_raw != 0 else 0
                                transform_y = round(transform_y_raw * canvas_height) if transform_y_raw != 0 else 0
                                found_segment = True
                                break
                        if found_segment:
                            break
                
                track_render_index = self._get_track_render_index(draft_content, video.get("id"))
                track_id = self._get_track_id_by_material_id(draft_content, video.get("id"))
                
                pic_item = {
                    "id": video.get("id", ""),
                    # "canvases_id": self.canvas_id or "",  # 移除不必要的canvases_id字段
                    "material_name": video.get("name", video.get("material_name", "")),  # 修复material_name缺失
                    "path": self._normalize_path(video.get("path", "")),
                    "width": video.get("width", 0),
                    "height": video.get("height", 0),
                    "tracks": {
                        "id": track_id or video.get("id", ""),  # 确保轨道ID正确设置
                        "render_index": 0,  # 添加render_index字段
                        "track_render_index": track_render_index,  # 获取实际的轨道索引
                        "segments_id": "",  # 添加segments_id字段
                        "scale_x": scale_x,  # 使用真实的缩放值
                        "scale_y": scale_y,  # 使用真实的缩放值
                        "transform_x": transform_x,  # 使用真实的平移值（已经是绝对像素）
                        "transform_y": transform_y,  # 使用真实的平移值（已经是绝对像素）
                        "start": start_time,  # 使用segment中的开始时间
                        "duration": duration,  # 使用segment中的时长
                        "common_keyframes": []
                    }
                }
                pics.append(pic_item)
            
            # 为每个图片填充tracks.id、segments_id和关键帧信息
            for pic in pics:
                pic_id = pic.get('id')
                
                # 1. 填充track_id（如果存在映射关系）
                if hasattr(self, 'track_id_mapping'):
                    track_render_index = pic.get('tracks', {}).get('track_render_index', 0)
                    track_id = self.track_id_mapping.get(track_render_index, "")
                    pic['tracks']['id'] = track_id
                
                # 2. 查找对应的segment并提取关键帧信息（独立于track_id_mapping）
                tracks = draft_content.get('tracks', [])
                found_segment = False
                
                for track in tracks:
                    if track.get('type') == 'video':
                        for segment in track.get('segments', []):
                            if segment.get('material_id') == pic_id:
                                found_segment = True
                                pic['tracks']['segments_id'] = segment.get('id', '')
                                
                                # 提取关键帧数据（支持common_keyframes和material_animations）
                                keyframes_dict = []
                                material_animations_dict = []
                                
                                # 获取画布尺寸用于数值转换
                                canvas = draft_content.get('canvas', {})
                                canvas_width = canvas.get('width', 1920)
                                canvas_height = canvas.get('height', 1080)
                                
                                # 1. 首先尝试提取common_keyframes（图片3的方式）
                                common_keyframes = segment.get('common_keyframes', [])
                                if common_keyframes:
                                    for keyframe_group in common_keyframes:
                                        property_type = keyframe_group.get('property_type', '')
                                        keyframe_list = keyframe_group.get('keyframe_list', [])
                                        group_id = keyframe_group.get('id', '')
                                        
                                        # 转换keyframe_list为原始项目格式
                                        if keyframe_list:
                                            keyframe_list_out = []
                                            for keyframe in keyframe_list:
                                                original_values = keyframe.get('values', [])
                                                converted_values = []
                                                
                                                # 根据属性类型转换数值
                                                for value in original_values:
                                                    if property_type == 'KFTypePositionX':
                                                        # X位置：相对值转换为绝对像素
                                                        converted_values.append(round(value * canvas_width))
                                                    elif property_type == 'KFTypePositionY':
                                                        # Y位置：相对值转换为绝对像素
                                                        converted_values.append(round(value * canvas_height))
                                                    elif property_type == 'KFTypeScaleX':
                                                        # 缩放：相对值转换为百分比
                                                        converted_values.append(round(value * 100, 1))
                                                    elif property_type == 'KFTypeScaleY':
                                                        # 缩放Y轴：相对值转换为百分比
                                                        converted_values.append(round(value * 100, 1))
                                                    elif property_type == 'KFTypeRotation':
                                                        # 旋转：保持原值（度数）
                                                        converted_values.append(round(value, 6))
                                                    else:
                                                        # 其他类型保持原值
                                                        converted_values.append(value)
                                                
                                                keyframe_data = {
                                                    "id": keyframe.get('id', ''),
                                                    "time_offset": keyframe.get('time_offset', 0) / 1000000.0,  # 微秒转秒
                                                    "values": converted_values
                                                }
                                                keyframe_list_out.append(keyframe_data)
                                            keyframes_dict.append({
                                                "property_type": property_type,
                                                "id": group_id,
                                                "keyframe_list": keyframe_list_out
                                            })
                                
                                # 2. 始终尝试从material_animations中提取动画效果（支持同时有关键帧和动画的情况）
                                extra_material_refs = segment.get('extra_material_refs', [])
                                matched_anim_id = ""
                                for ref_id in extra_material_refs:
                                    # 在material_animations中查找对应的动画
                                    material_animations = draft_content.get('materials', {}).get('material_animations', [])
                                    
                                    for material_anim in material_animations:
                                        if material_anim.get('id') == ref_id:
                                            matched_anim_id = ref_id
                                            animations = material_anim.get('animations', [])
                                            
                                            for animation in animations:
                                                # 提取动画参数
                                                start_orig = animation.get('start', 0)
                                                duration_orig = animation.get('duration', 0)
                                                category_name = animation.get('category_name', '')
                                                anim_name = animation.get('name', '')
                                                anim_type = animation.get('type', '')
                                                
                                                # 转换时间单位为秒（start和duration都是微秒，需要统一转换）
                                                start_seconds = float(start_orig) / 1000000.0  # start也是微秒，需要转换为秒
                                                duration_seconds = float(duration_orig) / 1000000.0  # duration是微秒，需要转换为秒
                                                
                                                # 创建动画效果记录（按照原始项目格式）
                                                animation_effect = {
                                                    "type": anim_type,
                                                    "name": anim_name,
                                                    "start": round(start_seconds, 3),  # 转换为秒，保留3位小数
                                                    "duration": round(duration_seconds, 3)  # 转换为秒，保留3位小数
                                                }
                                                
                                                # 添加到material_animations数组
                                                material_animations_dict.append(animation_effect)
                                
                                # 分别存储关键帧和动画效果
                                pic['tracks']['common_keyframes'] = keyframes_dict
                                if material_animations_dict and matched_anim_id:
                                    pic['tracks']['material_animations'] = {
                                        "id": matched_anim_id,  # 添加引用的动画ID
                                        "animations": material_animations_dict
                                    }
                                break
                        if found_segment:
                            break
              
            logger.info(f"提取图片信息成功: {len(pics)}个图片")
            return pics
            
        except Exception as e:
            logger.error(f"提取图片信息失败: {e}")
            raise ValueError(f"提取图片信息失败: {e}")
    
    def extract_texts_info(self, draft_content: Dict) -> List[Dict]:
        """提取文字信息"""
        try:
            materials = draft_content.get("materials", {})
            texts = materials.get("texts", [])
            
            # tracks是列表，不是字典
            tracks_list = draft_content.get("tracks", [])
            
            # 获取画布尺寸用于坐标转换
            canvas_config = draft_content.get("canvas_config", {})
            canvas_width = canvas_config.get("width", 1920)
            canvas_height = canvas_config.get("height", 1080)
            
            text_list = []
            for text in texts:
                text_id = text.get("id", "")
                
                # 解析文字内容（可能包含JSON格式的样式信息）
                content_str = text.get("content", "")
                text_display = content_str
                try:
                    # 尝试解析JSON格式的文字内容
                    import json
                    content_data = json.loads(content_str)
                    if isinstance(content_data, dict) and "text" in content_data:
                        text_display = content_data["text"]
                    else:
                        text_display = content_str
                except:
                    text_display = content_str
                
                # 提取文字样式信息
                text_color = text.get("color", "#FFFFFF")
                
                # 尝试从content中解析描边信息
                border_color = "black"
                border_width = 0.0
                try:
                    import json
                    content_data = json.loads(content_str)
                    if isinstance(content_data, dict) and "styles" in content_data:
                        styles = content_data["styles"]
                        if isinstance(styles, list) and len(styles) > 0:
                            first_style = styles[0]
                            if "strokes" in first_style and isinstance(first_style["strokes"], list):
                                stroke_info = first_style["strokes"][0]  # 取第一个描边
                                if "content" in stroke_info and "solid" in stroke_info["content"]:
                                    color_values = stroke_info["content"]["solid"]["color"]
                                    if isinstance(color_values, list) and len(color_values) >= 3:
                                        # 转换RGB值到十六进制颜色
                                        r, g, b = [int(c * 255) for c in color_values]
                                        border_color = f"#{r:02X}{g:02X}{b:02X}"
                                
                                if "width" in stroke_info:
                                    # border_width转换关系：原值*500（根据合成逻辑反推）
                                    # 合成时：converted_border_width = original_border_width / 500
                                    # 解析时：original_border_width = converted_border_width * 500
                                    border_width_raw = stroke_info["width"]
                                    border_width = float(border_width_raw) * 500 if border_width_raw != 0 else 0  # 保持原始精度，不进行float转换
                except:
                    pass
                
                # 从tracks中查找对应的segment信息
                segment_info = self._find_text_segment_by_material_id(tracks_list, text_id)
                
                # 处理关键帧数据，转换为显示值，使用与图片相同的字典格式
                keyframes_dict = []
                if segment_info:
                    common_keyframes = segment_info.get('common_keyframes', [])
                    
                    for kf_group in common_keyframes:
                        property_type = kf_group.get('property_type', '')
                        keyframe_list = kf_group.get('keyframe_list', [])
                        group_id = kf_group.get('id', '')
                        
                        # 转换keyframe_list为原始项目格式，与图片关键帧保持一致
                        if keyframe_list:
                            keyframe_list_out = []
                            for keyframe in keyframe_list:
                                time_offset_micros = keyframe.get('time_offset', 0)
                                time_offset_seconds = time_offset_micros / 1000000.0  # 转换为秒
                                original_values = keyframe.get('values', [])
                                converted_values = []
                                
                                # 根据属性类型转换数值
                                for value in original_values:
                                    if property_type == 'KFTypePositionX':
                                        # X位置：相对值转换为绝对像素
                                        converted_values.append(round(value * canvas_width))
                                    elif property_type == 'KFTypePositionY':
                                        # Y位置：相对值转换为绝对像素
                                        converted_values.append(round(value * canvas_height))
                                    elif property_type == 'KFTypeScaleX':
                                        # 缩放：相对值转换为百分比
                                        converted_values.append(round(value * 100, 1))
                                    elif property_type == 'KFTypeScaleY':
                                        # 缩放Y轴：相对值转换为百分比
                                        converted_values.append(round(value * 100, 1))
                                    elif property_type == 'KFTypeRotation':
                                        # 旋转：保持原值（度数）
                                        converted_values.append(round(value, 6))
                                    else:
                                        # 其他类型保持原值
                                        converted_values.append(value)
                                
                                keyframe_data = {
                                    "id": keyframe.get('id', ''),
                                    "time_offset": time_offset_seconds,  # 使用秒为单位
                                    "values": converted_values  # 使用转换后的显示值
                                }
                                keyframe_list_out.append(keyframe_data)
                            keyframes_dict.append({
                                "property_type": property_type,
                                "id": group_id,
                                "keyframe_list": keyframe_list_out
                            })
                
                # 默认值
                transform_x = 0.0
                transform_y = 0.0
                scale_x = 1.0
                scale_y = 1.0
                start = 0.0
                duration = 5.0
                track_render_index = 2
                track_id = text.get("track_id", "")
                font_path = (text.get("font_path", "") or
                             text.get("font_name", "") or
                             text.get("name", ""))
                font_resource_id = text.get("font_resource_id", "")
                fonts_title = ""
                fonts_list = text.get("fonts", []) or []
                if fonts_list and isinstance(fonts_list, list):
                    fonts_title = fonts_list[0].get("title", "") or ""
                    if not font_resource_id:
                        font_resource_id = fonts_list[0].get("resource_id", "") or fonts_list[0].get("effect_id", "")

                if not font_resource_id:
                    content_str = text.get("content")
                    if isinstance(content_str, str):
                        try:
                            import json as _json
                            content_obj = _json.loads(content_str)
                            styles = content_obj.get("styles", []) if isinstance(content_obj, dict) else []
                            if styles:
                                font_obj = styles[0].get("font", {}) or {}
                                font_resource_id = font_obj.get("id", "") or font_resource_id
                        except Exception:
                            pass
                
                if segment_info:
                    # 从segment的clip中获取位置信息
                    clip = segment_info.get("clip", {})
                    clip_transform = clip.get("transform", {})
                    clip_scale = clip.get("scale", {})
                    
                    # 获取位置（相对坐标，需要转换为绝对坐标）
                    relative_x = clip_transform.get("x", 0.0)
                    relative_y = clip_transform.get("y", 0.0)
                    transform_x = relative_x * canvas_width
                    transform_y = relative_y * canvas_height
                    
                    # 获取缩放
                    scale_x = clip_scale.get("x", 1.0)
                    scale_y = clip_scale.get("y", 1.0)
                    
                    # 获取时间信息（微秒转秒），安全检查
                    source_timerange = segment_info.get("source_timerange", {})
                    target_timerange = segment_info.get("target_timerange", {})
                    
                    if source_timerange:
                        start = source_timerange.get("start", 0) / 1000000.0
                    else:
                        start = 0.0
                        
                    if target_timerange:
                        duration = target_timerange.get("duration", 5000000) / 1000000.0
                    else:
                        duration = 5.0
                    
                    # 获取轨道索引和ID
                    track_render_index = segment_info.get("track_render_index", 2)
                    track_id = segment_info.get("track_id", track_id)
                    
                    # 修复font_path缺失，尝试多个字段
                    font_path = (text.get("font_path", "") or
                                 text.get("font_name", "") or
                                 text.get("name", "") or
                                 font_path)
                
                text_item = {
                    "id": text_id,
                    "content": text_display,
                    "text_color": text_color,
                    "border_color": border_color,
                    "border_width": border_width,
                    "font_size": text.get("font_size", 24),
                    "font_path": self._normalize_path(font_path),
                    "font_resource_id": font_resource_id,
                    "fonts_title": fonts_title,
                    # "canvases_id": self.canvas_id or "",  # 移除不必要的canvases_id字段
                    "tracks": {
                        "id": track_id or video.get("id", ""),  # 确保轨道ID正确设置
                        "track_render_index": track_render_index,
                        "transform_x": float(transform_x),
                        "transform_y": float(transform_y),
                        "scale_x": float(scale_x),
                        "scale_y": float(scale_y),
                        "start": float(start),
                        "duration": float(duration),
                        "text_alpha": 1.0,
                    "common_keyframes": keyframes_dict,  # 使用与图片一致的列表格式
                        "material_animations": {}  # 初始化为空
                    }
                }
                
                # 2. 提取文字的动画效果（与图片相同的处理逻辑）
                extra_material_refs = segment_info.get('extra_material_refs', [])
                material_animations_dict = []
                
                for ref_id in extra_material_refs:
                    # 在material_animations中查找对应的动画
                    material_animations = draft_content.get('materials', {}).get('material_animations', [])
                    
                    for material_anim in material_animations:
                        if material_anim.get('id') == ref_id:
                            animations = material_anim.get('animations', [])
                            
                            for animation in animations:
                                # 提取动画参数
                                start_orig = animation.get('start', 0)
                                duration_orig = animation.get('duration', 0)
                                category_name = animation.get('category_name', '')
                                anim_name = animation.get('name', '')
                                anim_type = animation.get('type', '')
                                
                                # 转换时间单位为秒
                                start_seconds = float(start_orig)  # start已经是秒
                                duration_seconds = float(duration_orig) / 1000000.0  # duration是微秒，需要转换为秒
                                
                                # 创建动画效果记录（按照原始项目格式）
                                animation_effect = {
                                    "type": anim_type,
                                    "name": anim_name,
                                    "start": round(start_seconds, 3),  # 转换为秒，保留3位小数
                                    "duration": round(duration_seconds, 3)  # 转换为秒，保留3位小数
                                }
                                
                                # 添加到material_animations数组
                                material_animations_dict.append(animation_effect)
                
                # 更新文字的material_animations
                if material_animations_dict:
                    text_item['tracks']['material_animations'] = {
                        "id": ref_id,  # 添加引用的动画ID
                        "animations": material_animations_dict
                    }
                
                text_list.append(text_item)
            
            logger.info(f"提取文字信息成功: {len(text_list)}个文字")
            return text_list
            
        except Exception as e:
            logger.error(f"提取文字信息失败: {e}")
            raise ValueError(f"提取文字信息失败: {e}")
    
    def _find_text_segment_by_material_id(self, tracks_list: List[Dict], material_id: str) -> Dict[str, Any]:
        """根据material_id查找对应的文字segment信息"""
        for track in tracks_list:
            if track.get("type") == "text":
                segments = track.get("segments", [])
                for segment in segments:
                    if segment.get("material_id") == material_id:
                        # 添加track信息到返回结果中
                        segment["track_id"] = track.get("id", "")
                        segment["track_render_index"] = tracks_list.index(track)
                        return segment
        return {}
    
    def extract_audio_info(self, draft_content: Dict) -> Dict[str, List[Dict]]:
        """提取音频信息"""
        try:
            # 从draft_content中提取音频信息（按照原始项目结构）
            materials = draft_content.get("materials", {})
            audios_data = materials.get("audios", [])
            
            audio_info = []
            
            # 建立Material ID到轨道信息的映射
            audio_track_mapping = {}
            tracks = draft_content.get("tracks", [])
            
            audio_track_index = 0  # 为音频轨道单独计数索引
            for track in tracks:
                if track.get("type") == "audio":
                    track_id = track.get("id", "")
                    track_id = track.get("id", "")
                    segments = track.get("segments", [])
                    
                    for segment in segments:
                        material_id = segment.get("material_id", "")
                        if material_id:
                            start_time = segment.get("target_timerange", {}).get("start", 0) / 1000000.0
                            duration_time = segment.get("target_timerange", {}).get("duration", 0) / 1000000.0
                            
                            audio_track_mapping[material_id] = {
                                "track_render_index": audio_track_index,
                                "id": track_id,
                                "segments_id": segment.get("id", ""),
                                "start": start_time,
                                "duration": duration_time
                            }
                    audio_track_index += 1  # 在轨道级别增加音频轨道索引
            
            for audio in audios_data:
                audio_id = audio.get("id", "")
                
                # 获取轨道信息
                track_info = audio_track_mapping.get(audio_id, {
                    "track_render_index": 0,
                    "id": audio.get("id", ""),
                    "segments_id": "",
                    "start": 0.0,
                    "duration": 0.0
                })
                
                audio_item = {
                    "id": audio_id,
                    "name": audio.get("name", ""),
                    "path": self._normalize_path(audio.get("path", "")),
                    "duration": audio.get("duration", 0) / 1000000.0,  # 微秒转秒
                    "tracks": {
                        "volume": audio.get("volume", 1.0),
                        "start": track_info["start"],  # 使用轨道上的实际开始时间
                        "track_render_index": track_info["track_render_index"],
                        "id": track_info.get("id", audio.get("id", "")),
                        "segments_id": track_info.get("segments_id", ""),
                        "segment_duration": track_info["duration"]  # 轨道上的片段持续时间
                    }
                }
                
                # 直接添加到音频数组，移除sound层级
                audio_info.append(audio_item)
            
            total_audios = len(audio_info)
            logger.info(f"提取音频信息成功: {total_audios}个音频")
            return audio_info
            
        except Exception as e:
            logger.error(f"提取音频信息失败: {e}")
            raise ValueError(f"提取音频信息失败: {e}")
    
    def _get_track_render_index(self, draft_content: Dict, material_id: str) -> int:
        """获取指定material_id对应的track_render_index"""
        try:
            tracks = draft_content.get("tracks", [])
            if not tracks:
                return 0
                
            # 查找包含该material_id的track
            for i, track in enumerate(tracks):
                if track.get("type") == "video":
                    for segment in track.get("segments", []):
                        if segment.get("material_id") == material_id:
                            return i  # 返回track在tracks列表中的索引
            return 0
        except Exception as e:
            logger.warning(f"获取track_render_index失败: {e}")
            return 0
    
    def _get_track_id_by_material_id(self, draft_content: Dict, material_id: str) -> str:
        """获取指定material_id对应的track_id"""
        try:
            tracks = draft_content.get("tracks", [])
            if not tracks:
                return ""
                
            # 查找包含该material_id的track
            for track in tracks:
                track_type = track.get("type", "")
                # 根据素材类型查找对应轨道
                target_type = ""
                if track_type == "video":
                    target_type = "video"
                elif track_type == "text":
                    target_type = "text" 
                elif track_type == "audio":
                    target_type = "audio"
                
                for segment in track.get("segments", []):
                    if segment.get("material_id") == material_id:
                        return track.get("id", "")
            return ""
        except Exception as e:
            logger.warning(f"获取track_id失败: {e}")
            return ""
    
    def extract_tracks_info(self, draft_content: Dict) -> Dict[str, Any]:
        """提取轨道信息"""
        try:
            # 更新tracks_info结构，统一音频为sounds
            tracks_info = {"video_track": [], "texts_track": [], "audios_track": []}
            
            tracks = draft_content.get("tracks", [])
            
            if tracks:
                for track in tracks:
                    track_type = track.get("type", "")
                    track_render_index = tracks.index(track)
                    track_id = track.get("id", "")
                    segments = track.get("segments", [])
                    
                    # 只处理有segments的轨道
                    if not segments:
                        continue
                    
                    track_item = {
                        "track_render_index": track_render_index,
                        "id": track_id
                    }
                    
                    if track_type == "video":
                        # 图片轨道
                        tracks_info["video_track"].append(track_item)
                    elif track_type == "text":
                        # 文字轨道
                        tracks_info["texts_track"].append(track_item)
                    elif track_type == "audio":
                        # 音频轨道（统一为sounds）
                        tracks_info["audios_track"].append(track_item)
            
            total_tracks = (len(tracks_info['video_track']) + 
                          len(tracks_info['texts_track']) + 
                          len(tracks_info['audios_track']))
            
            logger.info(f"提取轨道信息成功: {len(tracks_info['video_track'])}个图片轨道, "
                       f"{len(tracks_info['texts_track'])}个文字轨道, "
                       f"{len(tracks_info['audios_track'])}个音频轨道, 共{total_tracks}个轨道")
            return tracks_info
            
        except Exception as e:
            logger.error(f"提取轨道信息失败: {e}")
            return {"video_track": [], "texts_track": [], "audios_track": []}
    
    def _find_track_info_by_id(self, tracks: Union[Dict, List], target_id: str) -> Dict[str, Any]:
        """根据ID查找对应的轨道信息"""
        # 支持两种tracks格式：字典格式和列表格式
        
        if isinstance(tracks, dict):
            # 字典格式：{"videos": [track1, track2], "texts": [track3, track4]}
            for track_type, track_list in tracks.items():
                for track in track_list:
                    if track.get("id") == target_id:
                        return track
        elif isinstance(tracks, list):
            # 列表格式：[track1, track2, track3, ...]
            for track in tracks:
                if track.get("id") == target_id:
                    return track
        
        return {}
    
    def save_draft_para_collect(self, output_path: str, draft_para_collect: Optional[Dict[str, Any]] = None) -> None:
        """
        保存解析结果为draft_para_collect.json
        
        Args:
            output_path: 输出文件路径
            draft_para_collect: 可选的draft_para_collect数据，如果不提供则重新解析
        """
        try:
            if draft_para_collect is None:
                draft_para_collect = self.parse_draft_content()
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(draft_para_collect, f, ensure_ascii=False, indent=2)
            
            logger.info(f"draft_para_collect.json保存成功: {output_path}")
            
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise ValueError(f"保存文件失败: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取草稿摘要信息"""
        try:
            draft_content = self._read_json_file(self.draft_content_path)
            materials = draft_content.get("materials", {})
            
            summary = {
                "草稿文件夹": str(self.draft_folder_path),
                "画布信息": draft_content.get("timeline", {}).get("canvas", {}),
                "素材统计": {
                    "图片数量": len(materials.get("videos", [])),
                    "文字数量": len(materials.get("texts", [])),
                    "音频数量": len(materials.get("audios", []))
                },
                "总时长": draft_content.get("duration", 0),
                "帧率": draft_content.get("fps", 30.0)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取摘要失败: {e}")
            return {"错误": str(e)}


# 便捷函数
def parse_draft_folder(draft_folder_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    便捷函数：解析草稿文件夹
    
    Args:
        draft_folder_path: 草稿文件夹路径
        output_path: 可选的输出路径
        
    Returns:
        Dict: 解析后的draft_para_collect
    """
    parser = DraftParser(draft_folder_path)
    draft_para_collect = parser.parse_draft_content()
    
    if output_path:
        parser.save_draft_para_collect(output_path, draft_para_collect)
    
    return draft_para_collect


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python draft_parser.py <草稿文件夹路径> [输出路径]")
        sys.exit(1)
    
    draft_folder = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = parse_draft_folder(draft_folder, output_path)
        print("解析成功！")
        print(f"图片数量: {len(result.get('videos', []))}")
        print(f"文字数量: {len(result.get('texts', []))}")
        print(f"音频数量: {len(result.get('bgms', [])) + len(result.get('voices', [])) + len(result.get('sounds', []))}")
        
    except Exception as e:
        print(f"解析失败: {e}")
        sys.exit(1)
