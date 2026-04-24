from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.data_lake.build import validate_lake


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate data lake artifacts.")
    parser.add_argument("--config", default="configs/data_lake.yaml", help="Path to data lake config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = validate_lake(args.config)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

