#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from skill_config import load_runtime_config


SECTION_STORYBOARD = "## 口播文案分镜设计"
SECTION_SCRIPT = "## 口播文案"
IMAGE_RE = re.compile(r"!\[\[([^\]]+)\]\]")


def _extract_section_lines(md_text: str, section_title: str) -> List[str]:
    lines = md_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == section_title:
            start = i + 1
            break
    if start is None:
        raise ValueError(f"section not found: {section_title}")

    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return lines[start:end]


def _is_cut_note_line(line: str) -> bool:
    s = line.strip()
    return s.startswith("> [剪辑注开始]") or s.startswith("> [剪辑注结束]") or s.startswith(">")


def _extract_script_text(md_text: str) -> str:
    lines = _extract_section_lines(md_text, SECTION_SCRIPT)
    out: List[str] = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        out.append(s)
    return "\n".join(out).strip()


def parse_storyboard(md_path: Path, attachments_dir_name: str = "attachments") -> Dict[str, Any]:
    text = md_path.read_text(encoding="utf-8")
    section_lines = _extract_section_lines(text, SECTION_STORYBOARD)
    script_text = _extract_script_text(text)
    md_dir = md_path.parent
    attachments_dir = md_dir / attachments_dir_name
    if not attachments_dir.exists() and attachments_dir_name == "attachments":
        fallback_dir = md_dir / "Attachments"
        if fallback_dir.exists():
            attachments_dir = fallback_dir
            attachments_dir_name = "Attachments"

    items: List[Dict[str, Any]] = []
    current_text_parts: List[str] = []
    current_prompt_lines: Optional[List[str]] = None
    in_prompt = False
    prompt_lang = ""
    in_cut_note = False
    cut_note_lines: List[str] = []

    def current_text() -> str:
        return " ".join([p.strip() for p in current_text_parts if p.strip()]).strip()

    for raw_line in section_lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if not stripped:
            continue
        if stripped.startswith("> [剪辑注开始]"):
            in_cut_note = True
            cut_note_lines = []
            continue
        if stripped.startswith("> [剪辑注结束]"):
            in_cut_note = False
            note_text = " ".join([x.strip() for x in cut_note_lines if x.strip()]).strip()
            if note_text:
                items.append(
                    {
                        "index": len(items) + 1,
                        "item_type": "black_note",
                        "narration": note_text,
                        "prompt": "",
                        "prompt_lang": "",
                        "image_name": "",
                        "image_rel_path": "",
                        "image_abs_path": "",
                        "image_exists": False,
                    }
                )
            cut_note_lines = []
            continue
        if in_cut_note:
            if not stripped.startswith(">"):
                cut_note_lines.append(stripped)
            continue
        if _is_cut_note_line(stripped):
            continue

        if stripped.startswith("```"):
            if not in_prompt:
                in_prompt = True
                prompt_lang = stripped[3:].strip().lower()
                current_prompt_lines = []
            else:
                in_prompt = False
            continue

        if in_prompt:
            if current_prompt_lines is not None:
                current_prompt_lines.append(line)
            continue

        image_match = IMAGE_RE.search(stripped)
        if image_match:
            image_name = image_match.group(1).strip()
            rel_path = f"{attachments_dir_name}/{image_name}"
            abs_path = (attachments_dir / image_name).resolve()
            prompt_text = ""
            if current_prompt_lines:
                prompt_text = "\n".join(current_prompt_lines).strip()

            items.append(
                {
                    "index": len(items) + 1,
                    "item_type": "image",
                    "narration": current_text(),
                    "prompt": prompt_text,
                    "prompt_lang": prompt_lang or "prompt",
                    "image_name": image_name,
                    "image_rel_path": rel_path.replace("\\", "/"),
                    "image_abs_path": str(abs_path),
                    "image_exists": abs_path.exists(),
                }
            )
            current_text_parts = []
            current_prompt_lines = None
            prompt_lang = ""
            continue

        # regular narration line
        current_text_parts.append(stripped)

    missing = [it["image_rel_path"] for it in items if not it["image_exists"]]
    return {
        "status": "success",
        "source_md": str(md_path.resolve()),
        "script_text": script_text,
        "attachments_dir": str(attachments_dir.resolve()),
        "total_items": len(items),
        "missing_images": missing,
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse markdown: extract script text + storyboard image sequence.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--config", default="", help="Path to config.json.")
    parser.add_argument("--md-path", required=True, help="Path to markdown file.")
    parser.add_argument("--output-json", default="", help="Path to output json. Default: <project>/output/storyboard_sequence.json")
    parser.add_argument("--output-script", default="", help="Path to output script txt. Default: <project>/output/script_text.txt")
    parser.add_argument("--attachments-dir-name", default="attachments", help="Relative attachments folder name.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    cfg_path = Path(args.config).resolve() if args.config else None
    cfg = load_runtime_config(project_root, cfg_path)
    defaults = (((cfg.get("defaults") or {}).get("parse_storyboard")) or {})

    md_path = Path(args.md_path).resolve()
    result = parse_storyboard(md_path, attachments_dir_name=args.attachments_dir_name)
    output_json_default = str(defaults.get("output_json") or "output/storyboard_sequence.json")
    output_script_default = str(defaults.get("output_script") or "output/script_text.txt")
    output_path = Path(args.output_json).resolve() if args.output_json else (project_root / output_json_default)
    script_path = Path(args.output_script).resolve() if args.output_script else (project_root / output_script_default)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(str(result.get("script_text", "")), encoding="utf-8")
    print(str(output_path))
    print(str(script_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
