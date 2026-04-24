from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.training.trainer import run_training


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train otoscopy image classifier.")
    parser.add_argument("--config", default="configs/train.yaml", help="Path to train config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_training(args.config)
    print(result)


if __name__ == "__main__":
    main()
