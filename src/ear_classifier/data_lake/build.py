from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from ear_classifier.data.split import make_patient_splits
from ear_classifier.data_lake.config import load_label_mapping, load_yaml, resolve_project_path, slugify
from ear_classifier.data_lake.schema import BRONZE_COLUMNS, GOLD_COLUMNS, SILVER_COLUMNS


def _empty(value: Any) -> bool:
    return pd.isna(value) or str(value).strip() == ""


def _source_output_dir(lake_root: Path, source_id: str) -> Path:
    return lake_root / "raw" / source_id


def _safe_copy(source: Path, destination: Path, overwrite: bool = False) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        return
    shutil.copy2(source, destination)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    return df[columns]


def _source_manifest(source_cfg: dict[str, Any], lake_root: Path) -> pd.DataFrame:
    source_id = source_cfg["source_id"]
    image_root = resolve_project_path(source_cfg["image_root"])
    labels_csv = resolve_project_path(source_cfg["labels_csv"])
    processed_image_root = resolve_project_path(source_cfg.get("processed_image_root", ""))
    processed_labels_csv = source_cfg.get("processed_labels_csv")
    processed_df = pd.DataFrame()
    if processed_labels_csv:
        processed_path = resolve_project_path(processed_labels_csv)
        if processed_path.exists():
            processed_df = pd.read_csv(processed_path)

    df = pd.read_csv(labels_csv)
    if not processed_df.empty:
        processed_subset_columns = [
            column
            for column in [
                "image_id",
                "image_path",
                "raw_image_path",
                "raw_sha256",
                "processed_sha256",
                "processed_width",
                "processed_height",
            ]
            if column in processed_df.columns
        ]
        processed_subset = processed_df[processed_subset_columns].rename(
            columns={"image_path": "_processed_image_path"}
        )
        df = df.merge(processed_subset, on="image_id", how="left", suffixes=("", "_processed"))

    rows: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        raw_relative = str(row.get("image_path", ""))
        processed_relative = str(row.get("_processed_image_path", ""))
        resolved_raw = Path(raw_relative)
        if not resolved_raw.is_absolute():
            resolved_raw = image_root / resolved_raw

        resolved_processed = Path(processed_relative)
        if processed_relative and not resolved_processed.is_absolute():
            resolved_processed = processed_image_root / resolved_processed

        lake_image_id = f"{source_id}::{row.get('image_id')}"
        rows.append(
            {
                "lake_image_id": lake_image_id,
                "source_id": source_id,
                "source_name": source_cfg.get("source_name", source_id),
                "source_dataset_slug": source_cfg.get("dataset_slug", ""),
                "source_license": source_cfg.get("license", ""),
                "source_site": source_cfg.get("site", ""),
                "source_device": source_cfg.get("device", ""),
                "source_notes": source_cfg.get("notes", ""),
                "image_id": row.get("image_id", ""),
                "image_path": raw_relative,
                "resolved_image_path": str(resolved_raw),
                "processed_image_path": processed_relative,
                "resolved_processed_image_path": str(resolved_processed) if processed_relative else "",
                "original_path": row.get("original_path", ""),
                "label_original": row.get("label", ""),
                "patient_id": row.get("patient_id", ""),
                "patient_id_source": row.get(
                    "patient_id_source",
                    source_cfg.get("patient_id_source", ""),
                ),
                "study_id": row.get("study_id", ""),
                "ear_side": row.get("ear_side", ""),
                "age": row.get("age", ""),
                "sex": row.get("sex", ""),
                "quality": row.get("quality", ""),
                "sha256": row.get("sha256", ""),
                "raw_sha256": row.get("raw_sha256", row.get("sha256", "")),
                "processed_sha256": row.get("processed_sha256", ""),
                "width": row.get("width", ""),
                "height": row.get("height", ""),
                "processed_width": row.get("processed_width", ""),
                "processed_height": row.get("processed_height", ""),
            }
        )

    raw_source_dir = _source_output_dir(lake_root, source_id)
    raw_source_dir.mkdir(parents=True, exist_ok=True)
    _write_json(raw_source_dir / "source_metadata.json", source_cfg)
    manifest = _ensure_columns(pd.DataFrame(rows), BRONZE_COLUMNS)
    manifest.to_csv(raw_source_dir / "manifest.csv", index=False)
    return manifest


