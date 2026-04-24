from __future__ import annotations

from typing import Final

DEFAULT_MODEL_ID: Final[str] = "baseline_effb0"

MODEL_REGISTRY: Final[dict[str, dict[str, str]]] = {
    "baseline_effb0": {
        "label": "EfficientNet-B0",
        "checkpoint": "models/checkpoints/baseline_effb0/best.pt",
    },
    "baseline_resnet18": {
        "label": "ResNet18",
        "checkpoint": "models/checkpoints/baseline_resnet18/best.pt",
    },
    "baseline_custom_cnn": {
        "label": "Custom CNN",
        "checkpoint": "models/checkpoints/baseline_custom_cnn/best.pt",
    },
}


def list_available_models() -> list[dict[str, str]]:
    return [
        {
            "id": model_id,
            "label": meta["label"],
            "checkpoint": meta["checkpoint"],
        }
        for model_id, meta in MODEL_REGISTRY.items()
    ]


def is_valid_model_id(model_id: str | None) -> bool:
    return bool(model_id) and model_id in MODEL_REGISTRY


def resolve_model_checkpoint(model_id: str | None = None, checkpoint: str | None = None) -> str | None:
    if checkpoint:
        return checkpoint
    if model_id and model_id in MODEL_REGISTRY:
        return MODEL_REGISTRY[model_id]["checkpoint"]
    return None
