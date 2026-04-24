from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def resolve_project_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def slugify(value: str) -> str:
    import re

    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def load_label_mapping(path: str | Path) -> dict[str, str]:
    config = load_yaml(path)
    mapping: dict[str, str] = {}
    for standard_label, aliases in config.get("standard_labels", {}).items():
        mapping[slugify(standard_label)] = standard_label
        for alias in aliases or []:
            mapping[slugify(alias)] = standard_label
    return mapping

