from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.config import load_data_config
from ear_classifier.data.split import make_patient_splits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create patient-level train/val/test splits.")
    parser.add_argument("--config", default="configs/data.yaml", help="Path to data config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_data_config(args.config)
    columns = cfg.get("columns", {})
    split_cfg = cfg.get("split", {})

    paths = make_patient_splits(
        labels_csv=Path(cfg["labels_csv"]),
        output_dir=Path(cfg["splits_dir"]),
        patient_col=columns.get("patient_id", "patient_id"),
        label_col=columns.get("label", "label"),
        group_col=split_cfg.get("group_column"),
        val_size=float(split_cfg.get("val_size", 0.15)),
        test_size=float(split_cfg.get("test_size", 0.15)),
        seed=int(cfg.get("seed", 42)),
        stratify_by_label=bool(split_cfg.get("stratify_by_label", True)),
        deduplicate_by_group=bool(split_cfg.get("deduplicate_by_group", False)),
    )

    for split, path in paths.items():
        print(f"{split}: {path}")


if __name__ == "__main__":
    main()
