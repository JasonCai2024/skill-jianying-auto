#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the full Jianying auto pipeline: parse storyboard -> align audio -> compose draft."
    )
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--md-path", required=True, help="Storyboard markdown file.")
    parser.add_argument("--audio-path", required=True, help="Dubbing audio file.")
    parser.add_argument("--config", default="", help="Optional config.json path.")
    parser.add_argument("--template-id", default="", help="Optional template id override.")
    parser.add_argument("--attachments-dir-name", default="attachments", help="Relative attachments folder name.")
    parser.add_argument("--subtitle-max-chars", type=int, default=18, help="Max chars per subtitle line.")
    parser.add_argument("--plan-only", action="store_true", help="Skip final draft composition and only output plan files.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    python_exe = sys.executable

    parse_cmd = [
        python_exe,
        str(project_root / "scripts" / "parse_storyboard_md.py"),
        "--project-root",
        str(project_root),
        "--md-path",
        str(Path(args.md_path).resolve()),
        "--attachments-dir-name",
        args.attachments_dir_name,
    ]
    align_cmd = [
        python_exe,
        str(project_root / "scripts" / "align.py"),
        "--project-root",
        str(project_root),
        "--audio",
        str(Path(args.audio_path).resolve()),
        "--subtitle-max-chars",
        str(args.subtitle_max_chars),
    ]
    compose_cmd = [
        python_exe,
        str(project_root / "scripts" / "compose_from_assets.py"),
        "--project-root",
        str(project_root),
        "--audio-path",
        str(Path(args.audio_path).resolve()),
        "--subtitle-max-chars",
        str(args.subtitle_max_chars),
    ]

    if args.config:
        cfg = str(Path(args.config).resolve())
        parse_cmd.extend(["--config", cfg])
        align_cmd.extend(["--config", cfg])
        compose_cmd.extend(["--config", cfg])
    if args.template_id:
        compose_cmd.extend(["--template-id", args.template_id])
    if args.plan_only:
        compose_cmd.append("--plan-only")

    _run(parse_cmd)
    _run(align_cmd)
    _run(compose_cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
