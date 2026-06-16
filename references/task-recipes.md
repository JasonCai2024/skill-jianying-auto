# Task Recipes

## Recipe A: 一键生成剪映草稿
1. 输入：一篇包含 `## 口播文案` 和 `## 口播文案分镜设计` 的 Markdown，以及对应配音音频。
2. 要求：Markdown 同级默认存在 `attachments/` 目录，存放引用图片。
3. 调用 `python scripts/run_pipeline.py --md-path "<md>" --audio-path "<audio>"`。
4. 检查输出：
   - `output/storyboard_sequence.json`
   - `output/aligned_asr.json`
   - 剪映草稿目录

## Recipe 1: 反向解析草稿
1. 输入：剪映草稿目录（含 `draft_content.json` / `draft_meta_info.json`）。
2. 调用 `parse_draft_folder` 生成参数对象或参数 JSON。
3. 检查 `canvas.duration`、`tracks` 分组数量、`videos/texts/audios` 数量。

## Recipe 0: 文案配音对齐
1. 输入：口播文案 `txt` + 对应配音音频 `mp3/wav`。
2. 调用 `scripts/align.py`，输出 `aligned_*.json` 与 `aligned_*.srt`。
3. 默认通过 ServiceHub OSS 代理上传音频，再调用 ServiceHub ASR 获取字级时间戳。

## Recipe 0.5: 分镜 Markdown 解析（图片序列）
1. 输入：包含 `## 口播文案分镜设计` 章节的 md 文件。
2. 要求：图片引用格式固定 `![[xxx.png]]`，图片位于 md 同级 `attachments/`；若仅存在 `Attachments/`，按兼容模式处理。
3. 调用 `scripts/parse_storyboard_md.py` 生成 `storyboard_sequence_*.json`。
4. 输出项包含：`index/narration/prompt/image_rel_path/image_abs_path/image_exists`。

## Recipe 2: 参数合成草稿
1. 输入：参数 JSON 路径。
2. 调用 `execute_draft_composition_workflow` 返回草稿目录。
3. 立即运行 `check_draft_output`。

## Recipe 3: 手工编排并合成
1. 用 `DraftParaCollect` 创建 canvas + tracks。
2. 添加视频/文字/音频片段，必要时添加关键帧和动画。
3. `close_canvas` 输出参数文件。
4. 调用合成入口并校验。

## Recipe 5: 反向解析现有剪映草稿
1. 输入：现有剪映草稿目录。
2. 调用 `scripts/parse.py` 导出参数 JSON。
3. 检查 `canvas`、`tracks`、`videos/texts/audios` 是否完整。

## Recipe 6: Roundtrip 校验
1. 输入：现有剪映草稿目录。
2. 调用 `scripts/roundtrip.py` 执行 parse -> compose -> validate。
3. 若失败，继续用 `scripts/validate.py` 和 `utility/draft_config_comb_check.py` 定位差异。

## Recipe 7: 对齐质量评估
1. 输入：`aligned_asr.json` 与参考 `SRT`。
2. 调用 `scripts/evaluate_alignment.py`。
3. 关注 `p50/p90/max` 的开始、结束和时长误差。

## Recipe 4: 映射不命中排查
1. 字体：检查 `fonts_title` 与 `font_name_map.json` 键名是否一致。
2. 音频：检查 `name.lower()` 是否存在于 `audio_name_map.json`。
3. 动画：检查 `material_type + category_id + name` 是否存在于 `animation_map.json`。
4. 对齐异常：优先检查 `output/asr_mid/06_symbol_split_lines.json`、`08_rechunk_lines.json`、`12_aligned_segments.json`。
