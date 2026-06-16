#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose Jianying draft folder from draft_para_collect JSON.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--input", required=True, help="Path to draft_para_collect json.")
    args = parser.parse_args()

    sys.path.insert(0, args.project_root)
    from utility.draft_config_comb import execute_draft_composition_workflow

    out_dir = execute_draft_composition_workflow(args.input)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
