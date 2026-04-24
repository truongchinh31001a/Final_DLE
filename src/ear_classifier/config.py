from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def resolve_from_config(config_path: str | Path, maybe_relative_path: str | Path) -> Path:
    path = Path(maybe_relative_path)
    if path.is_absolute():
        return path
    config_dir = Path(config_path).resolve().parent
    config_relative = (config_dir / path).resolve()
    if config_relative.exists():
        return config_relative
    return (config_dir.parent / path).resolve()


def load_data_config(path: str | Path) -> dict[str, Any]:
    raw = load_yaml(path)
    data = raw.get("data", raw)
    data["_config_path"] = str(Path(path).resolve())
    return data


def load_training_config(path: str | Path) -> dict[str, Any]:
    cfg = load_yaml(path)
    data_config_path = cfg.get("data_config", "configs/data.yaml")
    data_config_path = resolve_from_config(path, data_config_path)
    cfg["data"] = load_data_config(data_config_path)
    cfg["_config_path"] = str(Path(path).resolve())
    return cfg


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def get_device(requested: str = "auto") -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)
