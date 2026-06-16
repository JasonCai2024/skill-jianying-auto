"""
剪辑合成模块 (utility/draft_config_comb.py) - ext独立版本

本模块是对原项目 utility/draft_config_comb.py 的适配版本，提供剪辑草稿合成功能。
主要功能分为素材转换和草稿合成两部分：

素材转换功能：
- 图片/文字动画路径转换
- 字体名称和路径转换  
- 文字内容格式转换

草稿合成功能：
- 复制空白剪辑草稿
- 修改画布配置
- 创建和添加轨道
- 添加图片、文字、音频素材
- 添加动画效果
- 更新草稿元数据

作者: AutoCut 项目开发组
创建时间: 2024年
版本: 2.0 (ext适配版本)
"""

import os
import sys
import json
import time
import shutil
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import asdict
from datetime import datetime
import copy
import hashlib

# 导入ext版本的数据模型
try:
    from .models.draft_collect_models import (
        BaseModel, CanvasModel, PicModel, TextModel, BGMModel, VoiceModel, SoundModel,
        TrackInfoModel, MaterialAnimationModel
    )
    from .models.draft_comb_models import (
        BaseCombModel, AnimationPathModel, CanvasConfigModel, TrackModel, DraftContentModel
    )
except ImportError:
    # 如果导入失败，使用基础模型
    BaseModel = object
    BaseCombModel = object
    AnimationPathModel = object

# 导入日志模块
try:
    from logger import get_logger
except ImportError:
    import logging as std_logging
    get_logger = lambda name: std_logging.getLogger(name)

# 导入ext设置
try:
    from settings_ext import settings
except ImportError:
    # 如果没有settings_ext，使用默认设置
    class DefaultSettings:
        temp_folder = "temp"
        effect_folder = "user_data/effect"
    settings = DefaultSettings()


