from __future__ import annotations

import torch

from ear_classifier.models.classifier import build_model


def test_resnet18_forward_shape() -> None:
    model = build_model(
        "resnet18",
        num_classes=5,
        pretrained=False,
        library="torchvision",
    )
    model.eval()

    with torch.inference_mode():
        logits = model(torch.randn(2, 3, 224, 224))

    assert tuple(logits.shape) == (2, 5)


def test_custom_cnn_forward_shape() -> None:
    model = build_model(
        "custom_cnn",
        num_classes=5,
        pretrained=False,
        dropout=0.3,
        library="custom",
    )
    model.eval()

    with torch.inference_mode():
        logits = model(torch.randn(2, 3, 224, 224))

    assert tuple(logits.shape) == (2, 5)
