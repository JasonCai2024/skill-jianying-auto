# Module Map

## 核心入口
- 总控入口：`scripts/run_pipeline.py`
- 对齐入口：`scripts/align.py` -> `aligner/core/servicehub_asr_processor.py::ServiceHubASRProcessor.process`
- 分镜入口：`scripts/parse_storyboard_md.py` -> `parse_storyboard(md_path, attachments_dir_name="attachments")`
- 解析入口：`utility/draft_parser.py::parse_draft_folder(draft_folder_path, output_path=None)`
- 合成入口：`utility/draft_config_comb.py::execute_draft_composition_workflow(draft_para_collect_path)`
- 编排类：`utility/draft_para_collect.py::DraftParaCollect`
- 校验入口：`utility/draft_config_comb_check.py::check_draft_output(input_param_file, draft_folder, raise_on_error=True)`

## 合成主链路
- `DraftConfigComb.execute_draft_composition()`
- `create_complete_simplified_content.py` 负责拼 top-level / materials / tracks
- `complete_materials_builder.py` 负责 materials.*
- `complete_tracks_builder_fixed.py` 负责 tracks + segments

## 映射
- `draft_config_utility.py`
- `load_font_name_map / resolve_font_by_title`
- `load_audio_name_map`
- `load_animation_map`

## 对齐模块
- `aligner/core/text_preprocessor.py`：文案清洗与分句
- `aligner/core/servicehub_asr_processor.py`：ServiceHub ASR / LLM 调度与字幕时间轴生成
- `aligner/core/output_formatter.py`：输出 JSON/SRT

## 配置入口
- `scripts/skill_config.py`：加载 `config.json`、`.env`、`data/credentials.json`
- 凭证优先级：显式配置 > 环境变量 / `.env` > `data/credentials.json`

## 数据结构要点
- `canvas`: `id/width/height/duration/source_draft_fold_path/jianying_folder_path/output_parent_draft_folder_path`
- `videos[].tracks`: `id/track_render_index/segments_id/start/duration/scale_x/scale_y/transform_x/transform_y/common_keyframes/material_animations`
- `texts[].tracks`: 同视频，额外 `text_alpha`
- `audios[].tracks`: `id/segments_id/track_render_index/start/segment_duration/volume`
- `tracks`: `video_track/texts_track/audios_track`（每项至少 `id + track_render_index`）
