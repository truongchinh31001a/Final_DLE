from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.config import load_data_config
from ear_classifier.data.processing import run_processing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process raw otoscopy images.")
    parser.add_argument("--config", default="configs/data.yaml", help="Path to data config.")
    parser.add_argument("--force", action="store_true", help="Clear processed images before rebuilding.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_data_config(args.config)
    report = run_processing(cfg, force=args.force)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

