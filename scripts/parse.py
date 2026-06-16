#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Jianying draft folder to draft_para_collect JSON.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--draft-folder", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    sys.path.insert(0, args.project_root)
    from utility.draft_parser import parse_draft_folder

    result = parse_draft_folder(args.draft_folder, args.output or None)
    if args.output:
        print(os.path.abspath(args.output))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
