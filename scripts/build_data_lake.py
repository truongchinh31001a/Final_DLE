from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.data_lake.build import build_bronze, build_gold, build_silver, validate_lake


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build data lake bronze/silver/gold datasets.")
    parser.add_argument("--config", default="configs/data_lake.yaml", help="Path to data lake config.")
    parser.add_argument(
        "--stage",
        choices=["bronze", "silver", "gold", "all"],
        default="all",
        help="Lake stage to build.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite copied gold images.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs: dict[str, object] = {}

    if args.stage in {"bronze", "all"}:
        bronze = build_bronze(args.config)
        outputs["bronze_rows"] = len(bronze)

    if args.stage in {"silver", "all"}:
        silver = build_silver(args.config)
        outputs["silver_rows"] = len(silver)

    if args.stage in {"gold", "all"}:
        gold = build_gold(args.config, force=args.force)
        outputs["gold_rows"] = len(gold)

    outputs["validation"] = validate_lake(args.config)
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()