def build_bronze(config_path: str | Path) -> pd.DataFrame:
    cfg = load_yaml(config_path)
    lake_root = resolve_project_path(cfg["lake"]["root"])
    bronze_dir = lake_root / "bronze"
    registry_dir = lake_root / "registry"
    bronze_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.mkdir(parents=True, exist_ok=True)

    manifests = [_source_manifest(source_cfg, lake_root) for source_cfg in cfg.get("sources", [])]
    bronze = pd.concat(manifests, ignore_index=True) if manifests else pd.DataFrame(columns=BRONZE_COLUMNS)
    bronze = _ensure_columns(bronze, BRONZE_COLUMNS)
    bronze.to_csv(bronze_dir / "unified_manifest.csv", index=False)

    sources = pd.DataFrame(cfg.get("sources", []))
    sources.to_csv(registry_dir / "sources.csv", index=False)
    return bronze


def build_silver(config_path: str | Path) -> pd.DataFrame:
    cfg = load_yaml(config_path)
    lake_root = resolve_project_path(cfg["lake"]["root"])
    label_mapping = load_label_mapping(resolve_project_path(cfg["lake"]["label_mapping"]))
    bronze_path = lake_root / "bronze" / "unified_manifest.csv"
    if not bronze_path.exists():
        build_bronze(config_path)

    bronze = pd.read_csv(bronze_path, keep_default_na=False)
    silver = bronze.copy()
    silver["label_standard"] = silver["label_original"].map(lambda value: label_mapping.get(slugify(value), ""))
    silver["label_mapping_status"] = silver["label_standard"].map(lambda value: "mapped" if value else "unmapped")
    silver["image_exists"] = silver["resolved_image_path"].map(lambda path: Path(path).exists())
    silver["processed_image_exists"] = silver["resolved_processed_image_path"].map(
        lambda path: bool(path) and Path(path).exists()
    )

    raw_hash = silver["raw_sha256"].astype(str)
    processed_hash = silver["processed_sha256"].astype(str)
    silver["duplicate_raw_sha256"] = raw_hash.ne("") & raw_hash.duplicated(keep=False)
    silver["duplicate_processed_sha256"] = processed_hash.ne("") & processed_hash.duplicated(keep=False)
    group_source = raw_hash.where(raw_hash.ne(""), silver["patient_id"].astype(str))
    silver["split_group"] = group_source

    silver = _ensure_columns(silver, SILVER_COLUMNS)
    silver_dir = lake_root / "silver"
    silver_dir.mkdir(parents=True, exist_ok=True)
    silver.to_csv(silver_dir / "labels.csv", index=False)

    report = {
        "rows": int(len(silver)),
        "sources": silver["source_id"].value_counts().to_dict(),
        "label_mapping_status": silver["label_mapping_status"].value_counts().to_dict(),
        "class_counts": silver["label_standard"].value_counts().to_dict(),
        "missing_raw_images": int((~silver["image_exists"]).sum()),
        "missing_processed_images": int((~silver["processed_image_exists"]).sum()),
        "duplicate_raw_groups": int(silver.loc[silver["duplicate_raw_sha256"], "raw_sha256"].nunique()),
        "duplicate_processed_groups": int(
            silver.loc[silver["duplicate_processed_sha256"], "processed_sha256"].nunique()
        ),
        "patient_id_sources": silver["patient_id_source"].value_counts().to_dict(),
    }
    _write_json(silver_dir / "quality_report.json", report)
    return silver


