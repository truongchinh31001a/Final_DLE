from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def _patient_label_table(
    df: pd.DataFrame,
    group_col: str,
    label_col: str,
) -> pd.DataFrame:
    def majority_label(labels: pd.Series) -> str:
        return labels.mode().iat[0]

    return (
        df.groupby(group_col, as_index=False)[label_col]
        .agg(majority_label)
        .rename(columns={label_col: "_patient_majority_label"})
    )


def _safe_train_test_split(
    table: pd.DataFrame,
    test_size: float,
    seed: int,
    stratify: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    stratify_labels = table["_patient_majority_label"] if stratify else None
    try:
        return train_test_split(
            table,
            test_size=test_size,
            random_state=seed,
            stratify=stratify_labels,
        )
    except ValueError:
        return train_test_split(table, test_size=test_size, random_state=seed, stratify=None)


def make_patient_splits(
    labels_csv: str | Path,
    output_dir: str | Path,
    patient_col: str = "patient_id",
    label_col: str = "label",
    group_col: str | None = None,
    val_size: float = 0.15,
    test_size: float = 0.15,
    seed: int = 42,
    stratify_by_label: bool = True,
    deduplicate_by_group: bool = False,
) -> dict[str, Path]:
    labels_csv = Path(labels_csv)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(labels_csv)
    missing = [col for col in [patient_col, label_col] if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}")
    if group_col and group_col not in df.columns:
        raise ValueError(f"Missing group column: {group_col}")
    if deduplicate_by_group and not group_col:
        raise ValueError("deduplicate_by_group=True requires an explicit group_col")

    split_group_col = group_col if group_col else patient_col
    if split_group_col != patient_col:
        df = df.copy()
        df["_split_group"] = df[split_group_col].fillna("").astype(str)
        empty_group = df["_split_group"].str.strip().eq("")
        df.loc[empty_group, "_split_group"] = df.loc[empty_group, patient_col].astype(str)
        split_group_col = "_split_group"

    patient_table = _patient_label_table(df, split_group_col, label_col)
    train_val_patients, test_patients = _safe_train_test_split(
        patient_table,
        test_size=test_size,
        seed=seed,
        stratify=stratify_by_label,
    )

    relative_val_size = val_size / (1.0 - test_size)
    train_patients, val_patients = _safe_train_test_split(
        train_val_patients,
        test_size=relative_val_size,
        seed=seed,
        stratify=stratify_by_label,
    )

    patient_sets = {
        "train": set(train_patients[split_group_col]),
        "val": set(val_patients[split_group_col]),
        "test": set(test_patients[split_group_col]),
    }

    paths: dict[str, Path] = {}
    for split_name, split_group_ids in patient_sets.items():
        split_df = df[df[split_group_col].isin(split_group_ids)].copy()
        if deduplicate_by_group:
            split_df = split_df.drop_duplicates(subset=[split_group_col], keep="first").copy()
        split_df["split"] = split_name
        if "_split_group" in split_df.columns:
            split_df = split_df.drop(columns=["_split_group"])
        path = output_dir / f"{split_name}.csv"
        split_df.to_csv(path, index=False)
        paths[split_name] = path

    return paths
