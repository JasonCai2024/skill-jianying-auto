# 自动化剪辑技能包设计文档

- 项目名称：`skill-jianying-auto`
- 文档版本：`v1.7`
- 最后更新：`2026-06-16`
- 适用实现：当前 `scripts/`、`aligner/core/`、`utility/` 代码

## 1. 目标与范围
- 目标：输入分镜 Markdown 与配音音频，自动生成可打开编辑的剪映草稿。
- 范围：分镜解析 -> ASR 字幕对齐 -> 剪辑编排 -> 剪辑合成。
- 主方案：ServiceHub ASR（`fun-asr`）字级时间戳 + 文案约束纠错 + 符号断句 + 长句切分 + 草稿自动生成。
- 约束：技能侧不再直接持有阿里云 OSS `Bucket/AK/SK/Region`，统一改为调用 ServiceHub 暴露的 OSS 代理接口。

## 2. 整体业务流程
```text
[输入]
  分镜.md + attachments/* + audio.mp3
      |
      v
(1) 分镜 Markdown 解析子技能
  - 解析 ## 口播文案
  - 解析 ## 口播文案分镜设计
  - 产出口播文案文本 + 分镜序列JSON
      |
      v
(2) ASR 字幕对齐子技能
  - 通过 ServiceHub OSS 代理上传音频 -> ServiceHub ASR 字级时间戳(fun-asr)
  - LLM纠错(仅纠错，不加标点/分段)
  - 符号断句 + 长句切分 + LCS时序映射
  - 产出 aligned json/srt
      |
      v
(3) 剪辑编排子技能
  - 字幕轨直接使用 aligned segments 时间戳
  - 图片轨按分镜叙述匹配到字幕段区间
  - 根据模板注入额外文字轨样式
  - 产出 draft_para_collect 参数文件
      |
      v
(4) 剪辑合成子技能
  - 参数文件 -> draft_content/meta + 草稿目录
  - 路径修正（素材绝对路径可用）
      |
      v
[输出]
  D:/JianyingPro Drafts/<draft_id>
```

## 3. 子技能设计与执行顺序

### 3.1 子技能A（第1步）：分镜 Markdown 解析
- 入口：`python scripts/parse_storyboard_md.py --md-path <md路径> [--output-json <路径>] [--output-script <路径>]`
- 解析章节：
- `## 口播文案`：输出纯文本口播文案（供 ASR 对齐使用）
- `## 口播文案分镜设计`：输出图片分镜序列
- 图片引用格式：`![[xxx.png]]`，图片目录固定为同级 `attachments/` 或 `Attachments/`
- 剪辑注规则：`> [剪辑注开始] ... > [剪辑注结束]` 输出为 `black_note` 项

默认输出约定（未指定输出参数）：
- `output/storyboard_sequence.json`
- `output/script_text.txt`

### 3.2 子技能B（第2步）：ASR 字幕对齐
- 入口：`python scripts/align.py --audio <音频> [--text-file <文案>] [--output-json <路径>] [--output-srt <路径>] [--subtitle-max-chars <N>]`
- 默认输入回退：
- 未指定 `--text-file` 时，默认读取子技能A输出：`output/script_text.txt`
- 默认输出约定（未指定输出参数）：
- `output/aligned_asr.json`
- `output/aligned_asr.srt`

流程说明：
1. 调 ServiceHub `/api/oss/upload-audio` 上传音频，换取公网 `oss_url`。
2. 调 `/api/asr/paid-rotation`（`transcript_format=word_timestamps`）获取字级时序。
3. 调 `/api/llm/paid-rotation`做纠错：仅纠错，不增删词，不加标点/换行。
4. 按口播文案符号固定断句。
5. 仅对超长句调用 LLM 切分，失败时回退确定性切分。
6. LCS 映射回 ASR 时轴，生成短句级 `segments`。
7. 在 `finally` 中调 ServiceHub `/api/oss/delete-audio` 删除上传对象。

关键实现约束（已固化）：
- 草稿字幕直接使用 `aligned segments` 时间戳，不再二次拆分重分配时长。
- 长句 LLM 切分结果必须通过强校验（仅允许切分，不允许丢字/改序/增字；且每段不超阈值），否则自动回退。

### 3.3 子技能C（第3步）：剪辑编排
- 入口：
- `python scripts/compose_from_assets.py --audio-path <音频> [--aligned-json <路径>] [--storyboard-json <路径>] [--template-id <模板>] [--save-params <路径>]`
- 输入项（固定约定）：
- 字幕输入：`output/aligned_asr.json`（可被 `--aligned-json` 覆盖）
- 分镜输入：`output/storyboard_sequence.json`（可被 `--storyboard-json` 覆盖）
- 音频输入：命令行 `--audio-path`
- 输出项：
- `output/draft_para_collect_from_assets.json`（可被 `--save-params` 覆盖）
- `output/image_timeline_from_storyboard.json`
- `output/subtitle_timeline_display.json`

