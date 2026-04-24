from __future__ import annotations

import torch.nn as nn

from ear_classifier.models.custom_cnn import CustomCNN


def _build_timm_model(
    model_name: str,
    num_classes: int,
    pretrained: bool,
    dropout: float,
) -> nn.Module:
    try:
        import timm
    except ImportError as exc:
        raise ImportError(
            "timm is required for model.library='timm'. Install it with: python -m pip install timm"
        ) from exc

    return timm.create_model(
        model_name,
        pretrained=pretrained,
        num_classes=num_classes,
        drop_rate=dropout,
    )


def _build_torchvision_model(model_name: str, num_classes: int, pretrained: bool) -> nn.Module:
    from torchvision import models

    if model_name == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model
    if model_name == "resnet50":
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        model = models.resnet50(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model
    if model_name == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
        return model
    raise ValueError(f"Unsupported torchvision model: {model_name}")


def build_model(
    model_name: str,
    num_classes: int,
    pretrained: bool = True,
    dropout: float = 0.0,
    library: str = "auto",
    **kwargs,
) -> nn.Module:
    if model_name == "custom_cnn":
        if library.lower() not in {"auto", "custom"}:
            raise ValueError("custom_cnn must use model.library='custom' or 'auto'")
        return CustomCNN(
            num_classes=num_classes,
            dropout=dropout,
            head_hidden_dim=int(kwargs.get("head_hidden_dim", 128)),
        )

    library = library.lower()
    if library == "timm":
        return _build_timm_model(model_name, num_classes, pretrained, dropout)
    if library == "torchvision":
        return _build_torchvision_model(model_name, num_classes, pretrained)
    if library != "auto":
        raise ValueError("model library must be one of: auto, timm, torchvision")

    try:
        return _build_timm_model(model_name, num_classes, pretrained, dropout)
    except ImportError:
        return _build_torchvision_model(model_name, num_classes, pretrained)
