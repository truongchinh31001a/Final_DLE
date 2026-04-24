from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image


@dataclass(frozen=True)
class ProcessedImage:
    output_path: Path
    crop_box: tuple[int, int, int, int]
    original_size: tuple[int, int]
    processed_size: tuple[int, int]
    sha256: str


def resolve_project_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else Path.cwd() / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_reset_dir(path: Path) -> None:
    project_root = Path.cwd().resolve()
    resolved = path.resolve()
    if resolved == project_root or project_root not in resolved.parents:
        raise ValueError(f"Refusing to delete outside project: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def content_crop_box(
    image: Image.Image,
    threshold: int,
    padding_ratio: float,
    min_content_area_ratio: float,
) -> tuple[int, int, int, int]:
    gray = image.convert("L")
    mask = gray.point(lambda pixel: 255 if pixel > threshold else 0)
    bbox = mask.getbbox()
    width, height = image.size
    full_box = (0, 0, width, height)
    if bbox is None:
        return full_box

    left, top, right, bottom = bbox
    crop_area = max(right - left, 0) * max(bottom - top, 0)
    image_area = width * height
    if crop_area / image_area < min_content_area_ratio:
        return full_box

    padding = int(max(width, height) * padding_ratio)
    left = max(left - padding, 0)
    top = max(top - padding, 0)
    right = min(right + padding, width)
    bottom = min(bottom + padding, height)
    return (left, top, right, bottom)


def process_one_image(
    source_path: Path,
    output_path: Path,
    image_size: int,
    crop_to_content: bool,
    crop_threshold: int,
    crop_padding_ratio: float,
    min_content_area_ratio: float,
    output_format: str,
    jpeg_quality: int,
) -> ProcessedImage:
    with Image.open(source_path) as image:
        image = image.convert("RGB")
        original_size = image.size
        crop_box = (
            content_crop_box(
                image,
                threshold=crop_threshold,
                padding_ratio=crop_padding_ratio,
                min_content_area_ratio=min_content_area_ratio,
            )
            if crop_to_content
            else (0, 0, image.width, image.height)
        )
        image = image.crop(crop_box)
        image = image.resize((image_size, image_size), Image.Resampling.LANCZOS)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_kwargs: dict[str, Any] = {}
        if output_format.lower() in {"jpg", "jpeg"}:
            save_kwargs = {"quality": jpeg_quality, "optimize": True}
        image.save(output_path, **save_kwargs)

    return ProcessedImage(
        output_path=output_path,
        crop_box=crop_box,
        original_size=original_size,
        processed_size=(image_size, image_size),
        sha256=sha256_file(output_path),
    )


def run_processing(data_cfg: dict[str, Any], force: bool = False) -> dict[str, Any]:
    processing_cfg = data_cfg.get("processing", {})
    source_labels = resolve_project_path(
        processing_cfg.get("source_labels_csv", data_cfg.get("raw_labels_csv", "data/raw/labels.csv"))
    )
    source_image_root = resolve_project_path(
        processing_cfg.get("source_image_root", data_cfg.get("raw_image_root", "data/raw/images"))
    )
    output_image_root = resolve_project_path(
        processing_cfg.get("output_image_root", "data/processed/images")
    )
    output_labels = resolve_project_path(
        processing_cfg.get("output_labels_csv", "data/processed/labels.csv")
    )
    output_report = resolve_project_path(
        processing_cfg.get("output_report_json", "data/processed/processing_report.json")
    )

    if force:
        safe_reset_dir(output_image_root)
    else:
        output_image_root.mkdir(parents=True, exist_ok=True)
    output_labels.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)

    image_size = int(processing_cfg.get("image_size", data_cfg.get("image_size", 224)))
    output_format = str(processing_cfg.get("output_format", "jpg")).lower()
    extension = "jpg" if output_format == "jpeg" else output_format
    class_names = set(data_cfg["classes"])
    image_col = data_cfg.get("columns", {}).get("image_path", "image_path")
    label_col = data_cfg.get("columns", {}).get("label", "label")

    source_df = pd.read_csv(source_labels)
    required = [image_col, label_col, "image_id"]
    missing = [col for col in required if col not in source_df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}")

    processed_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    deduplicate = bool(processing_cfg.get("deduplicate_by_sha256", False))

    for row in source_df.to_dict(orient="records"):
        label = row[label_col]
        if label not in class_names:
            skipped_rows.append({**row, "skip_reason": f"unknown_label:{label}"})
            continue

        source_path = Path(row[image_col])
        if not source_path.is_absolute():
            source_path = source_image_root / source_path
        if not source_path.exists():
            skipped_rows.append({**row, "skip_reason": "missing_image"})
            continue

        raw_hash = str(row.get("sha256") or sha256_file(source_path))
        if deduplicate and raw_hash in seen_hashes:
            skipped_rows.append({**row, "skip_reason": "duplicate_sha256"})
            continue
        seen_hashes.add(raw_hash)

        output_path = output_image_root / str(label) / f"{row['image_id']}.{extension}"
        try:
            processed = process_one_image(
                source_path=source_path,
                output_path=output_path,
                image_size=image_size,
                crop_to_content=bool(processing_cfg.get("crop_to_content", True)),
                crop_threshold=int(processing_cfg.get("crop_threshold", 8)),
                crop_padding_ratio=float(processing_cfg.get("crop_padding_ratio", 0.03)),
                min_content_area_ratio=float(processing_cfg.get("min_content_area_ratio", 0.25)),
                output_format=output_format,
                jpeg_quality=int(processing_cfg.get("jpeg_quality", 95)),
            )
        except Exception as exc:
            skipped_rows.append({**row, "skip_reason": f"processing_error:{exc}"})
            continue

        left, top, right, bottom = processed.crop_box
        processed_rows.append(
            {
                **row,
                image_col: processed.output_path.relative_to(output_image_root).as_posix(),
                "raw_image_path": Path(row[image_col]).as_posix(),
                "raw_sha256": raw_hash,
                "processed_sha256": processed.sha256,
                "processed_width": processed.processed_size[0],
                "processed_height": processed.processed_size[1],
                "crop_left": left,
                "crop_top": top,
                "crop_right": right,
                "crop_bottom": bottom,
                "processing_status": "ok",
            }
        )

    processed_df = pd.DataFrame(processed_rows)
    processed_df.to_csv(output_labels, index=False)

    report = {
        "source_labels_csv": str(source_labels),
        "source_image_root": str(source_image_root),
        "output_image_root": str(output_image_root),
        "output_labels_csv": str(output_labels),
        "image_size": image_size,
        "total_rows": int(len(source_df)),
        "processed_rows": int(len(processed_rows)),
        "skipped_rows": int(len(skipped_rows)),
        "class_counts": dict(Counter(row[label_col] for row in processed_rows)),
        "skip_counts": dict(Counter(row["skip_reason"] for row in skipped_rows)),
        "note": "Images are resized without normalization; normalization stays in training transforms.",
    }
    output_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if skipped_rows:
        pd.DataFrame(skipped_rows).to_csv(output_report.with_suffix(".skipped.csv"), index=False)

    return report
