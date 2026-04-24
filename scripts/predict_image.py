from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.inference.predictor import OtoscopyPredictor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict one otoscopy image.")
    parser.add_argument("--config", default="configs/inference.yaml", help="Path to inference config.")
    parser.add_argument("--checkpoint", default=None, help="Optional checkpoint override.")
    parser.add_argument("--image", required=True, help="Image path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    predictor = OtoscopyPredictor(args.config, args.checkpoint)
    print(json.dumps(predictor.predict(args.image), indent=2))


if __name__ == "__main__":
    main()
