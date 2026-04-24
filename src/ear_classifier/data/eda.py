from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image, ImageDraw, ImageStat


def resolve_project_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else Path.cwd() / path


def _empty_counts(df: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    for column in df.columns:
        values = df[column]
        if values.dtype == object:
            strings = values.astype("string")
            counts[column] = int(strings.isna().sum() + strings.dropna().str.strip().eq("").sum())
        else:
            counts[column] = int(values.isna().sum())
    return {column: count for column, count in counts.items() if count > 0}


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def _image_stats(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        gray = rgb.convert("L")
        stats = ImageStat.Stat(gray)
        channel_stats = ImageStat.Stat(rgb)
        return {
            "image_exists": True,
            "image_width": int(rgb.width),
            "image_height": int(rgb.height),
            "image_mode": image.mode,
            "mean_brightness": float(stats.mean[0]),
            "contrast_std": float(stats.stddev[0]),
            "red_mean": float(channel_stats.mean[0]),
            "green_mean": float(channel_stats.mean[1]),
            "blue_mean": float(channel_stats.mean[2]),
            "file_size_kb": path.stat().st_size / 1024,
        }


def inspect_images(df: pd.DataFrame, image_root: Path, image_col: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        image_path = Path(row[image_col])
        if not image_path.is_absolute():
            image_path = image_root / image_path

        stats: dict[str, Any]
        if image_path.exists():
            try:
                stats = _image_stats(image_path)
            except Exception as exc:
                stats = {"image_exists": False, "image_error": str(exc)}
        else:
            stats = {"image_exists": False, "image_error": "missing"}

        rows.append({**row, "resolved_image_path": str(image_path), **stats})

    return pd.DataFrame(rows)


def load_splits(splits_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for split in ["train", "val", "test"]:
        path = splits_dir / f"{split}.csv"
        if path.exists():
            frame = pd.read_csv(path)
            frame["split"] = split
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_summary(
    eda_df: pd.DataFrame,
    split_df: pd.DataFrame,
    class_names: list[str],
    label_col: str,
    patient_col: str,
) -> dict[str, Any]:
    class_counts = eda_df[label_col].value_counts().reindex(class_names, fill_value=0).to_dict()
    image_exists = eda_df["image_exists"].fillna(False).astype(bool)
    missing_images = int((~image_exists).sum())
    duplicate_raw = (
        int(eda_df["raw_sha256"].duplicated().sum())
        if "raw_sha256" in eda_df.columns
        else int(eda_df["sha256"].duplicated().sum())
        if "sha256" in eda_df.columns
        else None
    )
    duplicate_processed = (
        int(eda_df["processed_sha256"].duplicated().sum())
        if "processed_sha256" in eda_df.columns
        else None
    )

    image_summary: dict[str, Any] = {}
    if image_exists.any():
        available = eda_df[image_exists]
        image_summary = {
            "width_counts": available["image_width"].value_counts().sort_index().to_dict(),
            "height_counts": available["image_height"].value_counts().sort_index().to_dict(),
            "brightness": available["mean_brightness"].describe().to_dict(),
            "contrast": available["contrast_std"].describe().to_dict(),
            "file_size_kb": available["file_size_kb"].describe().to_dict(),
        }

    split_summary: dict[str, Any] = {}
    if not split_df.empty:
        split_summary = {
            "counts": split_df["split"].value_counts().reindex(["train", "val", "test"], fill_value=0).to_dict(),
            "by_class": (
                split_df.groupby(["split", label_col])
                .size()
                .unstack(fill_value=0)
                .reindex(index=["train", "val", "test"], columns=class_names, fill_value=0)
                .to_dict(orient="index")
            ),
        }

    synthetic_patient_ids = False
    if "patient_id_source" in eda_df.columns:
        synthetic_patient_ids = bool(
            eda_df["patient_id_source"].fillna("").astype(str).eq("synthetic_image_id").all()
        )

    return {
        "num_rows": int(len(eda_df)),
        "num_classes": int(len(class_names)),
        "class_counts": {str(key): int(value) for key, value in class_counts.items()},
        "missing_images": missing_images,
        "empty_value_counts": _empty_counts(eda_df),
        "unique_patients": int(eda_df[patient_col].nunique()) if patient_col in eda_df.columns else None,
        "synthetic_patient_ids": synthetic_patient_ids,
        "duplicate_raw_hashes": duplicate_raw,
        "duplicate_processed_hashes": duplicate_processed,
        "image_summary": image_summary,
        "split_summary": split_summary,
    }


def duplicate_group_report(
    df: pd.DataFrame,
    hash_col: str,
    label_col: str,
    split_col: str | None = "split",
) -> pd.DataFrame:
    if hash_col not in df.columns:
        return pd.DataFrame()
    duplicates = df[df.duplicated(hash_col, keep=False)].copy()
    if duplicates.empty:
        return pd.DataFrame()

    aggregations: dict[str, Any] = {
        "num_images": ("image_id", "size"),
        "labels": (label_col, lambda values: "|".join(sorted(set(map(str, values))))),
        "image_ids": ("image_id", lambda values: "|".join(map(str, values))),
    }
    if split_col and split_col in duplicates.columns:
        aggregations["splits"] = (split_col, lambda values: "|".join(sorted(set(map(str, values)))))
        aggregations["num_splits"] = (split_col, lambda values: len(set(map(str, values))))

    report = duplicates.groupby(hash_col).agg(**aggregations).reset_index()
    report["num_labels"] = report["labels"].str.split("|").map(len)
    return report.sort_values(["num_splits" if "num_splits" in report.columns else "num_images", hash_col])


def duplicate_summary(duplicate_df: pd.DataFrame) -> dict[str, Any]:
    if duplicate_df.empty:
        return {
            "duplicate_groups": 0,
            "duplicate_rows": 0,
            "cross_split_groups": 0,
            "cross_label_groups": 0,
        }

    duplicate_rows = int(duplicate_df["num_images"].sum())
    cross_split_groups = (
        int((duplicate_df["num_splits"] > 1).sum()) if "num_splits" in duplicate_df.columns else None
    )
    return {
        "duplicate_groups": int(len(duplicate_df)),
        "duplicate_rows": duplicate_rows,
        "cross_split_groups": cross_split_groups,
        "cross_label_groups": int((duplicate_df["num_labels"] > 1).sum()),
    }


def _save_plot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_class_distribution(df: pd.DataFrame, class_names: list[str], label_col: str, output_path: Path) -> None:
    counts = df[label_col].value_counts().reindex(class_names, fill_value=0).reset_index()
    counts.columns = [label_col, "count"]
    plt.figure(figsize=(10, 5))
    sns.barplot(data=counts, x=label_col, y="count", color="#4e79a7")
    plt.xticks(rotation=25, ha="right")
    plt.title("Class distribution")
    plt.xlabel("Class")
    plt.ylabel("Images")
    _save_plot(output_path)


def plot_split_distribution(split_df: pd.DataFrame, class_names: list[str], label_col: str, output_path: Path) -> None:
    if split_df.empty:
        return
    counts = (
        split_df.groupby(["split", label_col])
        .size()
        .unstack(fill_value=0)
        .reindex(index=["train", "val", "test"], columns=class_names, fill_value=0)
    )
    plt.figure(figsize=(10, 5))
    bottom = np.zeros(len(counts))
    palette = sns.color_palette("Set2", n_colors=len(class_names))
    for color, class_name in zip(palette, class_names, strict=True):
        values = counts[class_name].to_numpy()
        plt.bar(counts.index, values, bottom=bottom, label=class_name, color=color)
        bottom += values
    plt.title("Split distribution by class")
    plt.xlabel("Split")
    plt.ylabel("Images")
    plt.legend(loc="upper right", fontsize=8)
    _save_plot(output_path)


def plot_brightness_by_class(df: pd.DataFrame, label_col: str, output_path: Path) -> None:
    available = df[df["image_exists"].fillna(False).astype(bool)]
    if available.empty:
        return
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=available, x=label_col, y="mean_brightness", color="#59a14f")
    plt.xticks(rotation=25, ha="right")
    plt.title("Brightness by class")
    plt.xlabel("Class")
    plt.ylabel("Mean grayscale brightness")
    _save_plot(output_path)


def plot_contrast_by_class(df: pd.DataFrame, label_col: str, output_path: Path) -> None:
    available = df[df["image_exists"].fillna(False).astype(bool)]
    if available.empty:
        return
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=available, x=label_col, y="contrast_std", color="#f28e2b")
    plt.xticks(rotation=25, ha="right")
    plt.title("Contrast by class")
    plt.xlabel("Class")
    plt.ylabel("Grayscale standard deviation")
    _save_plot(output_path)


def make_sample_grid(
    df: pd.DataFrame,
    image_root: Path,
    image_col: str,
    label_col: str,
    output_path: Path,
    samples_per_class: int = 5,
    seed: int = 42,
) -> None:
    rng = np.random.default_rng(seed)
    labels = sorted(df[label_col].dropna().unique())
    thumbs: list[tuple[str, Image.Image]] = []
    for label in labels:
        class_df = df[df[label_col] == label]
        sample_size = min(samples_per_class, len(class_df))
        if sample_size == 0:
            continue
        indices = rng.choice(class_df.index.to_numpy(), size=sample_size, replace=False)
        for index in indices:
            image_path = Path(df.loc[index, image_col])
            if not image_path.is_absolute():
                image_path = image_root / image_path
            if not image_path.exists():
                continue
            with Image.open(image_path) as image:
                thumb = image.convert("RGB")
                thumb.thumbnail((128, 128))
                canvas = Image.new("RGB", (144, 166), "white")
                canvas.paste(thumb, ((144 - thumb.width) // 2, 4))
                draw = ImageDraw.Draw(canvas)
                draw.text((6, 140), label[:22], fill="black")
                thumbs.append((label, canvas))

    if not thumbs:
        return

    columns = samples_per_class
    rows = math.ceil(len(thumbs) / columns)
    grid = Image.new("RGB", (columns * 144, rows * 166), "white")
    for idx, (_label, thumb) in enumerate(thumbs):
        x = (idx % columns) * 144
        y = (idx // columns) * 166
        grid.paste(thumb, (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid.save(output_path)


def write_markdown_report(summary: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# EDA Report",
        "",
        "## Dataset",
        "",
        f"- Total rows: {summary['num_rows']}",
        f"- Classes: {summary['num_classes']}",
        f"- Missing images: {summary['missing_images']}",
        f"- Unique patient IDs: {summary['unique_patients']}",
        f"- Synthetic patient IDs: {summary['synthetic_patient_ids']}",
        f"- Duplicate raw hashes: {summary['duplicate_raw_hashes']}",
        f"- Duplicate processed hashes: {summary['duplicate_processed_hashes']}",
        "",
        "## Class Counts",
        "",
    ]
    for label, count in summary["class_counts"].items():
        lines.append(f"- {label}: {count}")

    if summary["split_summary"]:
        lines.extend(["", "## Split Counts", ""])
        for split, count in summary["split_summary"]["counts"].items():
            lines.append(f"- {split}: {count}")

    duplicate_reports = summary.get("duplicate_reports", {})
    if duplicate_reports:
        lines.extend(["", "## Duplicate Checks", ""])
        for hash_col, report in duplicate_reports.items():
            lines.append(
                "- "
                f"{hash_col}: {report['duplicate_groups']} duplicate groups, "
                f"{report['duplicate_rows']} duplicate rows, "
                f"{report['cross_split_groups']} cross-split groups, "
                f"{report['cross_label_groups']} cross-label groups"
            )

    image_summary = summary.get("image_summary", {})
    if image_summary:
        brightness = image_summary.get("brightness", {})
        contrast = image_summary.get("contrast", {})
        lines.extend(
            [
                "",
                "## Image Stats",
                "",
                f"- Width counts: {image_summary.get('width_counts', {})}",
                f"- Height counts: {image_summary.get('height_counts', {})}",
                f"- Brightness mean: {brightness.get('mean', 0):.2f}",
                f"- Brightness min/max: {brightness.get('min', 0):.2f} / {brightness.get('max', 0):.2f}",
                f"- Contrast mean: {contrast.get('mean', 0):.2f}",
                f"- Contrast min/max: {contrast.get('min', 0):.2f} / {contrast.get('max', 0):.2f}",
            ]
        )

    empty_counts = summary.get("empty_value_counts", {})
    if empty_counts:
        lines.extend(["", "## Empty Values", ""])
        for column, count in empty_counts.items():
            lines.append(f"- {column}: {count}")

    if summary["synthetic_patient_ids"]:
        lines.extend(
            [
                "",
                "## Caveat",
                "",
                "The dataset uses synthetic image-level patient IDs. Report results as image-level splits, not real patient-level validation.",
            ]
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_eda(data_cfg: dict[str, Any], output_dir: str | Path = "reports/eda") -> dict[str, Any]:
    output_dir = resolve_project_path(output_dir)
    figure_dir = resolve_project_path("reports/figures/eda")
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    columns = data_cfg.get("columns", {})
    image_col = columns.get("image_path", "image_path")
    label_col = columns.get("label", "label")
    patient_col = columns.get("patient_id", "patient_id")
    labels_csv = resolve_project_path(data_cfg["labels_csv"])
    image_root = resolve_project_path(data_cfg["image_root"])
    splits_dir = resolve_project_path(data_cfg["splits_dir"])
    class_names = data_cfg["classes"]

    df = pd.read_csv(labels_csv)
    split_df = load_splits(splits_dir)
    eda_df = inspect_images(df, image_root=image_root, image_col=image_col)
    summary = _jsonable(build_summary(eda_df, split_df, class_names, label_col, patient_col))

    duplicate_source = split_df if not split_df.empty else eda_df
    duplicate_reports: dict[str, dict[str, Any]] = {}
    for hash_col in ["raw_sha256", "processed_sha256", "sha256"]:
        if hash_col not in duplicate_source.columns:
            continue
        duplicates = duplicate_group_report(duplicate_source, hash_col, label_col)
        if not duplicates.empty:
            duplicates.to_csv(output_dir / f"duplicate_groups_{hash_col}.csv", index=False)
        duplicate_reports[hash_col] = duplicate_summary(duplicates)
    summary["duplicate_reports"] = _jsonable(duplicate_reports)

    eda_df.to_csv(output_dir / "image_stats.csv", index=False)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown_report(summary, output_dir / "eda_report.md")

    plot_class_distribution(eda_df, class_names, label_col, figure_dir / "class_distribution.png")
    plot_split_distribution(split_df, class_names, label_col, figure_dir / "split_distribution.png")
    plot_brightness_by_class(eda_df, label_col, figure_dir / "brightness_by_class.png")
    plot_contrast_by_class(eda_df, label_col, figure_dir / "contrast_by_class.png")
    make_sample_grid(
        eda_df,
        image_root=image_root,
        image_col=image_col,
        label_col=label_col,
        output_path=figure_dir / "sample_grid.png",
    )

    return summary
