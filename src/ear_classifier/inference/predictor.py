from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from PIL import Image

from ear_classifier.config import get_device, load_data_config, load_yaml, resolve_from_config
from ear_classifier.data.transforms import build_transforms
from ear_classifier.models.classifier import build_model


class OtoscopyPredictor:
    def __init__(
        self,
        config_path: str | Path,
        checkpoint_path: str | Path | None = None,
    ) -> None:
        self.config_path = Path(config_path)
        cfg = load_yaml(self.config_path)
        data_config_path = resolve_from_config(
            self.config_path,
            cfg.get("data_config", "configs/data.yaml"),
        )
        self.data_cfg = load_data_config(data_config_path)
        self.class_names = self.data_cfg["classes"]
        self.device = get_device(cfg.get("device", "auto"))
        self.top_k = int(cfg.get("top_k", 3))

        checkpoint_path = checkpoint_path or cfg["checkpoint"]
        checkpoint_path = resolve_from_config(self.config_path, checkpoint_path)
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        model_cfg: dict[str, Any] = checkpoint.get("model_config", {"name": "efficientnet_b0"})
        self.model = build_model(
            model_name=model_cfg.get("name", "efficientnet_b0"),
            num_classes=len(self.class_names),
            pretrained=False,
            dropout=float(model_cfg.get("dropout", 0.0)),
            library=model_cfg.get("library", "auto"),
            head_hidden_dim=model_cfg.get("head_hidden_dim", 256),
            cbam_reduction=model_cfg.get("cbam_reduction", 16),
            spatial_kernel_size=model_cfg.get("spatial_kernel_size", 7),
        ).to(self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()
        self.transform = build_transforms(self.data_cfg, train=False)

    @staticmethod
    def _format_label(label: str) -> str:
        return label.replace("_", " ")

    @torch.inference_mode()
    def predict(self, image_path: str | Path) -> dict[str, Any]:
        image = Image.open(image_path).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0).cpu()
        top_k = min(self.top_k, len(self.class_names))
        values, indices = torch.topk(probs, k=top_k)
        predictions = [
            {
                "label": self._format_label(self.class_names[int(idx)]),
                "probability": float(prob),
            }
            for prob, idx in zip(values, indices, strict=True)
        ]
        return {
            "label": predictions[0]["label"],
            "confidence": predictions[0]["probability"],
            "top_k": predictions,
        }
