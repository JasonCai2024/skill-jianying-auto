#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate composed draft output against input params.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--input", required=True, help="Path to draft_para_collect json.")
    parser.add_argument("--draft-folder", required=True, help="Path to generated draft folder.")
    args = parser.parse_args()

    sys.path.insert(0, args.project_root)
    from utility.draft_config_comb_check import check_draft_output

    check_draft_output(args.input, args.draft_folder, raise_on_error=True)
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
