"""
输出格式化器

负责将处理后的对齐数据转换为标准格式
"""

import json
import time
from typing import List, Dict, Any

try:
    from ..utils.logger import get_logger
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from utils.logger import get_logger

logger = get_logger(__name__)

class OutputFormatter:
    """输出格式化器
    
    负责将处理后的对齐数据转换为标准格式
    """
    
    @staticmethod
    def to_subtitle_format(segments: List[Dict], original_text: str = "", 
                         audio_file: str = "", language: str = "zho") -> Dict:
        """转换为字幕格式
        
        生成与NovelCut完全一致的数据结构
        
        Args:
            segments: 处理后的分段数据
            original_text: 原始文本
            audio_file: 音频文件路径
            language: 语言代码
            
        Returns:
            Dict: 标准字幕格式数据
        """
        logger.info(f"转换为字幕格式，分段数量: {len(segments)}")
        
        # 计算总时长和分段数量
        total_duration = 0
        valid_segments = []
        
        for segment in segments:
            if segment.get('words') and segment.get('text'):
                # 计算分段时长
                segment_start = segment.get('start', 0)
                segment_duration = segment.get('duration', 0)
                
                # 确保words结构完整
                words = segment['words']
                if not isinstance(words, dict):
                    logger.warning(f"分段words结构异常: {words}, 跳过该分段")
                    continue
                
                # 验证必需的字段
                required_fields = ['group_id', 'text', 'start_time', 'end_time']
                if not all(field in words for field in required_fields):
                    logger.warning(f"分段words缺少必需字段: {words.keys()}, 跳过该分段")
                    continue
                
                # 验证数组长度一致性
                array_lengths = {
                    'text': len(words.get('text', [])),
                    'start_time': len(words.get('start_time', [])),
                    'end_time': len(words.get('end_time', []))
                }
                
                if len(set(array_lengths.values())) > 1:
                    logger.warning(f"分段words数组长度不一致: {array_lengths}, 跳过该分段")
                    continue
                
                valid_segments.append(segment)
                total_duration = max(total_duration, segment_start + segment_duration)
        
        if not valid_segments:
            logger.error("没有有效的分段数据")
            return {
                "status": "error",
                "error": "没有有效的分段数据"
            }
        
        # 构建标准格式结果
        result = {
            "status": "success",
            "language": language,
            "audio_file": audio_file,
            "original_text": original_text,
            "alignment_result": {
                "segments": valid_segments,
                "total_segments": len(valid_segments),
                "total_duration": total_duration
            }
        }
        
        logger.info(f"字幕格式转换完成，有效分段: {len(valid_segments)}, 总时长: {total_duration} 微秒")
        return result
    
    @staticmethod
    def to_srt_format(segments: List[Dict]) -> str:
        """转换为SRT字幕格式
        
        Args:
            segments: 分段数据
            
        Returns:
            str: SRT格式字幕
        """
        logger.info("转换为SRT字幕格式")
        
        srt_lines = []
        for i, segment in enumerate(segments, 1):
            if not segment.get('text') or segment.get('start') is None:
                continue
            
            # 转换微秒为时间格式
            start_time_us = segment['start']
            duration_us = segment.get('duration', 0)
            end_time_us = start_time_us + duration_us
            
            start_time = OutputFormatter._microseconds_to_srt_time(start_time_us)
            end_time = OutputFormatter._microseconds_to_srt_time(end_time_us)
            
            srt_lines.append(str(i))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(segment['text'])
            srt_lines.append("")  # 空行分隔
        
        srt_content = "\n".join(srt_lines)
        logger.info(f"SRT字幕生成完成，行数: {len(srt_lines)}")
        return srt_content
    
    @staticmethod
    def to_json_format(segments: List[Dict], indent: int = 2) -> str:
        """转换为JSON格式
        
        Args:
            segments: 分段数据
            indent: JSON缩进
            
        Returns:
            str: JSON格式字符串
        """
        logger.info("转换为JSON格式")
        
        json_data = {
            "segments": segments,
            "total_segments": len(segments),
            "timestamp": time.time()
        }
        
        json_content = json.dumps(json_data, ensure_ascii=False, indent=indent)
        logger.info(f"JSON格式生成完成，字符数: {len(json_content)}")
        return json_content
    
    @staticmethod
    def _microseconds_to_srt_time(microseconds: int) -> str:
        """将微秒转换为SRT时间格式 (HH:MM:SS,mmm)
        
        Args:
            microseconds: 微秒
            
        Returns:
            str: SRT时间格式字符串
        """
        total_seconds = microseconds // 1_000_000
        milliseconds = (microseconds % 1_000_000) // 1_000
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
