from __future__ import annotations

import pandas as pd
import pytest

from ear_classifier.data.split import make_patient_splits


def test_patient_splits_do_not_leak_patients(tmp_path) -> None:
    rows = []
    labels = ["normal", "otitis_media"]
    for patient_idx in range(20):
        rows.append(
            {
                "image_id": f"img_{patient_idx}",
                "image_path": f"img_{patient_idx}.jpg",
                "patient_id": f"P{patient_idx:03d}",
                "label": labels[patient_idx % 2],
            }
        )

    labels_csv = tmp_path / "labels.csv"
    pd.DataFrame(rows).to_csv(labels_csv, index=False)

    paths = make_patient_splits(
        labels_csv=labels_csv,
        output_dir=tmp_path / "splits",
        val_size=0.2,
        test_size=0.2,
        seed=7,
    )

    patient_sets = {
        split: set(pd.read_csv(path)["patient_id"])
        for split, path in paths.items()
    }

    assert patient_sets["train"].isdisjoint(patient_sets["val"])
    assert patient_sets["train"].isdisjoint(patient_sets["test"])
    assert patient_sets["val"].isdisjoint(patient_sets["test"])


def test_patient_splits_can_group_duplicates(tmp_path) -> None:
    rows = []
    for image_idx in range(10):
        rows.append(
            {
                "image_id": f"img_{image_idx}",
                "image_path": f"img_{image_idx}.jpg",
                "patient_id": f"P{image_idx:03d}",
                "label": "normal" if image_idx % 2 == 0 else "otitis_media",
                "raw_sha256": f"hash_{image_idx // 2}",
            }
        )

    labels_csv = tmp_path / "labels.csv"
    pd.DataFrame(rows).to_csv(labels_csv, index=False)

    paths = make_patient_splits(
        labels_csv=labels_csv,
        output_dir=tmp_path / "splits",
        group_col="raw_sha256",
        val_size=0.2,
        test_size=0.2,
        seed=3,
    )

    split_frames = []
    for split, path in paths.items():
        frame = pd.read_csv(path)
        frame["_split_name"] = split
        split_frames.append(frame)
    combined = pd.concat(split_frames)

    hash_split_counts = combined.groupby("raw_sha256")["_split_name"].nunique()
    assert hash_split_counts.max() == 1


def test_patient_splits_can_deduplicate_grouped_duplicates(tmp_path) -> None:
    rows = []
    for image_idx in range(10):
        rows.append(
            {
                "image_id": f"img_{image_idx}",
                "image_path": f"img_{image_idx}.jpg",
                "patient_id": f"P{image_idx:03d}",
                "label": "normal" if image_idx % 2 == 0 else "otitis_media",
                "raw_sha256": f"hash_{image_idx // 2}",
            }
        )

    labels_csv = tmp_path / "labels.csv"
    pd.DataFrame(rows).to_csv(labels_csv, index=False)

    paths = make_patient_splits(
        labels_csv=labels_csv,
        output_dir=tmp_path / "splits",
        group_col="raw_sha256",
        val_size=0.2,
        test_size=0.2,
        seed=3,
        deduplicate_by_group=True,
    )

    combined = pd.concat((pd.read_csv(path) for path in paths.values()), ignore_index=True)

    assert len(combined) == combined["raw_sha256"].nunique()


def test_patient_splits_require_group_column_for_deduplication(tmp_path) -> None:
    rows = [
        {
            "image_id": "img_0",
            "image_path": "img_0.jpg",
            "patient_id": "P000",
            "label": "normal",
        }
    ]
    labels_csv = tmp_path / "labels.csv"
    pd.DataFrame(rows).to_csv(labels_csv, index=False)

    with pytest.raises(ValueError, match="group_col"):
        make_patient_splits(
            labels_csv=labels_csv,
            output_dir=tmp_path / "splits",
            deduplicate_by_group=True,
        )
