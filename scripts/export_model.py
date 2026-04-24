from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ear_classifier.config import load_training_config
from ear_classifier.models.classifier import build_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a trained checkpoint to ONNX.")
    parser.add_argument("--config", default="configs/train.yaml", help="Path to train config.")
    parser.add_argument("--checkpoint", required=True, help="Path to checkpoint.")
    parser.add_argument("--output", default="models/exported/model.onnx", help="Output ONNX path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_training_config(args.config)
    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    model_cfg = checkpoint.get("model_config", cfg["model"])
    model = build_model(
        model_name=model_cfg.get("name", "efficientnet_b0"),
        num_classes=len(cfg["data"]["classes"]),
        pretrained=False,
        dropout=float(model_cfg.get("dropout", 0.0)),
        library=model_cfg.get("library", "auto"),
        head_hidden_dim=model_cfg.get("head_hidden_dim", 256),
        cbam_reduction=model_cfg.get("cbam_reduction", 16),
        spatial_kernel_size=model_cfg.get("spatial_kernel_size", 7),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    image_size = cfg["data"].get("image_size", 224)
    if isinstance(image_size, list):
        height, width = image_size
    else:
        height = width = int(image_size)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.randn(1, 3, height, width)
    torch.onnx.export(
        model,
        dummy,
        output,
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={"image": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    print(f"Exported {output}")


if __name__ == "__main__":
    main()