class DraftConfigComb:
    """
    剪辑合成主类 - ext独立版本
    
    负责将采集的剪辑参数转换为完整的剪映草稿文件。
    适配ext项目的独立运行环境。
    """
    
    def __init__(self):
        """
        初始化剪辑合成类
        """
        # 初始化日志记录器
        self.logger = get_logger(__name__)
        self.logger.info("初始化ext剪辑合成模块...")
        
        # 初始化目录路径 - 适配ext项目结构
        self._init_directories()
        
        # 初始化字体映射表
        self._init_font_mapping()
        
        self.logger.info("ext剪辑合成模块初始化完成")
    
    def _init_font_mapping(self):
        """
        初始化字体名称映射表
        建立原始字体名称到剪映字体名称的映射关系
        """
        self.font_mapping = {
            "系统": "zh-hans",
            "优设标题黑": "优设标题黑", 
            "arial": "arial",
            # 可以根据需要添加更多字体映射
        }
        self.logger.debug(f"字体映射表初始化完成，包含 {len(self.font_mapping)} 个映射")
    
    def _init_directories(self):
        """
        初始化目录路径 - 适配ext项目结构
        """
        # ext项目的基础路径
        current_file_dir = Path(__file__).parent
        base_path = current_file_dir.parent
        
        self.logger.info(f"ext项目基础路径: {base_path}")
        
        # 设置ext项目的目录路径
        self.template_dir = base_path / "user_data" / "draft_template"
        self.temp_dir = base_path / "temp" or getattr(settings, 'temp_folder', 'temp')
        self.effect_dir = base_path / "user_data" / "effect"
        self.output_dir = base_path / "output"  # 添加输出目录
        
        # 确保目录存在
        self.temp_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger.debug(f"模板目录: {self.template_dir}")
        self.logger.debug(f"临时目录: {self.temp_dir}")
        self.logger.debug(f"特效目录: {self.effect_dir}")
    
    def copy_blank_draft(self, draft_parent_folder: str) -> str:
        """
        复制空白剪辑草稿
        
        Args:
            draft_parent_folder (str): 草稿父文件夹路径
            
        Returns:
            str: 草稿文件夹路径
            
        Raises:
            FileNotFoundError: 当模板文件夹不存在时抛出
            IOError: 当文件操作失败时抛出
        """
        # 验证模板文件夹是否存在
        if not self.template_dir.exists():
            raise FileNotFoundError(f"模板文件夹不存在: {self.template_dir}")
        
        # 创建目标文件夹
        os.makedirs(draft_parent_folder, exist_ok=True)
        
        # 按时间戳生成新文件夹名称
        new_folder_name = time.strftime("%Y%m%d%H%M%S")
        new_draft_path = Path(draft_parent_folder) / new_folder_name
        
        try:
            # 复制模板文件夹
            shutil.copytree(self.template_dir, new_draft_path)
            self.logger.info(f"已复制空白草稿模板到: {new_draft_path}")
            
            return str(new_draft_path)
            
        except Exception as e:
            self.logger.error(f"复制空白草稿失败: {e}")
            raise IOError(f"复制空白草稿失败: {e}")
    
    def modify_canvas(self, draft_content: Dict[str, Any], draft_para_collect: Dict[str, Any]) -> Dict[str, Any]:
        """
        修改画布配置
        
        Args:
            draft_content (Dict[str, Any]): 草稿内容字典
            draft_para_collect (Dict[str, Any]): 采集的参数字典
            
        Returns:
            Dict[str, Any]: 修改后的草稿内容字典
            
        Raises:
            ValueError: 当参数无效时抛出
        """
        try:
            canvas_info = draft_para_collect.get("canvas", {})
            
            if not canvas_info:
                self.logger.warning("未找到画布配置信息")
                return draft_content
            
            # 修改画布配置
            if "canvas_config" in draft_content:
                canvas_config = draft_content["canvas_config"]
                
                # 修改画布尺寸
                if "height" in canvas_info:
                    canvas_config["height"] = canvas_info["height"]
                    self.logger.debug(f"画布高度已修改: {canvas_info['height']}")
                
                if "width" in canvas_info:
                    canvas_config["width"] = canvas_info["width"]
                    self.logger.debug(f"画布宽度已修改: {canvas_info['width']}")
                
                # 修改画布ID
                if "id" in canvas_info:
                    draft_content["id"] = canvas_info["id"]
                    self.logger.debug(f"画布ID已修改: {canvas_info['id']}")
                
                # 修改画布时长
                if "duration" in canvas_info:
                    duration = canvas_info["duration"]
                    # 参考草稿为微秒，输入为秒时需要转换
                    if isinstance(duration, (int, float)):
                        duration = int(duration * 1000000)
                    draft_content["duration"] = duration
                    self.logger.debug(f"画布时长已修改: {duration}")
            
            self.logger.debug("画布配置修改完成")
            return draft_content
            
        except Exception as e:
            self.logger.error(f"修改画布配置失败: {e}")
            raise ValueError(f"修改画布配置失败: {e}")
    
    # --- 动画路径转换方法 ---
    def convert_pic_in_animation(self, animation_name: str) -> AnimationPathModel:
        """
        转换图片入场动画路径
        
        Args:
            animation_name (str): 动画名称
            
        Returns:
            AnimationPathModel: 动画路径模型，包含路径和验证信息
            
        Raises:
            FileNotFoundError: 当动画文件夹不存在时抛出
            ValueError: 当动画名称为空时抛出
        """
        if not animation_name:
            raise ValueError("动画名称不能为空")
        
        animation_path = self.effect_dir / "pic_animation" / "in" / animation_name
        
        content_path = animation_path / "content.json"
        prefab_path = animation_path / "anim.prefab"
        script_path = animation_path / "Transform.lua"
        
        model = AnimationPathModel(
            animation_path=str(animation_path),
            content_path=str(content_path),
            prefab_path=str(prefab_path),
            script_path=str(script_path)
        )
        
        if not model.validate():
            raise FileNotFoundError(f"图片入场动画文件夹不存在: {animation_path}")
        
        self.logger.debug(f"图片入场动画转换成功: {animation_name} -> {animation_path}")
        return model
    
    def convert_pic_out_animation(self, animation_name: str) -> AnimationPathModel:
        """
        转换图片出场动画路径
        
        Args:
            animation_name (str): 动画名称
            
        Returns:
            AnimationPathModel: 动画路径模型，包含路径和验证信息
        """
        if not animation_name:
            raise ValueError("动画名称不能为空")
        
        animation_path = self.effect_dir / "pic_animation" / "out" / animation_name
        
        content_path = animation_path / "content.json"
        prefab_path = animation_path / "anim.prefab"
        script_path = animation_path / "Transform.lua"
        
        model = AnimationPathModel(
            animation_path=str(animation_path),
            content_path=str(content_path),
            prefab_path=str(prefab_path),
            script_path=str(script_path)
        )
        
        if not model.validate():
            raise FileNotFoundError(f"图片出场动画文件夹不存在: {animation_path}")
        
        self.logger.debug(f"图片出场动画转换成功: {animation_name} -> {animation_path}")
        return model
    
    def convert_text_in_animation(self, animation_name: str) -> AnimationPathModel:
        """
        转换文字入场动画路径
        
        Args:
            animation_name (str): 动画名称
            
        Returns:
            AnimationPathModel: 动画路径模型，包含路径和验证信息
        """
        if not animation_name:
            raise ValueError("动画名称不能为空")
        
        animation_path = self.effect_dir / "text_animation" / "in" / animation_name
        
        content_path = animation_path / "content.json"
        prefab_path = animation_path / "anim.prefab"
        script_path = animation_path / "PrinterOne.lua" if animation_name == "打字机 II" else animation_path / "Transform.lua"
        
        model = AnimationPathModel(
            animation_path=str(animation_path),
            content_path=str(content_path),
            prefab_path=str(prefab_path),
            script_path=str(script_path)
        )
        
        if not model.validate():
            raise FileNotFoundError(f"文字入场动画文件夹不存在: {animation_path}")
        
        self.logger.debug(f"文字入场动画转换成功: {animation_name} -> {animation_path}")
        return model
    
    def convert_text_out_animation(self, animation_name: str) -> AnimationPathModel:
        """
        转换文字出场动画路径
        
        Args:
            animation_name (str): 动画名称
            
        Returns:
            AnimationPathModel: 动画路径模型，包含路径和验证信息
        """
        if not animation_name:
            raise ValueError("动画名称不能为空")
        
        animation_path = self.effect_dir / "text_animation" / "out" / animation_name
        
        content_path = animation_path / "content.json"
        prefab_path = animation_path / "anim.prefab"
        script_path = animation_path / "Disappear.lua"
        
        model = AnimationPathModel(
            animation_path=str(animation_path),
            content_path=str(content_path),
            prefab_path=str(prefab_path),
            script_path=str(script_path)
        )
        
        if not model.validate():
            raise FileNotFoundError(f"文字出场动画文件夹不存在: {animation_path}")
        
        self.logger.debug(f"文字出场动画转换成功: {animation_name} -> {animation_path}")
        return model
    
    def copy_materials_to_draft(self, draft_para_collect: Dict[str, Any], draft_folder: str) -> Dict[str, Any]:
        """
        复制素材文件到草稿文件夹
        
        Args:
            draft_para_collect (Dict[str, Any]): 采集的参数字典
            draft_folder (str): 草稿文件夹路径
            
        Returns:
            Dict[str, Any]: 更新后的draft_para_collect
        """
        try:
            draft_path = Path(draft_folder)
            
            # 创建标准目录结构
            resources_dir = draft_path / "Resources" / "Local"
            images_dir = resources_dir / "images"
            audios_dir = resources_dir / "audios"
            voice_dir = audios_dir
            bgm_dir = resources_dir / "bgm"
            sound_effects_dir = resources_dir / "sound_effects"
            background_dir = resources_dir / "background"
            
            # 确保目录存在
            for dir_path in [images_dir, audios_dir, bgm_dir, sound_effects_dir, background_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            # 复制图片素材
            videos = draft_para_collect.get("videos", []) or []
            if videos:
                for pic in videos:
                    pic_path = pic.get("path", "")
                    if pic_path and os.path.exists(pic_path):
                        # 判断是否为背景图片
                        if pic.get("is_background", False):
                            dest_dir = background_dir
                        else:
                            dest_dir = images_dir
                        
                        # 复制文件
                        dest_path = dest_dir / os.path.basename(pic_path)
                        shutil.copy2(pic_path, dest_path)
                        
                        # 更新路径为相对路径
                        pic["path"] = str(dest_path.relative_to(draft_path)).replace("\\", "/")
                        self.logger.debug(f"图片已复制: {pic_path} -> {dest_path}")
            
            # 复制音频素材
            audio_types = [
                ("bgms", bgm_dir),
                ("voices", voice_dir),
                ("sounds", sound_effects_dir),
                ("audios", sound_effects_dir)
            ]
            
            for audio_type, dest_dir in audio_types:
                if audio_type in draft_para_collect:
                    for audio in draft_para_collect[audio_type]:
                        audio_path = audio.get("path", "")
                        if audio_path and os.path.exists(audio_path):
                            dest_path = dest_dir / os.path.basename(audio_path)
                            shutil.copy2(audio_path, dest_path)
                            
                            # 更新路径为相对路径
                            audio["path"] = str(dest_path.relative_to(draft_path)).replace("\\", "/")
                            self.logger.debug(f"音频已复制: {audio_path} -> {dest_path}")
            
            self.logger.info("素材文件复制完成")
            return draft_para_collect
            
        except Exception as e:
            self.logger.error(f"复制素材文件失败: {e}")
            raise ValueError(f"复制素材文件失败: {e}")
    
    def create_draft_meta_info(self, draft_folder: Path, draft_para_collect: Dict[str, Any]) -> None:
        """
        创建符合剪映标准的draft_meta_info.json文件
        
        Args:
            draft_folder (Path): 草稿文件夹路径
            draft_para_collect (Dict[str, Any]): 采集的参数字典
        """
        try:
            meta_file = draft_folder / "draft_meta_info.json"
            if not meta_file.exists():
                raise FileNotFoundError(f"draft_meta_info.json不存在: {meta_file}")

            with open(meta_file, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)

            canvas = draft_para_collect.get("canvas", {}) or {}

            # 始终以本次实际生成的草稿目录为准，避免模板残留路径污染
            actual_fold = str(draft_folder.resolve()).replace("\\", "/")
            meta_data["draft_fold_path"] = actual_fold
            meta_data["draft_name"] = Path(actual_fold).name
            meta_data["draft_removable_storage_device"] = Path(actual_fold).drive
            parent_path = str(Path(actual_fold).parent).replace("\\", "/")
            meta_data["draft_root_path"] = parent_path

            meta_data["draft_id"] = str(uuid.uuid4()).upper()

            now_us = int(time.time() * 1000000)
            meta_data["tm_draft_create"] = now_us
            meta_data["tm_draft_modified"] = now_us

            duration = canvas.get("duration")
            if isinstance(duration, (int, float)):
                meta_data["tm_duration"] = int(duration * 1000000)

            # 补齐剪映素材索引：若 draft_materials[type=0] 为空，则基于输入音频/图片构建
            now_s = int(time.time())
            now_us = int(time.time() * 1000000)
            draft_materials = meta_data.get("draft_materials")
            if not isinstance(draft_materials, list):
                draft_materials = []

            type0 = None
            for item in draft_materials:
                if isinstance(item, dict) and item.get("type") == 0:
                    type0 = item
                    break
            if type0 is None:
                type0 = {"type": 0, "value": []}
                draft_materials.append(type0)

            if not isinstance(type0.get("value"), list) or len(type0.get("value", [])) == 0:
                materials_value = []

                for audio in (draft_para_collect.get("audios", []) or []):
                    audio_path = (audio.get("path") or "").replace("\\", "/")
                    audio_name = Path(audio_path).name if audio_path else (audio.get("name") or "")
                    audio_duration = int(audio.get("duration") or 0)
                    if 0 < audio_duration < 1000000:
                        audio_duration = int(audio_duration * 1000000)
                    materials_value.append({
                        "create_time": now_s,
                        "duration": audio_duration,
                        "extra_info": audio_name,
                        "file_Path": audio_path,
                        "height": 0,
                        "id": str(uuid.uuid4()),
                        "import_time": now_s,
                        "import_time_ms": now_us,
                        "item_source": 1,
                        "md5": "",
                        "metetype": "music",
                        "roughcut_time_range": {"duration": audio_duration, "start": 0},
                        "sub_time_range": {"duration": -1, "start": -1},
                        "type": 0,
                        "width": 0
                    })

                for video in (draft_para_collect.get("videos", []) or []):
                    video_path = (video.get("path") or "").replace("\\", "/")
                    video_name = Path(video_path).name if video_path else (video.get("material_name") or "")
                    width = int(video.get("width") or 0)
                    height = int(video.get("height") or 0)
                    materials_value.append({
                        "create_time": now_s,
                        "duration": 5000000,
                        "extra_info": video_name,
                        "file_Path": video_path,
                        "height": height,
                        "id": str(uuid.uuid4()),
                        "import_time": now_s,
                        "import_time_ms": now_us,
                        "item_source": 1,
                        "md5": "",
                        "metetype": "photo",
                        "roughcut_time_range": {"duration": -1, "start": -1},
                        "sub_time_range": {"duration": -1, "start": -1},
                        "type": 0,
                        "width": width
                    })

                type0["value"] = materials_value
                meta_data["draft_materials"] = draft_materials

            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)

            self.logger.debug(f"草稿元数据文件已更新: {meta_file}")

        except Exception as e:
            self.logger.error(f"创建草稿元数据文件失败: {e}")
            raise ValueError(f"创建草稿元数据文件失败: {e}")
    
    def create_draft_settings(self, draft_folder: Path) -> None:
        """
        创建符合剪映标准的draft_settings文件
        
        Args:
            draft_folder (Path): 草稿文件夹路径
        """
        try:
            current_time = int(time.time())
            settings_content = f"""[General]
draft_create_time={current_time}
draft_last_edit_time={current_time}
real_edit_seconds=0
real_edit_keys=0
cloud_last_modify_platform=windows
"""
            
            settings_file = draft_folder / "draft_settings"
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(settings_content)
            
            self.logger.debug(f"草稿设置文件已创建: {settings_file}")
            
        except Exception as e:
            self.logger.error(f"创建草稿设置文件失败: {e}")
            raise ValueError(f"创建草稿设置文件失败: {e}")
    
    def create_additional_files(self, draft_folder: Path, simplified_content) -> None:
        """
        创建剪映草稿所需的其他文件
        
        Args:
            draft_folder (Path): 草稿文件夹路径
        """
        try:
            # 创建draft_agency_config.json - 匹配剪映标准格式
            agency_config = {
                "marterials": None,
                "use_converter": False,
                "video_resolution": 720
            }
            agency_file = draft_folder / "draft_agency_config.json"
            with open(agency_file, 'w', encoding='utf-8') as f:
                json.dump(agency_config, f, ensure_ascii=False, separators=(',', ':'))
            
            # 创建draft_biz_config.json - 参考草稿为空文件
            biz_file = draft_folder / "draft_biz_config.json"
            with open(biz_file, 'w', encoding='utf-8') as f:
                f.write("")
            
            # 创建attachment_editing.json - 匹配剪映标准格式
            attachment_editing = {
                "editing_draft": {
                    "edit_type": 0,
                    "has_adjusted_render_layer": False,
                    "is_use_adjust": False,
                    "is_use_lock_object": False,
                    "is_use_loudness_unify": False,
                    "is_use_retouch_face": True,
                    "is_use_smart_adjust_color": False,
                    "is_use_smart_motion": False,
                    "is_use_text_to_audio": False,
                    "profile_entrance_type": "",
                    "publish_enter_from": "",
                    "publish_type": "",
                    "text_convert_case_types": [],
                    "version": "1.0.0"
                }
            }
            attachment_file = draft_folder / "attachment_editing.json"
            with open(attachment_file, 'w', encoding='utf-8') as f:
                json.dump(attachment_editing, f, ensure_ascii=False, separators=(',', ':'))
            
            # 创建attachment_pc_common.json
            attachment_pc_common = {}
            pc_common_file = draft_folder / "attachment_pc_common.json"
            with open(pc_common_file, 'w', encoding='utf-8') as f:
                json.dump(attachment_pc_common, f, ensure_ascii=False, indent=2)
            
            # 创建key_value.json
            key_value = {}
            key_value_file = draft_folder / "key_value.json"
            with open(key_value_file, 'w', encoding='utf-8') as f:
                json.dump(key_value, f, ensure_ascii=False, indent=2)
            
            # 创建空的draft_extra文件
            extra_file = draft_folder / "draft.extra"
            extra_file.touch()
            
            # 创建空的draft_virtual_store.json文件
            virtual_store = {}
            virtual_store_file = draft_folder / "draft_virtual_store.json"
            with open(virtual_store_file, 'w', encoding='utf-8') as f:
                json.dump(virtual_store, f, ensure_ascii=False, separators=(',', ':'))
            
            # 创建template.tmp - 空白模板文件
            template_content = {
                "canvas_config": {
                    "height": 0,
                    "ratio": "original",
                    "width": 0
                },
                "color_space": 0,
                "config": {
                    "adjust_max_index": 1,
                    "attachment_info": [],
                    "combination_max_index": 1,
                    "export_range": None,
                    "export_settings": None,
                    "keyframe_graph_list": [],
                    "material_ai_edit_count": 0,
                    "mode": "common",
                    "player_version": "8.0.0",
                    "recover_from_adjust": False,
                    "recover_from_color_match": False,
                    "recover_from_color_wizard": False,
                    "recover_from_smart_cutter": False,
                    "recover_from_track_adjust": False,
                    "speed_setting": {
                        "speed_mode": 1,
                        "speed_segment_setting": {
                            "max_speed": 2.0,
                            "min_speed": 0.5,
                            "mode": 0
                        }
                    },
                    "use_adjust": False,
                    "use_3d_rotation": False,
                    "use_animation": False,
                    "use_beautify": False,
                    "use_chartlet": False,
                    "use_color_match": False,
                    "use_color_wizard": False,
                    "use_common_editing": False,
                    "use_correction": False,
                    "use_crop": False,
                    "use_custom_animations": False,
                    "use_keyframe": False,
                    "use_label": False,
                    "use_lut": False,
                    "use_morph_cut": False,
                    "use_motion_blur": False,
                    "use_motion_effect": False,
                    "use_peak": False,
                    "use_pro_color_wizard": False,
                    "use_smart_cutter": False,
                    "use_split_video": False,
                    "use_standard": False,
                    "use_sticker_text": False,
                    "use_stock_sounds": False,
                    "use_speed": False,
                    "use_style": False,
                    "use_text_ai": False,
                    "use_text_template": False,
                    "use_track_adjust": False,
                    "use_transition": False,
                    "use_video_effect": False,
                    "use_video_overlay": False,
                    "use_voice_changer": False,
                    "volume_setting": {
                        "curve_type": 0,
                        "max_keyframe_count": 1,
                        "speed": 1.0
                    }
                },
                "cover": None,
                "create_time": 0,
                "duration": 0,
                "extra_info": {},
                "fps": 30.0,
                "free_render_index_mode_on": False,
                "group_container": {},
                "id": "",
                "keyframe_graph_list": [],
                "keyframes": {},
                "last_modified_platform": {},
                "materials": {
                    "audios": [],
                    "chartlets": [],
                    "effects": [],
                    "handwrites": [],
                    "stickers": [],
                    "texts": [],
                    "videos": []
                },
                "tracks": []
            }
            template_file = draft_folder / "template.tmp"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_content, f, ensure_ascii=False, separators=(',', ':'))
            
            # 创建template-2.tmp - 复制主草稿内容作为模板
            template2_file = draft_folder / "template-2.tmp"
            with open(template2_file, 'w', encoding='utf-8') as f:
                json.dump(simplified_content, f, ensure_ascii=False, separators=(',', ':'))
            
            # 创建draft_content.json.bak - 主草稿的备份
            backup_file = draft_folder / "draft_content.json.bak"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(simplified_content, f, ensure_ascii=False, separators=(',', ':'))
            
            self.logger.debug(f"其他必需文件已创建完成")
            
        except Exception as e:
            self.logger.error(f"创建其他必需文件失败: {e}")
            raise ValueError(f"创建其他必需文件失败: {e}")
    
    def update_draft_metadata(self, draft_folder: Path):
        """
        更新草稿元数据文件 - 保留为兼容性方法，实际调用create_draft_meta_info
        
        Args:
            draft_folder (Path): 草稿文件夹路径
        """
        # 这个方法保留为兼容性，实际工作在create_draft_meta_info中完成
        pass
    
    def execute_draft_composition(
        self,
        draft_para_collect_path: Union[str, Dict[str, Any]]
    ) -> str:
        """
        执行完整的草稿合成工作流 - ext适配版本
        
        Args:
            draft_para_collect_path (Union[str, Dict[str, Any]]): 采集参数文件路径或参数字典
            
        Returns:
            str: 生成的草稿文件夹路径
            
        Raises:
            FileNotFoundError: 当文件不存在时抛出
            ValueError: 当参数无效时抛出
            IOError: 当文件操作失败时抛出
        """
        try:
            self.logger.info("开始执行ext草稿合成工作流...")
            trace_enabled = os.environ.get("JAS_TRACE_PATHS", "0") == "1"

            def _collect_paths_from_para(para: Dict[str, Any]) -> Dict[str, Any]:
                videos = [str((x or {}).get("path", "")).replace("\\", "/") for x in (para.get("videos", []) or [])]
                audios = [str((x or {}).get("path", "")).replace("\\", "/") for x in (para.get("audios", []) or [])]
                return {"videos": videos, "audios": audios}

            def _collect_paths_from_content(content: Dict[str, Any]) -> Dict[str, Any]:
                mats = (content.get("materials", {}) or {})
                videos = [str((x or {}).get("path", "")).replace("\\", "/") for x in (mats.get("videos", []) or [])]
                audios = [str((x or {}).get("path", "")).replace("\\", "/") for x in (mats.get("audios", []) or [])]
                return {"videos": videos, "audios": audios}

            def _write_trace(stage: str, payload: Dict[str, Any]) -> None:
                if not trace_enabled:
                    return
                trace_dir = self.output_dir / "trace"
                trace_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                digest = hashlib.md5(stage.encode("utf-8")).hexdigest()[:6]
                trace_path = trace_dir / f"{ts}_{stage}_{digest}.json"
                with open(trace_path, "w", encoding="utf-8") as tf:
                    json.dump(payload, tf, ensure_ascii=False, indent=2)

            def _prefer_existing_path(path_str: str) -> str:
                s = (path_str or "").replace("\\", "/")
                if not s:
                    return s
                p = Path(s)
                if s.startswith("D:/BaiduSyncdisk/"):
                    e = Path("E:/" + s[len("D:/"):])
                    if e.exists():
                        return str(e).replace("\\", "/")
                    if p.exists():
                        return str(p).replace("\\", "/")
                if s.startswith("E:/BaiduSyncdisk/"):
                    if p.exists():
                        return str(p).replace("\\", "/")
                    d = Path("D:/" + s[len("E:/"):])
                    if d.exists():
                        return str(d).replace("\\", "/")
                if p.exists():
                    return str(p).replace("\\", "/")
                return s
            
            # 步骤1: 加载采集参数
            if isinstance(draft_para_collect_path, dict):
                # 直接使用传入的字典
                draft_para_collect = draft_para_collect_path
                self.logger.debug("使用传入的参数字典")
            else:
                # 从文件加载参数
                with open(draft_para_collect_path, 'r', encoding='utf-8') as f:
                    draft_para_collect = json.load(f)
                self.logger.debug(f"从文件加载参数: {draft_para_collect_path}")
            _write_trace("01_loaded_para", _collect_paths_from_para(draft_para_collect))
            
            # 步骤2: 复制空白草稿
            canvas_cfg = draft_para_collect.get("canvas", {}) or {}
            draft_parent_folder = canvas_cfg.get("output_parent_draft_folder_path") or str(self.output_dir)
            if draft_parent_folder and not os.path.isabs(draft_parent_folder):
                draft_parent_folder = str(self.output_dir.parent / draft_parent_folder)
            draft_folder = self.copy_blank_draft(draft_parent_folder)
            self.logger.info(f"草稿文件夹创建完成: {draft_folder}")
            
            # 步骤3: 不复制素材文件，保持原始路径
            # 剪映草稿中的素材路径应该指向原始位置，不复制到草稿文件夹
            self.logger.debug("保持素材原始路径，不复制到草稿文件夹")
            
            # 步骤4: 加载草稿内容
            draft_content_path = Path(draft_folder) / "draft_content.json"
            with open(draft_content_path, 'r', encoding='utf-8') as f:
                draft_content = json.load(f)
            
            # 步骤5: 修改画布配置
            canvas_config = draft_para_collect.get("canvas", {})
            if canvas_config:
                draft_content = self.modify_canvas(draft_content, draft_para_collect)
                self.logger.debug("画布配置修改完成")

            # 在主流程内先统一素材路径（优先E盘实际存在路径）
            for v in (draft_para_collect.get("videos", []) or []):
                if "path" in v:
                    v["path"] = _prefer_existing_path(v.get("path", ""))
            for a in (draft_para_collect.get("audios", []) or []):
                if "path" in a:
                    a["path"] = _prefer_existing_path(a.get("path", ""))
            _write_trace("02_para_after_prefer", _collect_paths_from_para(draft_para_collect))
            
            # 步骤6: 创建符合剪映标准格式的草稿内容
            simplified_content = self._create_simplified_content(draft_para_collect, None)
            _write_trace("03_after_create_simplified", _collect_paths_from_content(simplified_content))
            
            # 步骤7: 保存修改后的草稿内容 - 使用压缩格式匹配剪映
            # 确保keyframes中的texts和videos为空（参考草稿模板要求）
            if 'keyframes' in simplified_content:
                simplified_content['keyframes']['texts'] = []
                simplified_content['keyframes']['videos'] = []

            # 再次兜底修正 materials 中路径，避免后续链路回写 D 盘
            mats = simplified_content.get("materials", {}) or {}
            for v in (mats.get("videos", []) or []):
                if "path" in v:
                    v["path"] = _prefer_existing_path(v.get("path", ""))
            for a in (mats.get("audios", []) or []):
                if "path" in a:
                    a["path"] = _prefer_existing_path(a.get("path", ""))
            simplified_content["materials"] = mats
            _write_trace("04_after_material_prefer", _collect_paths_from_content(simplified_content))
            
            with open(draft_content_path, 'w', encoding='utf-8') as f:
                json.dump(simplified_content, f, ensure_ascii=False, separators=(',', ':'))
            _write_trace("05_written_draft_content", {"draft_content_path": str(draft_content_path).replace("\\", "/"), **_collect_paths_from_content(simplified_content)})
            
            # 步骤8: 创建剪映标准格式的元数据文件
            self.create_draft_meta_info(Path(draft_folder), draft_para_collect)
            if trace_enabled:
                meta_file = Path(draft_folder) / "draft_meta_info.json"
                if meta_file.exists():
                    try:
                        meta = json.loads(meta_file.read_text(encoding="utf-8-sig"))
                        meta_paths = []
                        for item in meta.get("draft_materials", []) or []:
                            for v in item.get("value", []) or []:
                                if "file_Path" in v:
                                    meta_paths.append(str(v.get("file_Path", "")).replace("\\", "/"))
                        _write_trace("06_written_draft_meta", {"draft_meta_info_path": str(meta_file).replace("\\", "/"), "file_paths": meta_paths})
                    except Exception:
                        pass
            
            # 步骤9: 创建草稿设置文件
            self.create_draft_settings(Path(draft_folder))
            
            # 步骤10: 创建其他必需文件
            self.create_additional_files(Path(draft_folder), simplified_content)
            
            self.logger.info(f"ext草稿合成工作流执行完成，输出路径: {draft_folder}")
            return draft_folder
            
        except Exception as e:
            self.logger.error(f"ext草稿合成工作流执行失败: {e}")
            raise ValueError(f"ext草稿合成工作流执行失败: {e}")
    
    def _create_simplified_content(
        self,
        draft_para_collect: Dict[str, Any],
        template_content: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建完全符合源草稿结构的草稿内容
        
        Args:
            draft_para_collect (Dict[str, Any]): 采集的参数字典
            
        Returns:
            Dict[str, Any]: 完全符合源草稿结构的草稿内容
        """
        try:
            # 导入完整的创建器
            from .create_complete_simplified_content import create_complete_simplified_content
            
            # 使用完整创建器生成simplified_content
            simplified_content = create_complete_simplified_content(
                draft_para_collect,
                template_content=template_content
            )
            if "materials" not in simplified_content:
                simplified_content["materials"] = {}
            
            # 收集素材
            pics = draft_para_collect.get("videos", []) or []
            texts = draft_para_collect.get("texts", []) or []
            audios_unified = draft_para_collect.get("audios", []) or []
            # 兼容旧结构
            for audio_type in ("bgms", "voices", "sounds"):
                if audio_type in draft_para_collect and draft_para_collect.get(audio_type):
                    for a in draft_para_collect[audio_type]:
                        audios_unified.append({
                            "id": a.get("id", ""),
                            "name": a.get("name", a.get("material_name", "")),
                            "path": a.get("path", "").replace("\\", "/"),
                            "duration": a.get("duration", 0),
                            "tracks": a.get("tracks", {})
                        })
            # 用解析结果生成materials.audios，确保ID与tracks段一致，并与参考草稿字段完全对齐
            audios_materials = []
            for a in audios_unified:
                audios_materials.append({
                    "app_id": 0,
                    "category_id": "",
                    "category_name": "",
                    "check_flag": 1,
                    "copyright_limit_type": "none",
                    "duration": int((a.get("duration", 0) or 0) * 1000000),  # 解析结果为秒，转换为微秒以匹配参考草稿
                    "effect_id": "",
                    "formula_id": "",
                    "id": a.get("id", ""),
                    "intensifies_path": "",
                    "is_ai_clone_tone": False,
                    "is_text_edit_overdub": False,
                    "is_ugc": False,
                    "local_material_id": "",
                    "music_id": "",
                    "name": a.get("name", ""),
                    "path": a.get("path", ""),
                    "query": "",
                    "request_id": "",
                    "resource_id": "",
                    "search_id": "",
                    "source_from": "",
                    "source_platform": 0,
                    "team_id": "",
                    "text_id": "",
                    "tone_category_id": "",
                    "tone_category_name": "",
                    "tone_effect_id": "",
                    "tone_effect_name": "",
                    "tone_platform": "",
                    "tone_second_category_id": "",
                    "tone_second_category_name": "",
                    "tone_speaker": "",
                    "tone_type": "",
                    "type": "extract_music",
                    "video_id": "",
                    "wave_points": []
                })
            simplified_content["materials"]["audios"] = audios_materials
            
            texts_materials = []
            def _hex_to_rgb_list(h):
                v = (h or "").lstrip("#")
                if len(v) == 3:
                    v = "".join([c*2 for c in v])
                try:
                    r = int(v[0:2], 16) / 255.0
                    g = int(v[2:4], 16) / 255.0
                    b = int(v[4:6], 16) / 255.0
                    return [round(r, 6), round(g, 6), round(b, 6)]
                except Exception:
                    return [1, 1, 1]
            def _build_text_content_string(text_params):
                t = text_params.get("content", "")
                text_plain = t.get("text", "") if isinstance(t, dict) else (t or "")
                color_hex = text_params.get("text_color", "#FFFFFF")
                stroke_hex = text_params.get("border_color", "#000000")
                stroke_width = text_params.get("border_width", 0)
                font_path = text_params.get("font_name", "")
                font_size = text_params.get("font_size", 12.0)
                rng = [0, len(text_plain)]
                obj = {
                    "text": text_plain,
                    "styles": [{
                        "fill": { "content": { "solid": { "color": _hex_to_rgb_list(color_hex) } } },
                        "font": { "path": font_path, "id": "" },
                        "strokes": [{ "content": { "solid": { "color": _hex_to_rgb_list(stroke_hex) } }, "width": float(stroke_width) }],
                        "size": float(font_size),
                        "useLetterColor": True,
                        "range": rng
                    }]
                }
                import json as _json
                return _json.dumps(obj, ensure_ascii=False)
            for text in texts:
                tt = text.get("tracks", {}) or {}
                c = text.get("content", "")
                content_text = c.get("text", "") if isinstance(c, dict) else c
                texts_materials.append({
                    "ad_meta": {},
                    "app_id": 0,
                    "background_color": "",
                    "background_color_id": 0,
                    "background_mode": 0,
                    "bold": False,
                    "border_color": text.get("border_color", "#000000"),
                    "border_width": text.get("border_width", 0),
                    "category_id": "",
                    "category_name": "",
                    "check_flag": 1,
                    "copyright_limit_type": "none",
                    "effect_id": "",
                    "enable_3d": False,
                    "extra": "",
                    "font_family": 0,
                    "font_id": text.get("font_name", ""),
                    "font_license": 0,
                    "font_lock": False,
                    "font_name": text.get("font_name", ""),
                    "font_size": text.get("font_size", 12.0),
                    "format": {"align": 0, "direction": 0, "justify": 0},
                    "gradient": False,
                    "has_stroke": False,
                    "height": 1080,
                    "id": text.get("id", ""),
                    "intensity": 0,
                    "is_ugc": False,
                    "italic": False,
                    "letter_spacing": 0,
                    "line_spacing_percent": 100,
                    "local_material_id": "",
                    "lock": False,
                    "lyric": False,
                    "matting": False,
                    "narration": False,
                    "opacity": 100,
                    "path": "",
                    "preset_id": "",
                    "preset_name": "",
                    "primary_color": text.get("text_color", "#FFFFFF"),
                    "rotation": 0,
                    "scale": 1,
                    "shader_transparency": 1,
                    "source": "",
                    "source_platform": 0,
                    "space": 0,
                    "stroke": False,
                    "stroke_color": "",
                    "stroke_width": 0,
                    "team_id": "",
                    "template_id": "",
                    "text": None,
                    "content": _build_text_content_string(text),
                    "text_color": text.get("text_color", "#FFFFFF"),
                    "text_shadow": False,
                    "typeface": 0,
                    "url": "",
                    "use_font_animation": False,
                    "width": 1920,
                    "x": tt.get("transform_x", 0),
                    "y": tt.get("transform_y", 0)
                })
            # 根据留言板建议1：避免覆盖materials.texts，保留CompleteMaterialsBuilder的模板结构
            # 注释掉覆盖逻辑，使用CompleteMaterialsBuilder._create_texts()的结果
            # if texts:
            #     simplified_content["materials"]["texts"] = texts_materials
            # videos字段由CompleteMaterialsBuilder._create_videos生成，这里不再覆盖
            # videos_materials = []
            # for pic in pics:
            #     pt = pic.get("tracks", {}) or {}
            #     videos_materials.append({
            #         "app_id": 0,
            #         "id": pic.get("id", ""),
            #         "name": pic.get("material_name", ""),
            #         "duration": int((pt.get("duration", 0) or 0) * 1000000),
            #         "path": pic.get("path", "")
            #     })
            # # 只有当输入文件中有pics时才覆盖，否则保留complete_materials_builder中的设置
            # if pics:
            #     simplified_content["materials"]["videos"] = videos_materials
            material_anims = []
            text_anim_refs = {}
            for text in texts:
                tt = text.get("tracks", {}) or {}
                manims = tt.get("material_animations", {}) or {}
                animations = manims.get("animations") or []
                if animations:
                    anim_id = f"ANIM_{text.get('id','')}"
                    ref_list = []
                    convs = []
                    for am in animations:
                        start = am.get("start", 0)
                        duration = am.get("duration", 0)
                        convs.append({
                            "type": am.get("type"),
                            "name": am.get("name"),
                            "start": float(start),
                            "duration": int(round(duration * 1000000)) if isinstance(duration, (int, float)) else 0,
                            "category_name": am.get("category_name", "")
                        })
                    material_anims.append({"id": anim_id, "animations": convs})
                    text_anim_refs[text.get("id","")] = [anim_id]
            # simplified_content["materials"]["material_animations"] = material_anims  # 注释掉，使用complete_materials_builder生成的内容
            
            # tracks 已由 create_complete_simplified_content 生成，无需二次覆盖
            if "keyframes" not in simplified_content:
                simplified_content["keyframes"] = {"videos": [], "texts": [], "audios": []}
            # 将segment关键帧汇总到顶层keyframes（视频与文字）
            for t in simplified_content["tracks"]:
                for seg in t.get("segments", []) or []:
                    if "common_keyframes" in seg:
                        entry = {"segment_id": seg.get("id", ""), "keyframes": seg["common_keyframes"]}
                        # 根据 material_id 在 materials.texts/videos 的存在性来区分归类
                        mid = seg.get("material_id")
                        mats = simplified_content.get("materials", {}) or {}
                        mat_text_ids = set(m.get("id") for m in mats.get("texts", []) or [])
                        if mid in mat_text_ids:
                            simplified_content["keyframes"]["texts"].append(entry)
                        else:
                            simplified_content["keyframes"]["videos"].append(entry)
            
            # 强制确保platform和last_modified_platform字段与参考草稿一致（固定值）
            # 参考草稿中platform和last_modified_platform的hard_disk_id值不同！
            expected_platform = {
                "app_id": 3704,
                "app_source": "lv",
                "app_version": "5.9.0",
                "device_id": "3ed8b66f5ac1c0f2cbe5644f6ec6c024",
                "hard_disk_id": "dcd82461a72e6598ad89d94df6641c57",  # platform的值
                "mac_address": "f32f89242f5557310e627241e488ea71",  # 单个MAC地址
                "os": "windows",
                "os_version": "10.0.19045"
            }
            expected_last_modified_platform = {
                "app_id": 3704,
                "app_source": "lv",
                "app_version": "5.9.0",
                "device_id": "3ed8b66f5ac1c0f2cbe5644f6ec6c024",
                "hard_disk_id": "",  # last_modified_platform的值是空字符串！
                "mac_address": "f32f89242f5557310e627241e488ea71",  # 单个MAC地址
                "os": "windows",
                "os_version": "10.0.19045"
            }
            simplified_content['platform'] = expected_platform
            simplified_content['last_modified_platform'] = expected_last_modified_platform
            
            return simplified_content
        except Exception as e:
            self.logger.error(f"创建简化草稿内容失败: {e}")
            raise ValueError(f"创建简化草稿内容失败: {e}")


# 为了保持向后兼容性，提供简化接口
def execute_draft_composition_workflow(draft_para_collect_path: str) -> str:
    """
    简化的草稿合成工作流接口
    
    Args:
        draft_para_collect_path (str): 采集参数文件路径
        
    Returns:
        str: 生成的草稿文件夹路径
    """
    comb = DraftConfigComb()
    return comb.execute_draft_composition(draft_para_collect_path)
