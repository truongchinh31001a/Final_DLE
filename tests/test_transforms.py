from __future__ import annotations

from PIL import Image

from ear_classifier.data.transforms import build_transforms


def test_build_transforms_with_strong_augmentations() -> None:
    cfg = {
        "image_size": 224,
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
        },
        "augmentations": {
            "random_resized_crop": {"scale": [0.82, 1.0], "ratio": [0.9, 1.1]},
            "horizontal_flip_prob": 0.5,
            "random_affine": {
                "degrees": 12,
                "translate": [0.04, 0.04],
                "scale": [0.92, 1.08],
                "shear": [-5, 5],
            },
            "color_jitter": {
                "brightness": 0.18,
                "contrast": 0.18,
                "saturation": 0.12,
                "hue": 0.03,
            },
            "gaussian_blur": {"prob": 0.15, "kernel_size": 3, "sigma": [0.1, 0.8]},
            "random_erasing": {
                "p": 0.2,
                "scale": [0.02, 0.1],
                "ratio": [0.3, 3.0],
                "value": "random",
            },
        },
    }
    image = Image.new("RGB", (256, 256), color=(128, 64, 32))

    transform = build_transforms(cfg, train=True)
    tensor = transform(image)

    assert tuple(tensor.shape) == (3, 224, 224)