def _gold_row(row: dict[str, Any], image_path: str) -> dict[str, Any]:
    return {
        "image_id": row["lake_image_id"].replace("::", "__"),
        "image_path": image_path,
        "patient_id": row.get("patient_id", ""),
        "label": row.get("label_standard", ""),
        "source_id": row.get("source_id", ""),
        "source_name": row.get("source_name", ""),
        "site": row.get("source_site", ""),
        "device": row.get("source_device", ""),
        "ear_side": row.get("ear_side", ""),
        "age": row.get("age", ""),
        "sex": row.get("sex", ""),
        "quality": row.get("quality", ""),
        "patient_id_source": row.get("patient_id_source", ""),
        "study_id": row.get("study_id", ""),
        "raw_sha256": row.get("raw_sha256", ""),
        "processed_sha256": row.get("processed_sha256", ""),
        "width": row.get("width", ""),
        "height": row.get("height", ""),
        "processed_width": row.get("processed_width", ""),
        "processed_height": row.get("processed_height", ""),
        "split_group": row.get("split_group", ""),
    }


def build_gold(config_path: str | Path, force: bool = False) -> pd.DataFrame:
    cfg = load_yaml(config_path)
    lake_root = resolve_project_path(cfg["lake"]["root"])
    gold_cfg = cfg["gold"]
    dataset_id = gold_cfg["dataset_id"]
    image_root = resolve_project_path(gold_cfg["image_root"])
    labels_csv = resolve_project_path(gold_cfg["labels_csv"])
    splits_dir = resolve_project_path(gold_cfg["splits_dir"])
    copy_images = bool(gold_cfg.get("copy_images", True))

    silver_path = lake_root / "silver" / "labels.csv"
    if not silver_path.exists():
        build_silver(config_path)
    silver = pd.read_csv(silver_path, keep_default_na=False)

    allowed_classes = set(cfg["lake"]["standard_classes"])
    gold_source = silver[
        silver["label_mapping_status"].eq("mapped")
        & silver["label_standard"].isin(allowed_classes)
        & silver["processed_image_exists"].astype(bool)
    ].copy()

    if force and image_root.exists():
        project_root = Path.cwd().resolve()
        resolved = image_root.resolve()
        if resolved == project_root or project_root not in resolved.parents:
            raise ValueError(f"Refusing to delete outside project: {resolved}")
        shutil.rmtree(image_root)
    image_root.mkdir(parents=True, exist_ok=True)
    labels_csv.parent.mkdir(parents=True, exist_ok=True)
    splits_dir.mkdir(parents=True, exist_ok=True)

    gold_rows: list[dict[str, Any]] = []
    for row in gold_source.to_dict(orient="records"):
        source_path = Path(row["resolved_processed_image_path"])
        extension = source_path.suffix or ".jpg"
        relative_path = Path(str(row["label_standard"])) / f"{row['lake_image_id'].replace('::', '__')}{extension}"
        destination = image_root / relative_path
        if copy_images:
            _safe_copy(source_path, destination, overwrite=force)
            image_path = relative_path.as_posix()
        else:
            image_path = str(source_path)
        gold_rows.append(_gold_row(row, image_path=image_path))

    gold = _ensure_columns(pd.DataFrame(gold_rows), GOLD_COLUMNS)
    gold.to_csv(labels_csv, index=False)

    split_cfg = gold_cfg.get("split", {})
    paths = make_patient_splits(
        labels_csv=labels_csv,
        output_dir=splits_dir,
        patient_col="patient_id",
        label_col="label",
        group_col=split_cfg.get("group_column", "split_group"),
        val_size=float(split_cfg.get("val_size", 0.15)),
        test_size=float(split_cfg.get("test_size", 0.15)),
        seed=int(split_cfg.get("seed", 42)),
        stratify_by_label=bool(split_cfg.get("stratify_by_label", True)),
    )

    report = {
        "dataset_id": dataset_id,
        "rows": int(len(gold)),
        "class_counts": gold["label"].value_counts().to_dict(),
        "source_counts": gold["source_id"].value_counts().to_dict(),
        "patient_id_sources": gold["patient_id_source"].value_counts().to_dict(),
        "copy_images": copy_images,
        "image_root": str(image_root),
        "labels_csv": str(labels_csv),
        "splits": {split: str(path) for split, path in paths.items()},
        "split_counts": {
            split: int(pd.read_csv(path).shape[0])
            for split, path in paths.items()
        },
        "notes": [
            "This gold dataset uses duplicate-aware split_group from raw_sha256.",
            "Kaggle source still has synthetic image-level patient IDs, not real patient-level validation.",
        ],
    }
    _write_json(labels_csv.parent / "dataset_card.json", report)
    (labels_csv.parent / "dataset_card.md").write_text(_dataset_card_markdown(report), encoding="utf-8")
    return gold


