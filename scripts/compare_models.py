from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import seaborn as sns
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.models.classifier import build_model


DEFAULT_RUNS = [
    "baseline_custom_cnn",
    "baseline_effb0",
    "baseline_resnet18",
]
RUN_LABELS = {
    "baseline_custom_cnn": "Custom CNN",
    "baseline_effb0": "EfficientNet-B0",
    "baseline_resnet18": "ResNet18",
}
CLASS_NAMES = [
    "acute_otitis_media",
    "cerumen_impaction",
    "chronic_otitis_media",
    "myringosclerosis",
    "normal",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def metric(value: float | int | None) -> float | None:
    return None if value is None else float(value)


def best_epoch(history: list[dict[str, Any]]) -> dict[str, Any]:
    return max(history, key=lambda row: row["val"].get("macro_f1", -row["val"]["loss"]))


def resolve_test_metrics_path(run_name: str) -> Path:
    run_path = Path("reports/metrics") / run_name / "test_metrics.json"
    if run_path.exists():
        return run_path
    if run_name == "baseline_effb0":
        legacy_path = Path("reports/metrics/test_metrics.json")
        if legacy_path.exists():
            return legacy_path
    return run_path


def parameter_count(model_config: dict[str, Any], num_classes: int) -> int:
    model = build_model(
        model_name=model_config.get("name", "efficientnet_b0"),
        num_classes=num_classes,
        pretrained=False,
        dropout=float(model_config.get("dropout", 0.0)),
        library=model_config.get("library", "auto"),
        head_hidden_dim=model_config.get("head_hidden_dim", 256),
        cbam_reduction=model_config.get("cbam_reduction", 16),
        spatial_kernel_size=model_config.get("spatial_kernel_size", 7),
    )
    return sum(param.numel() for param in model.parameters())


def summarize_run(run_name: str) -> dict[str, Any]:
    history_path = Path("reports/metrics") / run_name / "history.json"
    checkpoint_path = Path("models/checkpoints") / run_name / "best.pt"
    test_metrics_path = resolve_test_metrics_path(run_name)
    if not history_path.exists():
        raise FileNotFoundError(f"Missing history: {history_path}")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Missing checkpoint: {checkpoint_path}")
    if not test_metrics_path.exists():
        raise FileNotFoundError(f"Missing test metrics: {test_metrics_path}")

    history = load_json(history_path)
    best = best_epoch(history)
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model_config = checkpoint.get("model_config", {})
    test_metrics = load_json(test_metrics_path)
    confusion_matrix = test_metrics.get("confusion_matrix", [])
    total_test = sum(sum(row) for row in confusion_matrix)
    correct_test = sum(confusion_matrix[i][i] for i in range(min(len(confusion_matrix), len(CLASS_NAMES))))
    test_errors = total_test - correct_test

    return {
        "run_name": run_name,
        "model": RUN_LABELS.get(run_name, run_name),
        "model_config": model_config,
        "epochs": len(history),
        "best_epoch": best["epoch"],
        "best_val_loss": metric(best["val"].get("loss")),
        "best_val_accuracy": metric(best["val"].get("accuracy")),
        "best_val_macro_f1": metric(best["val"].get("macro_f1")),
        "last_val_loss": metric(history[-1]["val"].get("loss")),
        "last_val_accuracy": metric(history[-1]["val"].get("accuracy")),
        "last_val_macro_f1": metric(history[-1]["val"].get("macro_f1")),
        "test_loss": metric(test_metrics.get("loss")),
        "test_accuracy": metric(test_metrics.get("accuracy")),
        "test_macro_f1": metric(test_metrics.get("macro_f1")),
        "test_balanced_accuracy": metric(test_metrics.get("balanced_accuracy")),
        "test_roc_auc_ovr_macro": metric(test_metrics.get("roc_auc_ovr_macro")),
        "test_errors": int(test_errors),
        "test_total": int(total_test),
        "checkpoint_mb": checkpoint_path.stat().st_size / (1024 * 1024),
        "params_m": parameter_count(model_config, num_classes=len(CLASS_NAMES)) / 1_000_000,
        "history_path": str(history_path),
        "checkpoint_path": str(checkpoint_path),
        "test_metrics_path": str(test_metrics_path),
        "confusion_matrix": confusion_matrix,
        "classification_report": test_metrics.get("classification_report", {}),
    }


def summarize_available_runs(run_names: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_name in run_names:
        try:
            rows.append(summarize_run(run_name))
        except FileNotFoundError as exc:
            print(f"Skipping {run_name}: {exc}")
    if not rows:
        raise SystemExit("No comparable runs found.")
    return rows


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    fields = [
        "run_name",
        "model",
        "epochs",
        "best_epoch",
        "params_m",
        "checkpoint_mb",
        "best_val_loss",
        "best_val_accuracy",
        "best_val_macro_f1",
        "test_loss",
        "test_accuracy",
        "test_macro_f1",
        "test_balanced_accuracy",
        "test_roc_auc_ovr_macro",
        "test_errors",
        "test_total",
        "checkpoint_path",
        "test_metrics_path",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_markdown(rows: list[dict[str, Any]], output_path: Path) -> None:
    ranked = sorted(rows, key=lambda row: (row["test_macro_f1"], -row["test_loss"]), reverse=True)
    available_runs = {row["run_name"] for row in rows}
    lines = [
        "# Model Comparison",
        "",
        "| Rank | Model | Params (M) | Best Epoch | Test Accuracy | Test Macro F1 | Test Loss | Errors |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(ranked, start=1):
        lines.append(
            "| "
            f"{rank} | {row['model']} | {fmt(row['params_m'], 2)} | {row['best_epoch']} | "
            f"{fmt(row['test_accuracy'])} | {fmt(row['test_macro_f1'])} | "
            f"{fmt(row['test_loss'])} | {row['test_errors']}/{row['test_total']} |"
        )

    lines.extend(["", "## Notes", ""])
    if "baseline_resnet18" in available_runs:
        lines.append("- ResNet18 is the current transfer-learning benchmark on this split.")
    else:
        lines.append(
            "- ResNet18 is the current benchmark config, but its artifacts are missing; rerun train/evaluate to include it here."
        )
    lines.append("- EfficientNet-B0 remains the recommended default because it keeps the best size/performance tradeoff.")
    lines.append("- Custom CNN is the lightweight baseline for quick experiments and small checkpoints.")
    lines.append(
        "- Treat all results as image-level validation because this dataset has synthetic image-level patient IDs."
    )
    lines.append(
        "- The dataset is clean, balanced, single-source, and duplicate-aware split was used; external validation is still needed."
    )

    lines.extend(["", "## Confusion Matrices", ""])
    for row in rows:
        lines.append(f"### {row['model']}")
        lines.append("")
        lines.append("Rows are true labels; columns are predicted labels.")
        lines.append("")
        lines.append("| true \\ pred | " + " | ".join(CLASS_NAMES) + " |")
        lines.append("|---|" + "|".join(["---:"] * len(CLASS_NAMES)) + "|")
        for class_name, values in zip(CLASS_NAMES, row["confusion_matrix"], strict=True):
            lines.append("| " + class_name + " | " + " | ".join(str(value) for value in values) + " |")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def plot_metric_bars(rows: list[dict[str, Any]], output_path: Path) -> None:
    metrics = ["test_accuracy", "test_macro_f1", "test_balanced_accuracy"]
    labels = [row["model"] for row in rows]
    x = range(len(labels))
    width = 0.25

    plt.figure(figsize=(10, 5))
    for offset, metric_name in enumerate(metrics):
        values = [row[metric_name] for row in rows]
        positions = [idx + (offset - 1) * width for idx in x]
        plt.bar(positions, values, width=width, label=metric_name.replace("test_", ""))

    plt.xticks(list(x), labels, rotation=15, ha="right")
    plt.ylim(0.99, 1.001)
    plt.ylabel("Score")
    plt.title("Test Metrics by Model")
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=160)
    plt.close()


def plot_confusion_matrices(rows: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        plt.figure(figsize=(6, 5))
        sns.heatmap(
            row["confusion_matrix"],
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=CLASS_NAMES,
            yticklabels=CLASS_NAMES,
            cbar=False,
        )
        plt.title(f"Confusion Matrix - {row['model']}")
        plt.xlabel("Predicted")
        plt.ylabel("True")
        plt.xticks(rotation=35, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()
        safe_name = row["run_name"].replace("/", "_")
        plt.savefig(output_dir / f"{safe_name}_confusion_matrix.png", dpi=160)
        plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare trained model runs.")
    parser.add_argument("--runs", nargs="+", default=DEFAULT_RUNS, help="Run names to compare.")
    parser.add_argument("--output-dir", default="reports/model_comparison", help="Output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    rows = summarize_available_runs(args.runs)
    rows = sorted(rows, key=lambda row: row["test_macro_f1"], reverse=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(rows, output_dir / "comparison.csv")
    write_markdown(rows, output_dir / "model_comparison.md")
    plot_metric_bars(rows, output_dir / "test_metric_comparison.png")
    plot_confusion_matrices(rows, output_dir)

    print(f"Wrote {output_dir / 'comparison.csv'}")
    print(f"Wrote {output_dir / 'model_comparison.md'}")
    for row in rows:
        print(
            f"{row['model']}: "
            f"test_acc={fmt(row['test_accuracy'])}, "
            f"macro_f1={fmt(row['test_macro_f1'])}, "
            f"loss={fmt(row['test_loss'])}, "
            f"errors={row['test_errors']}/{row['test_total']}"
        )


if __name__ == "__main__":
    main()
