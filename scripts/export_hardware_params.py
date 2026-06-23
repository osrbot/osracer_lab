#!/usr/bin/env python3
"""Export the shared OSRacer hardware parameters to JSON."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))

from hardware_params_loader import hardware_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Export OSRacer hardware parameters as JSON.")
    parser.add_argument("--output", default="-", help="Output JSON path, or '-' for stdout")
    parser.add_argument("--indent", type=int, default=2)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = hardware_summary()
    text = json.dumps(payload, indent=args.indent, sort_keys=True)
    if args.output == "-":
        print(text)
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n")
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
