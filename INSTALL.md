# 安装与运行

## 1. 环境准备

```powershell
pip install -r requirements.txt
```

建议使用 Python 3.11+。

## 2. 配置凭证

本技能支持以下优先级：

1. 显式 `--config`
2. 环境变量 / `.env`
3. `data/credentials.json`

请不要把真实凭证写入仓库。

## 3. 准备输入

- 一篇本地 Markdown 文件
- 该 Markdown 同级 `attachments/` 目录
- 一段配音音频文件

Markdown 至少包含：

- `## 口播文案`
- `## 口播文案分镜设计`
- 默认图片目录为同级 `attachments/`，若仅存在 `Attachments/` 也可兼容

## 4. 一键执行

```powershell
python scripts/run_pipeline.py --md-path "E:/path/episode.md" --audio-path "E:/path/episode.mp3"
```

可选参数：

```powershell
python scripts/run_pipeline.py `
  --md-path "E:/path/episode.md" `
  --audio-path "E:/path/episode.mp3" `
  --template-id template2 `
  --subtitle-max-chars 18
```

## 5. 分步执行

```powershell
python scripts/parse_storyboard_md.py --md-path "E:/path/episode.md"
python scripts/align.py --audio "E:/path/episode.mp3"
python scripts/compose_from_assets.py --audio-path "E:/path/episode.mp3" --template-id template2
```

## 6. 其他功能命令

```powershell
python scripts/parse.py --draft-folder "D:/JianyingPro Drafts/example" --output "E:/tmp/draft_para_collect.json"
python scripts/compose.py --input "E:/tmp/draft_para_collect.json"
python scripts/validate.py --input "E:/tmp/draft_para_collect.json" --draft-folder "D:/JianyingPro Drafts/example"
python scripts/roundtrip.py --draft-folder "D:/JianyingPro Drafts/example" --parsed-output "E:/tmp/roundtrip.json"
python scripts/evaluate_alignment.py --aligned-json "E:/tmp/aligned_asr.json" --ref-srt "E:/tmp/reference.srt"
```

## 7. 发布前安全检查

1. 检查 `.env` 未入库
2. 检查 `data/credentials.json` 未入库
3. 检查 `output/`、`logs/`、`temp/`、`.venv*` 未入库
4. 检查 `origin` 为不带凭证的干净 URL
5. GitHub 非交互推送时，只允许在单次命令里临时注入 token
