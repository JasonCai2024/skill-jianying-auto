---
name: skill-jianying-auto
description: Builds a Jianying draft from a storyboard Markdown file, local attachments, and a dubbing audio file. Use when Codex needs to parse `## 口播文案` and `## 口播文案分镜设计`, align subtitles with audio, and generate a Jianying draft folder for review or further editing.
disable-model-invocation: true
user-invocable: true
argument-hint: <md-path> <audio-path>
---

# Jianying Auto

## Goal

Build a Jianying draft from one storyboard Markdown file and one dubbing audio file. Preserve the source skill's full workflow surface: storyboard parsing, subtitle alignment, asset composition, draft generation, reverse parsing, roundtrip validation, and alignment quality evaluation.

## Required Inputs

1. Provide one local Markdown file that contains both:
   - `## 口播文案`
   - `## 口播文案分镜设计`
2. Store all referenced images under the Markdown file's sibling `attachments/` folder by default. If only `Attachments/` exists, use it as a compatibility fallback.
3. Provide one local dubbing audio file in `mp3` or `wav`.
4. Prepare credentials for:
   - ServiceHub ASR / LLM
   - ServiceHub OSS proxy
5. If you need reverse parsing or roundtrip validation, provide an existing Jianying draft folder.
6. Install Python dependencies from `requirements.txt`.

## Workflow

1. Read [references/task-recipes.md](references/task-recipes.md) for the standard execution chain and [references/module-map.md](references/module-map.md) for entry-point mapping.
2. Run `scripts/parse_storyboard_md.py` or `scripts/run_pipeline.py` to extract:
   - `output/storyboard_sequence.json`
   - `output/script_text.txt`
3. Run `scripts/align.py` to:
   - upload audio through ServiceHub OSS proxy
   - call ServiceHub ASR for word timestamps
   - correct ASR text with LLM under "only fix, never rewrite"
   - emit `output/aligned_asr.json` and `output/aligned_asr.srt`
4. Run `scripts/compose_from_assets.py` to:
   - map storyboard items to aligned subtitle timing
   - build image, subtitle, and audio tracks
   - generate a Jianying draft folder under the configured draft parent directory
5. Use `scripts/run_pipeline.py` when the user wants the end-to-end path in one command.
6. Use the auxiliary scripts when the user needs the source skill's non-primary capabilities:
   - `scripts/parse.py` for reverse parsing an existing Jianying draft into parameter JSON
   - `scripts/compose.py` for composing from an existing parameter JSON
   - `scripts/validate.py` for validating a generated draft against the input parameter JSON
   - `scripts/roundtrip.py` for parse -> compose -> validate end-to-end checks
   - `scripts/evaluate_alignment.py` for comparing aligned subtitle output with a reference SRT

## Decision Rules

1. Treat `attachments/` as the default image folder unless the user explicitly overrides `--attachments-dir-name`; if `attachments/` does not exist and `Attachments/` exists, use `Attachments/`.
2. Prefer `scripts/run_pipeline.py` for normal production runs.
3. If credentials are missing, load them in this order:
   - explicit config path
   - environment variables / `.env`
   - `data/credentials.json`
4. Merge explicit config over the skill's default `config.json`; do not replace the default config wholesale.
5. Keep compatibility with legacy local credential structures such as `wechat_proxy.remote_service_url`, `wechat_proxy.username`, and `wechat_proxy.passtoken` when they appear in `data/credentials.json` or an explicit config file.
6. Allow interactive or manual Jianying review after draft generation; this skill stops at producing the draft folder.
7. If subtitle timing drifts, inspect `output/asr_mid/` before changing code or templates.
8. Preserve template behavior from the source skill:
   - `template1` is the base composition template
   - `template2` adds image scaling and extra opening text overlay styles

## Output Requirements

Return:

1. The generated Jianying draft folder path.
2. The key intermediate outputs:
   - `output/storyboard_sequence.json`
   - `output/aligned_asr.json`
   - `output/aligned_asr.srt`
   - `output/draft_para_collect_from_assets.json`
   - `output/image_timeline_from_storyboard.json`
   - `output/subtitle_timeline_display.json`
3. When auxiliary scripts are used, also return their direct output path or validation result.
4. A short note on whether timing repair, fallback segmentation, or template-specific overlay logic was used.

## Validation

1. Confirm the Markdown file contains both required sections.
2. Confirm each storyboard image exists under the attachments folder.
3. Confirm `output/aligned_asr.json` contains subtitle segments.
4. Confirm the generated draft folder contains at least:
   - `draft_content.json`
   - `draft_meta_info.json`
5. If subtitle alignment looks wrong, inspect `output/asr_mid/06_symbol_split_lines.json`, `08_rechunk_lines.json`, `10_lcs_pairs.json`, and `12_aligned_segments.json`.
6. If doing roundtrip or reverse-parse work, run `scripts/validate.py` or `scripts/roundtrip.py` instead of checking output by eye only.

## Fallback

1. If the one-shot pipeline fails, run these scripts separately:
   - `scripts/parse_storyboard_md.py`
   - `scripts/align.py`
   - `scripts/compose_from_assets.py`
2. If the user already has a draft parameter JSON, skip storyboard parsing and use `scripts/compose.py`.
3. If the user needs to inspect an existing Jianying draft, use `scripts/parse.py`.
4. If ServiceHub credentials are missing, stop and request the required values instead of hardcoding them.
5. If the final draft cannot be composed, keep the generated parameter files in `output/` for manual inspection and run `scripts/validate.py` when possible.

## Examples

- `用 skill-jianying-auto 处理 E:\\notes\\episode.md 和 E:\\audio\\episode.mp3`
- `运行这个技能，把 episode.md 和配音生成剪映草稿`
- `先解析分镜，再对齐字幕，最后输出剪映草稿目录`
- `把这个现有剪映草稿反向解析成参数 JSON`
- `对这个已生成草稿做 roundtrip 校验`