def _dataset_card_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Dataset Card: {report['dataset_id']}",
        "",
        f"- Rows: {report['rows']}",
        f"- Image root: `{report['image_root']}`",
        f"- Labels CSV: `{report['labels_csv']}`",
        f"- Copy images: {report['copy_images']}",
        "",
        "## Class Counts",
        "",
    ]
    for label, count in report["class_counts"].items():
        lines.append(f"- {label}: {count}")
    lines.extend(["", "## Source Counts", ""])
    for source, count in report["source_counts"].items():
        lines.append(f"- {source}: {count}")
    lines.extend(["", "## Split Counts", ""])
    for split, count in report["split_counts"].items():
        lines.append(f"- {split}: {count}")
    lines.extend(["", "## Notes", ""])
    for note in report["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def validate_lake(config_path: str | Path) -> dict[str, Any]:
    cfg = load_yaml(config_path)
    lake_root = resolve_project_path(cfg["lake"]["root"])
    silver_path = lake_root / "silver" / "labels.csv"
    gold_labels_path = resolve_project_path(cfg["gold"]["labels_csv"])
    report: dict[str, Any] = {}

    if silver_path.exists():
        silver = pd.read_csv(silver_path, keep_default_na=False)
        report["silver_rows"] = int(len(silver))
        report["unmapped_labels"] = sorted(
            set(silver.loc[silver["label_mapping_status"].ne("mapped"), "label_original"])
        )
        report["missing_processed_images"] = int((~silver["processed_image_exists"].astype(bool)).sum())
        report["duplicate_raw_groups"] = int(silver.loc[silver["duplicate_raw_sha256"], "raw_sha256"].nunique())
    else:
        report["silver_missing"] = True

    if gold_labels_path.exists():
        gold = pd.read_csv(gold_labels_path, keep_default_na=False)
        report["gold_rows"] = int(len(gold))
        report["gold_class_counts"] = gold["label"].value_counts().to_dict()
        report["gold_source_counts"] = gold["source_id"].value_counts().to_dict()
        split_dir = resolve_project_path(cfg["gold"]["splits_dir"])
        split_frames = []
        for split in ["train", "val", "test"]:
            path = split_dir / f"{split}.csv"
            if path.exists():
                frame = pd.read_csv(path, keep_default_na=False)
                frame["split"] = split
                split_frames.append(frame)
        if split_frames:
            splits = pd.concat(split_frames, ignore_index=True)
            raw_cross_split = (
                splits.groupby("raw_sha256")["split"].nunique().gt(1).sum()
                if "raw_sha256" in splits.columns
                else None
            )
            report["gold_split_counts"] = splits["split"].value_counts().to_dict()
            report["gold_cross_split_duplicate_raw_groups"] = int(raw_cross_split or 0)
    else:
        report["gold_missing"] = True

    _write_json(lake_root / "registry" / "validation_report.json", report)
    return report

