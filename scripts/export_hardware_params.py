#!/usr/bin/env python3
"""Export the shared OSRacer hardware parameters to JSON."""

import argparse
import json
from pathlib import Path

from osracer_lab_assets.hardware_params import hardware_summary


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
