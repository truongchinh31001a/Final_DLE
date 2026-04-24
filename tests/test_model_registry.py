from __future__ import annotations

from ear_classifier.inference.model_registry import (
    DEFAULT_MODEL_ID,
    list_available_models,
    resolve_model_checkpoint,
)


def test_resolve_model_checkpoint_uses_registry() -> None:
    assert resolve_model_checkpoint(DEFAULT_MODEL_ID) == "models/checkpoints/baseline_effb0/best.pt"


def test_resolve_model_checkpoint_prefers_explicit_checkpoint() -> None:
    assert resolve_model_checkpoint(DEFAULT_MODEL_ID, checkpoint="custom/best.pt") == "custom/best.pt"


def test_list_available_models_contains_default_model() -> None:
    model_ids = {item["id"] for item in list_available_models()}
    assert DEFAULT_MODEL_ID in model_ids
