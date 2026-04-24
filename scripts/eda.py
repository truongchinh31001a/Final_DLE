from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.config import load_data_config
from ear_classifier.data.eda import run_eda


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run EDA for the otoscopy dataset.")
    parser.add_argument("--config", default="configs/data.yaml", help="Path to data config.")
    parser.add_argument("--output-dir", default="reports/eda", help="EDA output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_data_config(args.config)
    summary = run_eda(cfg, output_dir=args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

