"""
日志系统

提供统一的日志记录功能，支持不同级别的日志输出和文件记录
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional

# 全局日志记录器字典
_loggers = {}

def setup_logger(name: str = None, level: int = logging.INFO, 
                log_file: Optional[str] = None, 
                console: bool = True) -> logging.Logger:
    """
    初始化日志系统
    
    Args:
        name: 日志记录器名称，如果为None则使用根记录器
        level: 日志级别，默认为INFO
        log_file: 日志文件路径，如果为None则不写入文件
        console: 是否输出到控制台，默认为True
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 使用根记录器或指定名称的记录器
    logger_name = name if name else 'aeneas_aligner'
    logger = logging.getLogger(logger_name)
    
    # 避免重复配置
    if logger_name in _loggers:
        return logger
    
    logger.setLevel(level)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 记录已配置的记录器
    _loggers[logger_name] = logger
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器实例
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    logger_name = name if name else 'aeneas_aligner'
    
    if logger_name not in _loggers:
        # 自动设置默认日志记录器
        return setup_logger(
            name=logger_name,
            level=logging.INFO,
            log_file='logs/aeneas_aligner.log',
            console=True
        )
    
    return _loggers[logger_name]

def set_log_level(logger: logging.Logger, level: int):
    """
    设置日志记录器的级别
    
    Args:
        logger: 日志记录器实例
        level: 日志级别
    """
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

def add_file_handler(logger: logging.Logger, log_file: str, level: int = logging.INFO):
    """
    为日志记录器添加文件处理器
    
    Args:
        logger: 日志记录器实例
        log_file: 日志文件路径
        level: 日志级别
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)

def remove_all_handlers(logger: logging.Logger):
    """
    移除日志记录器的所有处理器
    
    Args:
        logger: 日志记录器实例
    """
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

# 默认设置
if not _loggers:
    # 初始化根日志记录器
    setup_logger(
        name='aeneas_aligner',
        level=logging.INFO,
        log_file='logs/aeneas_aligner.log',
        console=True
    )