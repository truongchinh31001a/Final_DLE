from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image


DATASET_SLUG = "ucimachinelearning/oto-endoscopic-image-dataset"
EXPECTED_LABELS = [
    "acute_otitis_media",
    "cerumen_impaction",
    "chronic_otitis_media",
    "myringosclerosis",
    "normal",
]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
LABEL_ALIASES = {
    "acute_otitis_media": "acute_otitis_media",
    "aom": "acute_otitis_media",
    "cerumen_impaction": "cerumen_impaction",
    "earwax": "cerumen_impaction",
    "earwax_plug": "cerumen_impaction",
    "earwax_impaction": "cerumen_impaction",
    "wax_impaction": "cerumen_impaction",
    "chronic_otitis_media": "chronic_otitis_media",
    "com": "chronic_otitis_media",
    "myringosclerosis": "myringosclerosis",
    "tympanosclerosis": "myringosclerosis",
    "normal": "normal",
    "healthy": "normal",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the Kaggle Otoscopic Image Dataset and build labels.csv."
    )
    parser.add_argument("--dataset", default=DATASET_SLUG, help="Kaggle dataset slug.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project raw data directory.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Build labels.csv from an already downloaded/extracted folder.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Existing extracted dataset folder used with --skip-download.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear generated images and staging data before rebuilding.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def staging_dir_name(dataset: str) -> str:
    return f"_kaggle_{slugify(dataset)}"


def discover_local_sources(raw_dir: Path, dataset: str) -> list[tuple[Path, str]]:
    excluded_dirs = {"images", "__pycache__"}
    local_sources: list[tuple[Path, str]] = []

    for path in sorted(raw_dir.iterdir()):
        if not path.is_dir():
            continue
        if path.name in excluded_dirs or path.name.startswith("_kaggle_"):
            continue
        if not any(image.suffix.lower() in IMAGE_EXTENSIONS for image in path.rglob("*") if image.is_file()):
            continue

        source_name = dataset if path.name == "Oto-Endoscopic_Images" else slugify(path.name)
        local_sources.append((path.resolve(), source_name))

    return local_sources


def download_dataset(dataset: str, staging_dir: Path, force: bool) -> None:
    if force:
        reset_dir(staging_dir)
    else:
        staging_dir.mkdir(parents=True, exist_ok=True)

    if any(staging_dir.iterdir()) and not force:
        print(f"Using existing extracted data in {staging_dir}")
        return

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:
        message = (
            "Kaggle package is not installed. Install the data extra first:\n"
            '  python -m pip install -e ".[data]"'
        )
        raise SystemExit(message) from exc

    try:
        api = KaggleApi()
        api.authenticate()
        api.dataset_download_files(dataset, path=staging_dir, unzip=True, quiet=False)
    except Exception as exc:
        message = (
            "Kaggle download failed. Install the data extra and configure credentials first:\n"
            '  python -m pip install -e ".[data]"\n'
            "  set KAGGLE_USERNAME=<your_username>\n"
            "  set KAGGLE_KEY=<your_api_key>\n"
            "Or place kaggle.json in %USERPROFILE%\\.kaggle\\kaggle.json."
        )
        raise SystemExit(message) from exc


def infer_label(image_path: Path, source_root: Path) -> str:
    relatives = image_path.relative_to(source_root).parents
    for parent in relatives:
        if parent == Path("."):
            continue
        normalized = slugify(parent.name)
        if normalized in LABEL_ALIASES:
            return LABEL_ALIASES[normalized]

    normalized_parent = slugify(image_path.parent.name)
    if normalized_parent in LABEL_ALIASES:
        return LABEL_ALIASES[normalized_parent]
    raise ValueError(f"Cannot infer class label from path: {image_path}")


def iter_images(source_root: Path) -> list[Path]:
    images = [
        path
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(images)


def unique_image_id(base_id: str, seen: Counter[str]) -> str:
    seen[base_id] += 1
    if seen[base_id] == 1:
        return base_id
    return f"{base_id}_{seen[base_id]}"


def build_labels(sources: list[tuple[Path, str]], raw_dir: Path, force: bool) -> Path:
    images_dir = raw_dir / "images"
    labels_csv = raw_dir / "labels.csv"
    if force:
        reset_dir(images_dir)
    else:
        images_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str | int]] = []
    seen_ids: Counter[str] = Counter()
    if not sources:
        raise SystemExit("No source directories found to build labels.csv")

    source_counts: Counter[str] = Counter()

    for source_root, source_name in sources:
        images = iter_images(source_root)
        if not images:
            print(f"Skipping empty source directory: {source_root}")
            continue

        for source_image in images:
            label = infer_label(source_image, source_root)
            if label not in EXPECTED_LABELS:
                raise ValueError(f"Unexpected label {label!r} from {source_image}")

            checksum = file_sha256(source_image)
            stem = slugify(source_image.stem) or "image"
            image_id = unique_image_id(f"{label}_{stem}_{checksum[:8]}", seen_ids)
            destination = images_dir / label / f"{image_id}{source_image.suffix.lower()}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists() or force:
                shutil.copy2(source_image, destination)

            with Image.open(destination) as image:
                width, height = image.size

            rows.append(
                {
                    "image_id": image_id,
                    "image_path": destination.relative_to(images_dir).as_posix(),
                    "patient_id": image_id,
                    "label": label,
                    "ear_side": "",
                    "age": "",
                    "sex": "",
                    "source": source_name,
                    "quality": "",
                    "patient_id_source": "synthetic_image_id",
                    "original_path": str(Path(source_root.name) / source_image.relative_to(source_root)),
                    "sha256": checksum,
                    "width": width,
                    "height": height,
                }
            )
            source_counts[source_name] += 1

    if not rows:
        raise SystemExit("No images found in the selected source directories")

    with labels_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    label_counts = Counter(row["label"] for row in rows)
    print(f"Wrote {labels_csv} with {len(rows)} images")
    for label in EXPECTED_LABELS:
        print(f"  {label}: {label_counts[label]}")
    print("Sources:")
    for source_name, count in sorted(source_counts.items()):
        print(f"  {source_name}: {count}")
    print("Note: Kaggle dataset does not include patient IDs; patient_id is synthetic per image.")
    return labels_csv


def main() -> None:
    args = parse_args()
    raw_dir = args.raw_dir.resolve()
    staging_dir = raw_dir / staging_dir_name(args.dataset)
    if args.source_dir:
        source_dir = args.source_dir.resolve()
        if not source_dir.exists():
            raise SystemExit(f"Source directory does not exist: {source_dir}")
        sources = [(source_dir, slugify(source_dir.name))]
    else:
        sources = discover_local_sources(raw_dir, args.dataset)
        if sources:
            print("Using existing local source directories:")
            for source_root, source_name in sources:
                print(f"  - {source_root} ({source_name})")
        elif not args.skip_download:
            download_dataset(args.dataset, staging_dir, force=args.force)
            sources = [(staging_dir.resolve(), args.dataset)]
        else:
            raise SystemExit(
                f"No local source directories found in {raw_dir} and --skip-download was provided."
            )

    build_labels(sources, raw_dir, force=args.force)


if __name__ == "__main__":
    main()
