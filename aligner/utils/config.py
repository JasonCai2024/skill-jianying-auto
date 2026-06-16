"""
配置管理

提供配置文件的读取和管理功能
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .logger import get_logger

logger = get_logger(__name__)

class Config:
    """配置管理类
    
    负责读取和管理配置文件，提供默认值和验证
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = get_logger(__name__)
        
        # 确定配置文件路径
        if config_file:
            self.config_file = Path(config_file)
        else:
            # 默认配置文件位置
            self.config_file = Path(__file__).parent.parent.parent / "config.json"
        
        self.config_data = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            Dict[str, Any]: 配置数据字典
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                self.logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                self.logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
                self.config_data = self._get_default_config()
                self.save_config()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self.config_data = self._get_default_config()
        
        return self.config_data
    
    def save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置文件保存成功: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'logging.level'
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config_data
        
        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        self.logger.debug(f"配置设置: {key} = {value}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return {
            "logging": {
                "level": "INFO",
                "file_path": "logs/aeneas_aligner.log",
                "max_bytes": 10485760,  # 10MB
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S"
            },
            "aeneas": {
                "auto_detect_python": True,
                "custom_python_path": "",
                "timeout_seconds": 300,
                "temp_dir": "temp",
                "keep_temp_files": False
            },
            "processing": {
                "default_language": "zho",
                "supported_languages": ["zho", "eng"],
                "max_text_length": 10000,
                "min_segment_duration": 0.5,
                "max_segment_duration": 30.0
            },
            "output": {
                "default_format": "json",
                "include_debug_info": True,
                "precision": "microseconds"
            }
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置的有效性
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        issues = []
        
        # 验证日志配置
        log_level = self.get('logging.level', 'INFO')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_levels:
            issues.append(f"无效的日志级别: {log_level}")
        
        # 验证Aeneas配置
        timeout = self.get('aeneas.timeout_seconds', 300)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            issues.append(f"无效的超时设置: {timeout}")
        
        # 验证语言配置
        default_lang = self.get('processing.default_language', 'zho')
        supported_langs = self.get('processing.supported_languages', ['zho', 'eng'])
        if default_lang not in supported_langs:
            issues.append(f"不支持的默认语言: {default_lang}")
        
        # 验证输出格式
        output_format = self.get('output.default_format', 'json')
        valid_formats = ['json', 'srt', 'txt']
        if output_format not in valid_formats:
            issues.append(f"不支持的输出格式: {output_format}")
        
        result = {
            "valid": len(issues) == 0,
            "issues": issues,
            "config": self.config_data
        }
        
        if not result["valid"]:
            self.logger.warning(f"配置验证失败: {issues}")
        else:
            self.logger.info("配置验证通过")
        
        return result
    
    def get_aeneas_python_path(self) -> Optional[str]:
        """获取Aeneas Python路径
        
        Returns:
            Optional[str]: Python路径，如果未配置则返回None
        """
        custom_path = self.get('aeneas.custom_python_path')
        if custom_path and Path(custom_path).exists():
            return custom_path
        
        # 如果启用了自动检测，返回None（由AeneasProcessor自动检测）
        if self.get('aeneas.auto_detect_python', True):
            return None
        
        return None
    
    def get_log_level(self) -> int:
        """获取日志级别的数值
        
        Returns:
            int: 日志级别数值
        """
        level_map = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }
        
        level_name = self.get('logging.level', 'INFO')
        return level_map.get(level_name, 20)
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 配置的字符串表示
        """
        return json.dumps(self.config_data, ensure_ascii=False, indent=2)

# 全局配置实例
_config_instance = None

def get_config(config_file: Optional[str] = None) -> Config:
    """获取全局配置实例
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        Config: 配置实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_file)
    return _config_instance