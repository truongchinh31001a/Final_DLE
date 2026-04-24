from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset


class OtoscopyImageDataset(Dataset):
    def __init__(
        self,
        labels: str | Path | pd.DataFrame,
        image_root: str | Path,
        class_names: list[str],
        image_col: str = "image_path",
        label_col: str = "label",
        transform: Any | None = None,
    ) -> None:
        self.df = pd.read_csv(labels) if isinstance(labels, (str, Path)) else labels.copy()
        self.image_root = Path(image_root)
        self.image_col = image_col
        self.label_col = label_col
        self.transform = transform
        self.class_names = class_names
        self.class_to_idx = {name: idx for idx, name in enumerate(class_names)}

        missing_columns = [col for col in [image_col, label_col] if col not in self.df.columns]
        if missing_columns:
            raise ValueError(f"Missing required column(s): {missing_columns}")
        if self.df[label_col].isna().any():
            raise ValueError(f"Missing labels found in column: {label_col}")

        unknown = sorted(set(self.df[label_col].dropna().unique()) - set(class_names))
        if unknown:
            raise ValueError(f"Unknown labels in dataset: {unknown}")

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
        row = self.df.iloc[index]
        image_path = Path(row[self.image_col])
        if not image_path.is_absolute():
            image_path = self.image_root / image_path

        image = Image.open(image_path).convert("RGB")
        if self.transform is not None:
            image = self.transform(image)

        label_idx = self.class_to_idx[row[self.label_col]]
        target = torch.tensor(label_idx, dtype=torch.long)
        meta = row.to_dict()
        meta["resolved_image_path"] = str(image_path)
        return image, target, meta
