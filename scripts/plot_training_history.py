from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


RUN_LABELS = {
    "baseline_custom_cnn": "Custom CNN",
    "baseline_effb0": "EfficientNet-B0",
    "baseline_resnet18": "ResNet18",
    "gold_resnet18": "Gold ResNet18",
    "baseline_resnet50": "ResNet50",
    "gold_resnet50": "Gold ResNet50",
}
DEFAULT_RUNS = [
    "baseline_custom_cnn",
    "baseline_effb0",
    "baseline_resnet18",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def flatten_history(run_name: str, history_path: Path) -> list[dict[str, Any]]:
    history = load_json(history_path)
    rows: list[dict[str, Any]] = []
    for record in history:
        train = record.get("train", {})
        val = record.get("val", {})
        rows.append(
            {
                "run_name": run_name,
                "model": RUN_LABELS.get(run_name, run_name),
                "epoch": int(record["epoch"]),
                "train_loss": float(train.get("loss", 0.0)),
                "train_accuracy": float(train.get("accuracy", 0.0)),
                "val_loss": float(val.get("loss", 0.0)),
                "val_accuracy": float(val.get("accuracy", 0.0)),
                "val_macro_f1": float(val.get("macro_f1", 0.0)),
                "val_balanced_accuracy": float(val.get("balanced_accuracy", 0.0)),
                "learning_rate": float(record.get("lr", 0.0)),
            }
        )
    return rows


def discover_runs(metrics_dir: Path) -> list[str]:
    runs = [
        path.parent.name
        for path in metrics_dir.rglob("history.json")
        if path.parent.name != metrics_dir.name
    ]
    return sorted(runs)


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "run_name",
        "model",
        "epoch",
        "train_loss",
        "train_accuracy",
        "val_loss",
        "val_accuracy",
        "val_macro_f1",
        "val_balanced_accuracy",
        "learning_rate",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def plot_line(rows: list[dict[str, Any]], metric: str, output_path: Path, title: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=pd.DataFrame(rows), x="epoch", y=metric, hue="model", marker="o")
    plt.title(title)
    plt.xlabel("Epoch")
    plt.ylabel(metric.replace("_", " ").title())
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def plot_run_panel(rows: list[dict[str, Any]], run_name: str, output_path: Path) -> None:
    run_rows = [row for row in rows if row["run_name"] == run_name]
    if not run_rows:
        return

    model_name = run_rows[0]["model"]
    epochs = [row["epoch"] for row in run_rows]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes[0, 0].plot(epochs, [row["train_loss"] for row in run_rows], marker="o", label="train_loss")
    axes[0, 0].plot(epochs, [row["val_loss"] for row in run_rows], marker="o", label="val_loss")
    axes[0, 0].set_title("Loss")
    axes[0, 0].legend()

    axes[0, 1].plot(epochs, [row["train_accuracy"] for row in run_rows], marker="o", label="train_acc")
    axes[0, 1].plot(epochs, [row["val_accuracy"] for row in run_rows], marker="o", label="val_acc")
    axes[0, 1].set_title("Accuracy")
    axes[0, 1].legend()

    axes[1, 0].plot(epochs, [row["val_macro_f1"] for row in run_rows], marker="o", color="#59a14f")
    axes[1, 0].set_title("Validation Macro F1")

    axes[1, 1].plot(epochs, [row["learning_rate"] for row in run_rows], marker="o", color="#f28e2b")
    axes[1, 1].set_title("Learning Rate")

    for axis in axes.flat:
        axis.set_xlabel("Epoch")
        axis.grid(alpha=0.25)

    fig.suptitle(f"Training Curves - {model_name}")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def best_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    best_score = max(row["val_macro_f1"] for row in rows)
    for row in rows:
        if row["val_macro_f1"] == best_score:
            return row
    return rows[-1]


def write_markdown(rows: list[dict[str, Any]], output_path: Path) -> None:
    run_names = []
    for row in rows:
        if row["run_name"] not in run_names:
            run_names.append(row["run_name"])

    lines = [
        "# Training History Report",
        "",
        "| Model | Epochs | Best Epoch | Best Val Macro F1 | Best Val Loss | Last Val Macro F1 | Last Val Loss |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for run_name in run_names:
        run_rows = [row for row in rows if row["run_name"] == run_name]
        best = best_row(run_rows)
        last = run_rows[-1]
        lines.append(
            "| "
            f"{best['model']} | {len(run_rows)} | {best['epoch']} | "
            f"{best['val_macro_f1']:.4f} | {best['val_loss']:.4f} | "
            f"{last['val_macro_f1']:.4f} | {last['val_loss']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## How To Read",
            "",
            "- `train_loss` and `val_loss` show whether the model is still improving or starting to overfit.",
            "- `val_macro_f1` is the main validation metric for class-balanced medical classification.",
            "- Best epoch matches the training checkpoint rule: first epoch reaching the highest `val_macro_f1`.",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot training history curves from history.json files.")
    parser.add_argument("--metrics-dir", default="reports/metrics", help="Metrics directory.")
    parser.add_argument("--output-dir", default="reports/training_history", help="Output directory.")
    parser.add_argument(
        "--runs",
        nargs="*",
        default=None,
        help="Run names to plot. Defaults to the finalized 3-model lineup.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics_dir = Path(args.metrics_dir)
    output_dir = Path(args.output_dir)
    run_names = args.runs or DEFAULT_RUNS

    rows: list[dict[str, Any]] = []
    for run_name in run_names:
        history_path = metrics_dir / run_name / "history.json"
        if history_path.exists():
            rows.extend(flatten_history(run_name, history_path))

    if not rows:
        raise SystemExit("No history rows found.")

    write_csv(rows, output_dir / "training_history.csv")
    write_markdown(rows, output_dir / "training_history_report.md")
    plot_line(rows, "train_loss", output_dir / "train_loss.png", "Train Loss by Epoch")
    plot_line(rows, "val_loss", output_dir / "val_loss.png", "Validation Loss by Epoch")
    plot_line(rows, "val_accuracy", output_dir / "val_accuracy.png", "Validation Accuracy by Epoch")
    plot_line(rows, "val_macro_f1", output_dir / "val_macro_f1.png", "Validation Macro F1 by Epoch")
    plot_line(rows, "learning_rate", output_dir / "learning_rate.png", "Learning Rate by Epoch")

    for run_name in run_names:
        plot_run_panel(rows, run_name, output_dir / f"{run_name}_training_panel.png")

    print(f"Wrote {output_dir / 'training_history_report.md'}")
    print(f"Wrote {output_dir / 'training_history.csv'}")


if __name__ == "__main__":
    main()
