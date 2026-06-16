#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse -> Compose -> Validate roundtrip.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--draft-folder", required=True, help="Source draft folder.")
    parser.add_argument("--parsed-output", required=True, help="Output parsed json file path.")
    args = parser.parse_args()

    sys.path.insert(0, args.project_root)
    from utility.draft_parser import parse_draft_folder
    from utility.draft_config_comb import execute_draft_composition_workflow
    from utility.draft_config_comb_check import check_draft_output

    parse_draft_folder(args.draft_folder, args.parsed_output)
    out_dir = execute_draft_composition_workflow(args.parsed_output)
    check_draft_output(args.parsed_output, out_dir, raise_on_error=True)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