编排原则：
- 字幕轨：直接使用 ASR 短句时间轴。
- 图片轨：按分镜 `narration` 匹配到字幕区间（可一图多句）。
- 图片开始时间：默认取区间首句开始时间；仅第一张图片强制从 `0.0s` 开始。
- 图片结束时间：下一图片开始时间（最后一张到音频末尾）。
- 额外文字轨：支持模板注入（如片头免责声明），支持像素坐标自动换算到剪映坐标系。

### 3.4 子技能D（第4步）：剪辑合成
- 执行：`DraftConfigComb.execute_draft_composition(...)`
- 输入：`draft_para_collect`
- 输出：草稿目录（`draft_content.json`、`draft_meta_info.json` 等）
- 草稿根目录：`config.json.draft_parent_folder`（当前 `D:/JianyingPro Drafts`）

## 4. 模板化控制（已实现）
- 模板目录：`user_data/templates/`
- 已有模板：
- `template1.json`：基础模板（图片不缩放）
- `template2.json`：图片缩放 + 片头额外文字轨（参考样例草稿）
- 模板选择：`--template-id template1|template2`
- 覆盖优先级：`CLI参数 > 模板文件 > config.json > 代码默认值`

### 4.1 template2 片头额外文字轨关键参数
- 时间与位置：
- `start=0.0`
- `duration=6.0`
- `transform_x_px=-1050`
- `transform_y_px=-836`
- `scale_x=0.7`
- `scale_y=0.7`
- 字体与描边：
- `font_title=新青年体`
- `font_size=7`
- `text_color=#000000`
- `border_color=#FFFFFF`
- `border_width=40`
- 混合与背景：
- `global_alpha=0.9`（混合不透明度 90%）
- `check_flag=31`（背景样式生效关键位）
- `background_style=1`
- `background_color=#FFFFFF`
- `background_round_radius=0.4`（40%）
- `background_width=0.0`（0%）
- `background_height=0.0`（0%）

## 5. 配置与敏感信息
- 技能配置：`skill-jianying-auto/config.json`
- 本地凭证回退：`skill-jianying-auto/data/credentials.json`
- 配置优先级：显式配置 > 环境变量 / `.env` > `data/credentials.json` > `config.json`
- 关键项：
- `draft_parent_folder`
- `default_template_id`
- `subtitle_style_sample_draft`
- `black_material.path`
- `servicehub.*`（当前 `asr_model=fun-asr`）
- `defaults.parse_storyboard.*`、`defaults.align.*`、`defaults.compose.*`（推荐维护默认参数）

当前敏感配置要求：
- 只要求 `servicehub.base_url`、`servicehub.username`、`servicehub.passtoken`
- OSS 的 `bucket/region/AK/SK` 固定保存在 ServiceHub 服务端，不再由技能使用者配置

## 6. 固定产物路径约定
- `output/script_text.txt`：口播文案（由分镜解析产出）
- `output/storyboard_sequence.json`：分镜序列（由分镜解析产出）
- `output/aligned_asr.json`：ASR对齐主结果
- `output/aligned_asr.srt`：ASR对齐SRT
- `output/draft_para_collect_from_assets.json`：编排参数
- `output/image_timeline_from_storyboard.json`：图片时间轴检查文件
- `output/subtitle_timeline_display.json`：字幕时间轴检查文件

## 7. 关键中间文件（ASR核查）
- `output/asr_mid/01_oss_upload.json`
- `output/asr_mid/02_asr_word_raw.json`
- `output/asr_mid/03_word_segments.json`
- `output/asr_mid/04_llm_correct_request.json`
- `output/asr_mid/05_llm_correct_response.json`
- `output/asr_mid/06_symbol_split_lines.json`
- `output/asr_mid/07b_llm_longline_request.json`
- `output/asr_mid/07c_llm_longline_response.json`
- `output/asr_mid/08_rechunk_lines.json`
- `output/asr_mid/09_asr_char_timeline.json`
- `output/asr_mid/10_lcs_pairs.json`
- `output/asr_mid/11_target_char_timing.json`
- `output/asr_mid/12_aligned_segments.json`
- `output/asr_mid/99_oss_delete.json`

其中：
- `01_oss_upload.json` 记录的是 ServiceHub OSS 代理上传结果，而不是技能直连 OSS 的 SDK 返回
- `99_oss_delete.json` 记录的是 ServiceHub OSS 代理删除结果

## 8. 推荐执行命令
```bash
python scripts/parse_storyboard_md.py \
  --md-path "<分镜md绝对路径>"

python scripts/align.py \
  --audio "<配音音频绝对路径>"

python scripts/compose_from_assets.py \
  --audio-path "<配音音频绝对路径>" \
  --template-id template2
```

## 9. 已知限制
- ASR 误识较多时，LCS 映射局部可能有轻微误差。
- 超长句切分质量受模型稳定性影响；当前已加“强校验+回退”以避免丢字导致整体错位。
