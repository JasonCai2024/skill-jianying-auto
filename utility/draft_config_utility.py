import re
from typing import Dict, List, Any
import os
import logging
import json
import sys
import shutil
from pathlib import Path
try:
    from settings_ext import settings
except ImportError:
    class DefaultSettings:
        base_dir = Path(__file__).resolve().parents[1]
    settings = DefaultSettings()

logger = logging.getLogger(__name__)

class TimestampConverter:
    @staticmethod
    def seconds_to_microseconds(seconds: float) -> int:
        return int(seconds * 1_000_000)
    @staticmethod
    def microseconds_to_seconds(microseconds: int) -> float:
        return microseconds / 1_000_000

class DraftConfigUtility:
    @staticmethod
    def process_subtitle_content(subtitle_content: str) -> List[str]:
        if not subtitle_content:
            return []
        lines = [line.strip() for line in subtitle_content.split('\n') if line.strip()]
        return lines
    @staticmethod
    def load_template_config(template_name: str) -> Dict[str, Any]:
        if os.path.isabs(template_name) or os.path.exists(template_name):
            template_file_path = template_name
        else:
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = str(settings.base_dir)
            template_file_path = os.path.join(base_path, "user_data", "draft_workflow", f"{template_name}.json")
        if not os.path.exists(template_file_path):
            raise FileNotFoundError(f"剪辑模版文件不存在: {template_file_path}")
        with open(template_file_path, 'r', encoding='utf-8') as f:
            template_config = json.load(f)
        return template_config

    @staticmethod
    def load_font_name_map() -> Dict[str, Any]:
        base_path = str(settings.base_dir)
        map_path = os.path.join(base_path, "user_data", "effect", "font_name_map.json")
        if not os.path.exists(map_path):
            return {}
        with open(map_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("font_name_map", {}) or {}

    @staticmethod
    def resolve_font_by_title(font_title: str, jianying_folder_path: str = "") -> Dict[str, Any]:
        if not font_title:
            return {}
        font_map = DraftConfigUtility.load_font_name_map()
        font_data = font_map.get(font_title, {}) or {}
        if not font_data:
            return {}
        font_path = font_data.get("font_path", "") or ""
        if font_path and not os.path.isabs(font_path):
            # 支持通过剪映安装目录拼接相对路径
            base = (jianying_folder_path or "").strip()
            if base:
                font_path = os.path.join(base, font_path)
            else:
                font_path = ""
        if font_path:
            font_path = font_path.replace("\\", "/")
        return {
            "font_path": font_path,
            "font_resource_id": font_data.get("font_resource_id", "") or ""
        }

    @staticmethod
    def load_audio_name_map() -> Dict[str, Any]:
        base_path = str(settings.base_dir)
        map_path = os.path.join(base_path, "user_data", "effect", "audio_name_map.json")
        if not os.path.exists(map_path):
            return {}
        with open(map_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        audio_map = data.get("audio_name_map", {}) or {}
        for _, value in audio_map.items():
            path = value.get("path")
            if path and not os.path.isabs(path):
                value["path"] = os.path.join(base_path, path).replace("\\", "/")
        return audio_map

    @staticmethod
    def load_animation_map() -> List[Dict[str, Any]]:
        base_path = str(settings.base_dir)
        map_path = os.path.join(base_path, "user_data", "effect", "animation_map.json")
        if not os.path.exists(map_path):
            return []
        with open(map_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("animation_map", []) or []

    # --- 字体编码转换 ---
    @staticmethod
    def font_code_convert(font_title: str) -> dict:
        """
        转换字体编码（返回字体请求ID、效果ID和路径）
        文档要求：
        1. 返回 {font_request_id, font_effect_id, font_path}
        2. 检查font_path是否存在，若不存在则从user_data/effect/text_font/复制
        """
        font_mapping = {
            "俪金黑": {
                "font_request_id": "20250415231746F9005D520F716ED1ADC8",
                "font_effect_id": "6740499317733200388",
                "font_path": "C:/Users/pc/AppData/Local/JianyingPro/User Data/Cache/effect/349465/4ef7d2eb7cdfcff226f086008045131a/俪金黑.TTF"
            },
            "优设标题黑": {
                "font_request_id": "20250415231746F9005D520F716ED1ADC8",
                "font_effect_id": "7068207165277737502",
                "font_path": "C:/Users/pc/AppData/Local/JianyingPro/User Data/Cache/effect/1588336/d9f1238f50005595eff5f545aa54776c/优设标题黑.ttf"
            }
        }
        
        if font_title not in font_mapping:
            # 检查是否是已映射的英文名称
            inverted_map = {
                v["font_path"].split('/')[-1].split('.')[0]: k 
                for k, v in font_mapping.items()
            }
            if font_title in inverted_map:
                return font_mapping[inverted_map[font_title]]
            
            raise ValueError(f"不支持的字体: {font_title}")

        font_data = font_mapping[font_title]
        
        # === 检查并复制字体文件 ===
        font_path = font_data["font_path"]
        if os.path.exists(font_path):
            logger.info(f"字体文件已存在: {font_path}")
        else:
            try:
                # 获取字体文件名（如"俪金黑.TTF"）
                font_file = os.path.basename(font_path)
                # 源字体路径（使用ext项目的user_data/effect/text_font/目录）
                if getattr(sys, 'frozen', False):
                    # 在打包环境中，使用可执行文件所在目录
                    base_path = os.path.dirname(sys.executable)
                else:
                    # 在源代码环境中，使用项目根目录
                    base_path = str(settings.base_dir)
                src_font = os.path.join(base_path, "user_data", "effect", "text_font", font_file)
                
                if os.path.exists(src_font):
                    # 创建目标目录（如果不存在）
                    os.makedirs(os.path.dirname(font_path), exist_ok=True)
                    # 复制字体文件
                    shutil.copy2(src_font, font_path)
                    logger.info(f"已复制字体文件: {src_font} -> {font_path}")
                else:
                    raise FileNotFoundError(f"源字体文件不存在: {src_font}")
            except Exception as e:
                raise RuntimeError(f"字体文件处理失败: {e}") from e
        
        return font_data

    # --- 动画编码转换 ---
    @classmethod
    def text_animation_code_convert(cls, animation_name: str) -> dict:
        """
        文字动画编码转换
        文档要求：
        1. 返回动画ID和路径
        2. 从user_data/effect/text_animation/复制动画文件
        """
        animation_map = {
            "渐显": {
                "animation_request_id": "202504152317473B08A6F4BD7734C2362C",
                "animation_effect_id": "6724916044072227332",
                "animation_id": "1644304",
                "animation_path": "C:/Users/pc/AppData/Local/JianyingPro/User Data/Cache/effect/1644304/40859aa05ff9f3e3a3f0de7bfead1c42"
            },
            "渐隐": {
                "animation_request_id": "202504152317477B8BDE84F8ADE3C3A88D",
                "animation_effect_id": "6724919382104871427",
                "animation_id": "1644600",
                "animation_path": "C:/Users/pc/AppData/Local/JianyingPro/User Data/Cache/effect/1644600/11004616098603d847593ce9ede05a62"
            },
            "颤抖": {
                "animation_request_id": "202504152317476EBE8976544E2BBC5E19",
                "animation_effect_id": "6764189482871689742",
                "animation_id": "1644509",
                "animation_path": "C:/Users/pc/AppData/Local/JianyingPro/User Data/Cache/effect/1644509/9d16d8998abe172511399c3158bddddd"
            }
        }
        
        if animation_name not in animation_map:
            raise ValueError(f"不支持的文字动画: {animation_name}")
        
        return animation_map[animation_name]

