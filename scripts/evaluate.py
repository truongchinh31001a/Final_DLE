from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.training.trainer import run_evaluation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate otoscopy image classifier.")
    parser.add_argument("--config", default="configs/train.yaml", help="Path to train config.")
    parser.add_argument("--checkpoint", required=True, help="Path to checkpoint.")
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = run_evaluation(args.config, args.checkpoint, args.split)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
