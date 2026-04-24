from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def format_metric(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.4f}"


def print_epoch(prefix: str, row: dict[str, Any]) -> None:
    train = row.get("train", {})
    val = row.get("val", {})
    print(
        f"{prefix} epoch {row.get('epoch')}: "
        f"train_loss={format_metric(train.get('loss'))}, "
        f"train_acc={format_metric(train.get('accuracy'))}, "
        f"val_loss={format_metric(val.get('loss'))}, "
        f"val_acc={format_metric(val.get('accuracy'))}, "
        f"val_macro_f1={format_metric(val.get('macro_f1'))}, "
        f"lr={format_metric(row.get('lr'))}"
    )


def print_classification_report(metrics: dict[str, Any]) -> None:
    report = metrics.get("classification_report", {})
    print("\nPer-class test metrics:")
    print(f"{'class':32} {'precision':>10} {'recall':>10} {'f1':>10} {'support':>10}")
    for label, values in report.items():
        if not isinstance(values, dict) or label in {"accuracy", "macro avg", "weighted avg"}:
            continue
        print(
            f"{label:32} "
            f"{format_metric(values.get('precision')):>10} "
            f"{format_metric(values.get('recall')):>10} "
            f"{format_metric(values.get('f1-score')):>10} "
            f"{int(values.get('support', 0)):>10}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize training and evaluation artifacts.")
    parser.add_argument("--run-name", default="baseline_effb0", help="Run name under reports/metrics.")
    parser.add_argument(
        "--history",
        type=Path,
        default=None,
        help="Optional explicit history.json path.",
    )
    parser.add_argument(
        "--test-metrics",
        type=Path,
        default=None,
        help="Path to test metrics JSON. Defaults to reports/metrics/<run-name>/test_metrics.json.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="Path to best checkpoint. Defaults to models/checkpoints/<run-name>/best.pt.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    history_path = args.history or Path("reports/metrics") / args.run_name / "history.json"
    checkpoint_path = args.checkpoint or Path("models/checkpoints") / args.run_name / "best.pt"
    test_metrics_path = args.test_metrics or Path("reports/metrics") / args.run_name / "test_metrics.json"
    if not test_metrics_path.exists() and args.test_metrics is None:
        legacy_metrics_path = Path("reports/metrics/test_metrics.json")
        if legacy_metrics_path.exists():
            test_metrics_path = legacy_metrics_path

    if not history_path.exists():
        raise SystemExit(f"Missing history file: {history_path}")

    history = load_json(history_path)
    if not history:
        raise SystemExit(f"History is empty: {history_path}")

    best = max(history, key=lambda row: row["val"].get("macro_f1", -row["val"]["loss"]))
    print(f"Run: {args.run_name}")
    print(f"History: {history_path}")
    print(f"Epochs: {len(history)}")
    print_epoch("Best", best)
    print_epoch("Last", history[-1])

    if checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        print(f"\nCheckpoint: {checkpoint_path}")
        print(f"Checkpoint epoch: {checkpoint.get('epoch')}")
        print(f"Model config: {checkpoint.get('model_config')}")
    else:
        print(f"\nCheckpoint missing: {checkpoint_path}")

    if test_metrics_path.exists():
        metrics = load_json(test_metrics_path)
        print(f"\nTest metrics: {test_metrics_path}")
        print(f"accuracy={format_metric(metrics.get('accuracy'))}")
        print(f"macro_f1={format_metric(metrics.get('macro_f1'))}")
        print(f"balanced_accuracy={format_metric(metrics.get('balanced_accuracy'))}")
        print(f"loss={format_metric(metrics.get('loss'))}")
        print(f"roc_auc_ovr_macro={format_metric(metrics.get('roc_auc_ovr_macro'))}")
        print("\nConfusion matrix:")
        for row in metrics.get("confusion_matrix", []):
            print("  " + " ".join(f"{int(value):4d}" for value in row))
        print_classification_report(metrics)
    else:
        print(f"\nTest metrics missing: {test_metrics_path}")


if __name__ == "__main__":
    main()
