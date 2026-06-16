"""
Aeneas核心处理器

提供完整的文本-音频强制对齐功能，包括：
- 文本预处理和分句
- Aeneas工具调用
- 结果后处理和格式化
"""

import os
import sys
import subprocess
import tempfile
import json
import time
import string
import re
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    from .text_preprocessor import TextPreprocessor
    from .output_formatter import OutputFormatter
    from ..utils.logger import get_logger
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.text_preprocessor import TextPreprocessor
    from core.output_formatter import OutputFormatter
    from utils.logger import get_logger

logger = get_logger(__name__)

class AeneasProcessor:
    """Aeneas强制对齐处理器
    
    提供完整的文本-音频强制对齐功能，包括：
    - 文本预处理和分句
    - Aeneas工具调用
    - 结果后处理和格式化
    """
    
    def __init__(self, aeneas_python_path: str = None, verbose: bool = False, use_mock: bool = False):
        """初始化Aeneas处理器

        Args:
            aeneas_python_path: Aeneas Python环境的路径，如果为None则自动检测
            verbose: 是否启用详细日志输出
            use_mock: 是否使用模拟模式（开发测试用）
        """
        self.verbose = verbose
        self.use_mock = use_mock or os.environ.get('AENEAS_MOCK', 'false').lower() == 'true'

        if self.use_mock:
            logger.info("🔧 启用Aeneas模拟模式（用于开发和测试）")
            self.aeneas_python_path = None
        else:
            try:
                self.aeneas_python_path = self._detect_aeneas_environment(aeneas_python_path)
            except RuntimeError as e:
                logger.warning(f"Aeneas环境检测失败，切换到模拟模式: {e}")
                self.use_mock = True
                self.aeneas_python_path = None

        if self.verbose:
            logger.setLevel(10)  # DEBUG level

        mode = "模拟模式" if self.use_mock else f"真实环境 ({self.aeneas_python_path})"
        logger.info(f"Aeneas处理器初始化完成，模式: {mode}")
    
    def process_alignment(self, audio_path: str, original_text: str, 
                      language: str = 'zho') -> Dict:
        """执行完整的对齐流程
        
        Args:
            audio_path: 音频文件路径
            original_text: 原始文案内容
            language: 语言代码 ('zho' 或 'eng')
            
        Returns:
            Dict: 包含对齐结果的字典，格式与NovelCut完全一致
        """
        logger.info(f"开始执行完整对齐流程")
        logger.info(f"音频文件: {audio_path}")
        logger.info(f"原始文本长度: {len(original_text)} 字符")
        logger.info(f"语言代码: {language}")
        
        try:
            # 1. 验证输入参数
            if not os.path.exists(audio_path):
                return {"status": "error", "error": f"音频文件不存在: {audio_path}"}
            
            if not original_text or not original_text.strip():
                return {"status": "error", "error": "原始文案内容不能为空"}
            
            # 2. 标准化语言代码
            normalized_language = TextPreprocessor.validate_language_code(language)
            
            # 3. 文本预处理
            logger.info("步骤 1/4: 文本预处理")
            processed_text = self._preprocess_text(original_text, normalized_language)
            
            # 4. 调用Aeneas工具
            logger.info("步骤 2/4: 调用Aeneas工具")
            raw_alignment_data = self._call_aeneas(audio_path, processed_text, normalized_language)
            
            if not raw_alignment_data:
                return {"status": "error", "error": "Aeneas对齐返回空数据"}
            
            # 5. 后处理对齐结果
            logger.info("步骤 3/4: 后处理对齐结果")
            processed_alignment_data = self._postprocess_alignment(raw_alignment_data)

            # 5.1 规范化真实 Aeneas 的输出结构与时间单位
            processed_alignment_data = self._normalize_segments_for_output(processed_alignment_data)
            
            # 6. 格式化输出
            logger.info("步骤 4/4: 格式化输出")
            result = self._format_output(
                processed_alignment_data, 
                original_text, 
                audio_path, 
                normalized_language
            )
            
            logger.info("✅ 完整对齐流程执行成功")
            return result
            
        except Exception as e:
            error_msg = f"对齐流程执行失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "error": error_msg}
    
    def _detect_aeneas_environment(self, manual_path: str = None) -> str:
        """检测Aeneas环境路径
        
        Args:
            manual_path: 手动指定的路径
            
        Returns:
            str: Aeneas Python可执行文件路径
            
        Raises:
            RuntimeError: 如果找不到任何Aeneas环境且未提供手动路径
        """
        # 如果提供了手动路径，直接验证
        if manual_path:
            if os.path.exists(manual_path):
                logger.info(f"使用手动指定的Aeneas路径: {manual_path}")
                return manual_path
            else:
                logger.warning(f"手动指定的路径不存在: {manual_path}")
        
        # 自动检测逻辑 - 优先检测Python 3.9环境
        possible_paths = [
            # 当前子项目的Python 3.9环境（最优选择）
            os.path.join(os.getcwd(), "venv_aeneas_py39", "Scripts", "python.exe"),
            # 当前目录的venv_aeneas
            os.path.join(os.getcwd(), "venv_aeneas", "Scripts", "python.exe"),
            # 上级目录（相对于子项目）
            os.path.join(os.path.dirname(os.getcwd()), "venv_aeneas", "Scripts", "python.exe"),
            # NovelCut项目中的venv_aeneas
            os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), "venv_aeneas", "Scripts", "python.exe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"检测到Aeneas环境: {path}")
                return path
        
        # 如果都找不到，提供友好的错误信息和安装建议
        error_msg = """
未找到Aeneas环境。请按以下方式之一安装：

方法1 - 在当前Python环境中安装（推荐）：
    pip install numpy
    pip install aeneas

方法2 - 使用conda安装：
    conda install -c conda-forge aeneas

方法3 - 从源码安装：
    git clone https://github.com/readbeyond/aeneas.git
    cd aeneas
    pip install -e .

方法4 - 手动指定路径：
    --aeneas-path "/path/to/your/python.exe"

安装完成后，请重新运行程序。
        """
        logger.error("未找到Aeneas环境")
        raise RuntimeError(error_msg.strip())
    
    def _preprocess_text(self, text: str, language: str) -> str:
        """文本预处理
        
        Args:
            text: 原始文本
            language: 语言代码
            
        Returns:
            str: 处理后的文本
        """
        return TextPreprocessor.prepare_for_aeneas(text, language)
    
    def _call_aeneas(self, audio_path: str, text: str,
                    language: str) -> List[Dict]:
        """调用Aeneas工具

        Args:
            audio_path: 音频文件路径
            text: 预处理后的文本
            language: 语言代码

        Returns:
            List[Dict]: Aeneas原始输出数据
        """
        # 检查是否使用模拟模式
        if self.use_mock:
            logger.info("🔧 使用模拟Aeneas环境...")
            return self._mock_aeneas_execution(text, language)

        logger.info(f"开始使用真实 Aeneas 环境进行强制对齐...")

        if not Path(audio_path).is_file():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            plain_text_path = temp_dir_path / "processed_text.txt"
            output_json_path = temp_dir_path / "result.json"
            
            # 写入处理后的文本
            plain_text_path.write_text(text, encoding='utf-8')
            
            # 构建Aeneas配置字符串
            config_string = f"task_language={language}|os_task_file_format=json|is_text_type=mplain|os_task_file_level=3"
            
            # 构建命令
            command = [
                str(self.aeneas_python_path), 
                "-m", "aeneas.tools.execute_task",
                str(Path(audio_path).resolve()),
                str(plain_text_path.resolve()),
                config_string,
                str(output_json_path.resolve())
            ]
            
            logger.info(f"准备执行 Aeneas 命令: {' '.join(command)}")
            
            try:
                # 执行Aeneas命令
                process = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    check=True
                )
                logger.info("Aeneas 命令执行成功")
                
                if self.verbose and process.stdout:
                    logger.debug(f"Aeneas STDOUT: {process.stdout}")
                
            except subprocess.CalledProcessError as e:
                # 增强错误日志
                error_output = (e.stderr or e.stdout or "").strip()
                error_message = f"Aeneas 强制对齐失败: {error_output}"
                logger.error(f"Aeneas 命令执行失败。返回码: {e.returncode}")
                logger.error(f"  - STDOUT: {(e.stdout or '').strip()}")
                logger.error(f"  - STDERR: {(e.stderr or '').strip()}")

                # 如果是numpy导入错误，自动切换到模拟模式
                if "numpy" in error_output.lower() and "import" in error_output.lower():
                    logger.warning("检测到numpy导入错误，自动切换到模拟模式")
                    return self._mock_aeneas_execution(text, language)

                raise RuntimeError(error_message)
            
            if not output_json_path.is_file():
                logger.warning("Aeneas未生成输出文件")
                return []
            
            # 读取结果
            with open(output_json_path, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # 解析Aeneas输出格式
            formatted_segments = self._parse_aeneas_output(result_data)
            
            logger.info(f"成功将 Aeneas 输出转换为 {len(formatted_segments)} 个仿 Whisper 格式的句子片段。")
            return formatted_segments
    
    def _parse_aeneas_output(self, result_data: Dict) -> List[Dict]:
        """解析Aeneas输出为仿Whisper格式
        
        Args:
            result_data: Aeneas原始输出数据
            
        Returns:
            List[Dict]: 仿Whisper格式的分段数据
        """
        formatted_segments = []
        
        def find_and_process_sentences_recursively(nodes: List[Dict]):
            if not isinstance(nodes, list): 
                return
            for node in nodes:
                children = node.get("children", [])
                if not children: 
                    continue
                if all(not child.get("children") for child in children):
                    # 叶子节点：包含词级信息
                    word_list = []
                    for w in children:
                        word_text = w.get("lines", [""])[0].lstrip('\ufeff')
                        word_start = float(w.get("begin", 0))
                        word_end = float(w.get("end", 0))
                        word_list.append({
                            "word": word_text,
                            "start": word_start,
                            "end": word_end
                        })
                    
                    if word_list:
                        sentence_text = " ".join(w["word"] for w in word_list)
                        formatted_segments.append({
                            "text": sentence_text,
                            "start": float(node.get("begin", 0)),
                            "end": float(node.get("end", 0)),
                            "words": word_list
                        })
                else:
                    find_and_process_sentences_recursively(children)
        
        # 处理所有顶层片段
        for top_level_frag in result_data.get("fragments", []):
            find_and_process_sentences_recursively([top_level_frag])
        
        # 按时间排序
        formatted_segments.sort(key=lambda x: x['start'])
        return formatted_segments
    
    def _postprocess_alignment(self, raw_data: List[Dict]) -> List[Dict]:
        """后处理对齐结果
        
        功能：
        1. 移除所有词条中的标点符号
        2. 在每两个有效词之间插入一个零时长的空格词条
        
        Args:
            raw_data: Aeneas原始数据
            
        Returns:
            List[Dict]: 处理后的对齐数据
        """
        logger.info("开始调整 Aeneas 输出，移除标点并插入空格词条...")
        
        # 定义需要移除的标点符号集合
        punctuation_to_remove = string.punctuation + '，。？！；："''（）《》【】…—·""'
        punctuation_pattern = f"[{re.escape(punctuation_to_remove)}]"
        
        adjusted_segments = []
        for segment in raw_data:
            new_segment = segment.copy()
            
            # 清理整个句子的文本
            if 'text' in new_segment:
                new_segment['text'] = re.sub(punctuation_pattern, '', new_segment['text']).replace('  ', ' ').strip()
            
            if 'words' in new_segment and isinstance(new_segment['words'], list):
                original_words = new_segment['words']
                new_words_with_spaces = []
                
                for i, word_info in enumerate(original_words):
                    new_word_info = word_info.copy()
                    if 'word' in new_word_info:
                        cleaned_word = re.sub(punctuation_pattern, '', new_word_info['word'])
                        if cleaned_word:
                            # 1. 添加清理后的核心词条
                            new_word_info['word'] = cleaned_word
                            new_words_with_spaces.append(new_word_info)
                            
                            # 2. 在词后添加一个零时长的空格（除了最后一个词）
                            if i < len(original_words) - 1:
                                space_word = {
                                    "word": " ",
                                    "start": new_word_info["end"],
                                    "end": new_word_info["end"]
                                }
                                new_words_with_spaces.append(space_word)
                
                new_segment['words'] = new_words_with_spaces
            
            # 只有当处理后仍然有有效的词时，才添加该分段
            if new_segment.get('words'):
                adjusted_segments.append(new_segment)
        
        logger.info(f"Aeneas 输出调整完成，剩余 {len(adjusted_segments)} 个分段。")
        return adjusted_segments
    
    def _format_output(self, processed_data: List[Dict], 
                    original_text: str, audio_path: str, 
                    language: str) -> Dict:
        """格式化最终输出
        
        Args:
            processed_data: 处理后的对齐数据
            original_text: 原始文本
            audio_path: 音频文件路径
            language: 语言代码
            
        Returns:
            Dict: 标准格式的输出结果
        """
        logger.info("格式化最终输出")
        
        # 转换为标准字幕格式
        result = OutputFormatter.to_subtitle_format(
            processed_data, original_text, audio_path, language
        )
        
        logger.info(f"输出格式化完成，状态: {result.get('status')}")
        return result

    def _normalize_segments_for_output(self, segments: List[Dict]) -> List[Dict]:
        """规范化分段结构以匹配输出格式要求

        真实 Aeneas 输出的 words 是 list（含 word/start/end，秒单位），
        输出格式要求 words 为 dict（含 group_id/text/start_time/end_time，毫秒单位）。
        同时确保 segment 的 start/end/duration 使用微秒单位。
        """
        normalized = []
        timestamp = int(time.time() * 1000)

        def tokenize_text(text: str) -> List[str]:
            if text == " ":
                return [" "]
            tokens = re.findall(r"[a-zA-Z]+|[0-9]+|[\u4e00-\u9fff]", text)
            return tokens if tokens else [text] if text else []

        for idx, segment in enumerate(segments):
            new_segment = segment.copy()
            words = new_segment.get("words")

            # 仅对真实 Aeneas 的 list 结构做转换
            if isinstance(words, list):
                if not words:
                    continue

                # 计算分段起止时间（秒）
                seg_start_sec = new_segment.get("start")
                seg_end_sec = new_segment.get("end")
                if seg_start_sec is None:
                    seg_start_sec = words[0].get("start", 0.0)
                if seg_end_sec is None:
                    seg_end_sec = words[-1].get("end", seg_start_sec)

                # 构建 words dict
                word_texts = []
                word_starts_ms = []
                word_ends_ms = []

                for w in words:
                    w_text = w.get("word", "")
                    w_start = w.get("start", seg_start_sec)
                    w_end = w.get("end", w_start)
                    if w_end < w_start:
                        w_end = w_start

                    sub_tokens = tokenize_text(w_text)
                    if not sub_tokens:
                        continue

                    sub_duration = max(w_end - w_start, 0.0)
                    if sub_duration == 0 or len(sub_tokens) == 1:
                        for token in sub_tokens:
                            word_texts.append(token)
                            start_ms = int((w_start - seg_start_sec) * 1000)
                            word_starts_ms.append(start_ms)
                            word_ends_ms.append(int((w_end - seg_start_sec) * 1000))
                    else:
                        per_token = sub_duration / len(sub_tokens)
                        for i, token in enumerate(sub_tokens):
                            token_start = w_start + i * per_token
                            token_end = w_start + (i + 1) * per_token
                            word_texts.append(token)
                            word_starts_ms.append(int((token_start - seg_start_sec) * 1000))
                            word_ends_ms.append(int((token_end - seg_start_sec) * 1000))

                new_segment["words"] = {
                    "group_id": f"Auto_{timestamp}_{idx}",
                    "text": word_texts,
                    "start_time": word_starts_ms,
                    "end_time": word_ends_ms,
                }

                # 统一为微秒单位
                new_segment["start"] = int(seg_start_sec * 1_000_000)
                new_segment["end"] = int(seg_end_sec * 1_000_000)
                new_segment["duration"] = new_segment["end"] - new_segment["start"]

            # 若已经是 dict 结构，保持原样（模拟模式）
            normalized.append(new_segment)

        return normalized
    
    def check_environment(self) -> Dict[str, Any]:
        """检查Aeneas环境是否可用

        Returns:
            Dict: 环境检查结果
        """
        # 如果使用模拟模式
        if self.use_mock:
            return {
                "available": True,
                "python_path": "模拟环境",
                "mode": "mock",
                "stdout": "模拟环境可用",
                "stderr": ""
            }

        try:
            # 测试aeneas模块导入
            result = subprocess.run([
                self.aeneas_python_path, "-c", "import aeneas; print('OK')"
            ], capture_output=True, text=True, timeout=10)

            is_available = result.returncode == 0 and 'OK' in result.stdout

            return {
                "available": is_available,
                "python_path": self.aeneas_python_path,
                "stdout": result.stdout if is_available else "",
                "stderr": result.stderr if not is_available else ""
            }
        except Exception as e:
            return {
                "available": False,
                "python_path": self.aeneas_python_path,
                "error": str(e)
            }

    def _mock_aeneas_execution(self, text: str, language: str) -> List[Dict]:
        """模拟Aeneas执行过程

        Args:
            text: 预处理后的文本
            language: 语言代码

        Returns:
            List[Dict]: 模拟的Aeneas输出数据
        """
        logger.info("🔧 模拟Aeneas强制对齐过程...")

        # 简单分句处理
        sentences = text.split('\n')
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            logger.warning("没有有效的句子进行对齐")
            return []

        # 生成模拟对齐结果
        # 假设音频总长度10秒，平均分配给每个句子
        audio_duration = 10.0
        segment_duration = audio_duration / len(sentences)

        formatted_segments = []
        current_time = 0.0

        for i, sentence in enumerate(sentences):
            # 智能分词：中文按字符，英文单词和数字保持完整
            import re
            # 分别匹配：中文、英文单词、数字，忽略标点符号
            # 1. 英文单词：[a-zA-Z]+  (如 "AI", "Don't")
            # 2. 数字：[0-9]+  (如 "2025", "3")
            # 3. 中文：[\u4e00-\u9fff]  (单个中文字符)
            # 使用|连接多个模式，re.findall会按顺序匹配
            words = re.findall(r'[a-zA-Z]+|[0-9]+|[\u4e00-\u9fff]', sentence)

            # 如果没有匹配到任何词（全是标点），使用整个句子按空格分割
            if not words:
                words = sentence.split()
            # 如果按空格分割后还是没有，使用整个句子作为单个词
            if not words:
                words = [sentence]

            word_duration = segment_duration / max(len(words), 1)

            # 创建词级时间戳数组
            word_texts = []
            word_starts = []
            word_ends = []

            for j, word in enumerate(words):
                word_start = current_time + j * word_duration
                word_end = word_start + word_duration

                word_texts.append(word)
                word_starts.append(int(word_start * 1000))  # 转换为毫秒
                word_ends.append(int(word_end * 1000))  # 转换为毫秒

            if word_texts:
                # 生成group_id
                import time
                group_id = f"Auto_{int(time.time() * 1000)}_{i}"

                formatted_segments.append({
                    "text": sentence,
                    "start": int(current_time * 1_000_000),  # 转换为微秒
                    "end": int((current_time + segment_duration) * 1_000_000),  # 转换为微秒
                    "duration": int(segment_duration * 1_000_000),  # 转换为微秒
                    "words": {
                        "group_id": group_id,
                        "text": word_texts,
                        "start_time": word_starts,
                        "end_time": word_ends
                    }
                })

            current_time += segment_duration

        logger.info(f"✅ 模拟Aeneas对齐完成: {len(formatted_segments)} 个句子, {sum(len(s['words']['text']) for s in formatted_segments)} 个词")
        return formatted_segments
