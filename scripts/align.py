#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from skill_config import load_runtime_config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ASR-based alignment by ServiceHub (OSS upload + word timestamps + LLM rechunk)."
    )
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--audio", required=True, help="Path to dubbing audio file (mp3/wav).")
    parser.add_argument("--text-file", default="", help="Path to dubbing script txt file (used for correction). Default: <project>/output/script_text.txt")
    parser.add_argument("--language", default="zho", choices=["zho", "eng"])
    parser.add_argument("--output-json", default="", help="Output alignment result json path. Default: <project>/output/aligned_asr.json")
    parser.add_argument("--output-srt", default="", help="Output subtitles srt path. Default: <project>/output/aligned_asr.srt")
    parser.add_argument("--config", default="", help="Path to config.json.")
    parser.add_argument("--subtitle-max-chars", type=int, default=18, help="Max chars per subtitle line after rechunk.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    sys.path.insert(0, str(project_root))

    from aligner.core.output_formatter import OutputFormatter
    from aligner.core.servicehub_asr_processor import ServiceHubASRProcessor

    cfg_path = Path(args.config).resolve() if args.config else None
    config = load_runtime_config(project_root, cfg_path)
    defaults = (((config.get("defaults") or {}).get("align")) or {})
    text_default = str(defaults.get("text_file") or "output/script_text.txt")
    output_json_default = str(defaults.get("output_json") or "output/aligned_asr.json")
    output_srt_default = str(defaults.get("output_srt") or "output/aligned_asr.srt")

    text_path = Path(args.text_file).resolve() if args.text_file else (project_root / text_default)
    if not text_path.exists():
        raise FileNotFoundError(f"text file not found: {text_path}")
    text = text_path.read_text(encoding="utf-8-sig")

    processor = ServiceHubASRProcessor(config=config, project_root=project_root)
    segments = processor.process(
        Path(args.audio).resolve(),
        script_text=text,
        max_chars=max(6, int(args.subtitle_max_chars)),
    )

    result = OutputFormatter.to_subtitle_format(
        segments=segments,
        original_text=text,
        audio_file=str(Path(args.audio).resolve()),
        language=args.language,
    )
    if result.get("status") != "success":
        raise RuntimeError(result.get("error", "alignment failed"))

    output_json = Path(args.output_json).resolve() if args.output_json else (project_root / output_json_default)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    srt_content = OutputFormatter.to_srt_format((result.get("alignment_result") or {}).get("segments") or [])
    output_srt = Path(args.output_srt).resolve() if args.output_srt else (project_root / output_srt_default)
    output_srt.parent.mkdir(parents=True, exist_ok=True)
    output_srt.write_text(srt_content, encoding="utf-8")

    print(str(output_json.resolve()))
    print(str(output_srt.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
