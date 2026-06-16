"""
文本预处理器

负责文本的清理、分句和格式化，为Aeneas处理做准备
"""

import re
import os
import string
from typing import List

try:
    from ..utils.logger import get_logger
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from utils.logger import get_logger

logger = get_logger(__name__)

class TextPreprocessor:
    """文本预处理器
    
    负责文本的清理、分句和格式化，为Aeneas处理做准备
    """
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本中的特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        logger.debug(f"清理文本前: {repr(text)}")
        
        # 移除BOM标记
        text = text.lstrip('\ufeff')
        
        # 标准化引号
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('"', '"').replace('"', '"')
        
        # 标准化破折号
        text = text.replace('—', '-').replace('…', '...')
        
        logger.debug(f"清理文本后: {repr(text)}")
        return text
    
    @staticmethod
    def split_sentences(text: str, language: str) -> List[str]:
        """按语言分句
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            List[str]: 分句后的列表
        """
        logger.debug(f"分句处理 - 语言: {language}, 文本: {repr(text)}")
        
        if language == 'eng':
            # 英文分句：基于标点符号和空格
            sentences = re.split(r'(?<=[.?!])\s+', text.strip())
        elif language == 'zho':
            # 中文分句优化：
            # 1) 优先保留用户输入中的换行（通常更接近口播节奏）
            # 2) 仅当没有换行时再按句号问号感叹号切分
            lines = [x.strip() for x in text.splitlines() if x.strip()]
            if len(lines) > 1:
                sentences = lines
            else:
                text2 = text.replace('。', '.').replace('？', '?').replace('！', '!')
                sentences = re.sub(r'([.?!])', r'\1\n', text2).splitlines()
        else:
            # 其他语言：通用分句规则
            sentences = re.split(r'(?<=[.?!])\s+', text.strip())
        
        # 清理每个句子并过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        logger.debug(f"分句结果: {sentences}")
        return sentences
    
    @staticmethod
    def merge_short_sentences(sentences: List[str], min_chars: int) -> List[str]:
        """合并过短句子，降低Aeneas过细切分带来的抖动。"""
        if min_chars <= 1 or not sentences:
            return sentences
        merged: List[str] = []
        buf = ""
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if not buf:
                buf = s
                continue
            if len(buf) < min_chars:
                buf = f"{buf}{s}"
            else:
                merged.append(buf)
                buf = s
        if buf:
            if merged and len(buf) < max(4, min_chars // 2):
                merged[-1] = f"{merged[-1]}{buf}"
            else:
                merged.append(buf)
        return merged

    @staticmethod
    def get_sentence_merge_min_chars() -> int:
        raw = os.environ.get("AENEAS_SENTENCE_MERGE_MIN_CHARS", "0").strip()
        try:
            v = int(raw)
        except ValueError:
            v = 0
        return max(0, v)

    @staticmethod
    def prepare_for_aeneas(text: str, language: str) -> str:
        """为Aeneas准备文本格式
        
        Args:
            text: 原始文本
            language: 语言代码
            
        Returns:
            str: Aeneas格式的文本
        """
        logger.info(f"为Aeneas预处理文本 (语言: {language})...")
        
        # 1. 清理文本
        cleaned_text = TextPreprocessor.clean_text(text)
        
        # 2. 按语言分句
        if language == 'eng':
            # 英文：移除非ASCII字符后分句
            cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_text)
            sentences = re.split(r'(?<=[.?!])\s+', cleaned_text.strip())
        elif language == 'zho':
            # 中文：优先保留输入换行的节奏，避免过度切分导致长音频累积漂移
            sentences = TextPreprocessor.split_sentences(cleaned_text, language)
        else:
            # 其他语言：通用分句
            sentences = TextPreprocessor.split_sentences(cleaned_text, language)
        
        # 3. 过滤空句子并重新组合
        sentences = [s.strip() for s in sentences if s.strip()]
        min_chars = TextPreprocessor.get_sentence_merge_min_chars()
        if language == 'zho' and min_chars > 1:
            before = len(sentences)
            sentences = TextPreprocessor.merge_short_sentences(sentences, min_chars)
            logger.info(f"中文短句合并: {before} -> {len(sentences)} (min_chars={min_chars})")

        result = "\n".join(sentences)
        logger.info(f"已将文本净化并拆分为 {len(sentences)} 个句子。")
        return result
    
    @staticmethod
    def validate_language_code(language: str) -> str:
        """验证并标准化语言代码
        
        Args:
            language: 输入的语言代码
            
        Returns:
            str: 标准化的语言代码
        """
        language_mapping = {
            'zh': 'zho',
            'cn': 'zho',
            'chinese': 'zho',
            'en': 'eng',
            'english': 'eng'
        }
        
        normalized_lang = language_mapping.get(language.lower(), language.lower())
        
        if normalized_lang not in ['zho', 'eng']:
            logger.warning(f"未识别的语言代码: {language}, 使用默认值 'zho'")
            return 'zho'
        
        logger.debug(f"语言代码标准化: {language} -> {normalized_lang}")
        return normalized_lang
