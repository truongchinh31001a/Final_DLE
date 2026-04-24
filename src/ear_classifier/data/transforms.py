from __future__ import annotations

from typing import Any

from torchvision import transforms


def _as_size(image_size: int | list[int] | tuple[int, int]) -> tuple[int, int]:
    if isinstance(image_size, int):
        return (image_size, image_size)
    if len(image_size) != 2:
        raise ValueError("image_size must be an int or a pair of ints")
    return (int(image_size[0]), int(image_size[1]))


def _as_tuple(value: Any, cast) -> Any:
    if isinstance(value, (list, tuple)):
        return tuple(cast(item) for item in value)
    return cast(value)


def build_transforms(data_cfg: dict[str, Any], train: bool) -> transforms.Compose:
    image_size = _as_size(data_cfg.get("image_size", 224))
    normalization = data_cfg.get("normalization", {})
    mean = normalization.get("mean", [0.485, 0.456, 0.406])
    std = normalization.get("std", [0.229, 0.224, 0.225])

    ops: list[Any] = []
    if train:
        aug = data_cfg.get("augmentations", {})
        random_resized_crop = aug.get("random_resized_crop", {})
        hflip_prob = float(aug.get("horizontal_flip_prob", 0.0))
        rotation_degrees = float(aug.get("rotation_degrees", 0.0))
        random_affine = aug.get("random_affine", {})
        color_jitter = aug.get("color_jitter", {})
        gaussian_blur = aug.get("gaussian_blur", {})
        random_erasing = aug.get("random_erasing", {})

        if random_resized_crop:
            ops.append(
                transforms.RandomResizedCrop(
                    image_size,
                    scale=_as_tuple(random_resized_crop.get("scale", [0.9, 1.0]), float),
                    ratio=_as_tuple(random_resized_crop.get("ratio", [0.95, 1.05]), float),
                )
            )
        else:
            ops.append(transforms.Resize(image_size))

        if hflip_prob > 0:
            ops.append(transforms.RandomHorizontalFlip(p=hflip_prob))
        if rotation_degrees > 0:
            ops.append(transforms.RandomRotation(degrees=rotation_degrees))
        if random_affine:
            ops.append(
                transforms.RandomAffine(
                    degrees=_as_tuple(random_affine.get("degrees", 0.0), float),
                    translate=_as_tuple(random_affine.get("translate", [0.0, 0.0]), float)
                    if "translate" in random_affine
                    else None,
                    scale=_as_tuple(random_affine.get("scale", [1.0, 1.0]), float)
                    if "scale" in random_affine
                    else None,
                    shear=_as_tuple(random_affine.get("shear", 0.0), float)
                    if "shear" in random_affine
                    else None,
                )
            )
        if color_jitter:
            ops.append(transforms.ColorJitter(**color_jitter))
        if gaussian_blur:
            blur_prob = float(gaussian_blur.get("prob", 0.0))
            if blur_prob > 0:
                ops.append(
                    transforms.RandomApply(
                        [
                            transforms.GaussianBlur(
                                kernel_size=int(gaussian_blur.get("kernel_size", 3)),
                                sigma=_as_tuple(gaussian_blur.get("sigma", [0.1, 1.0]), float),
                            )
                        ],
                        p=blur_prob,
                    )
                )
    else:
        aug = {}
        random_erasing = {}
        ops.append(transforms.Resize(image_size))

    ops.append(transforms.ToTensor())
    if train and random_erasing:
        erasing_prob = float(random_erasing.get("p", 0.0))
        if erasing_prob > 0:
            erasing_value = random_erasing.get("value", 0.0)
            if isinstance(erasing_value, list):
                erasing_value = tuple(float(item) for item in erasing_value)
            ops.append(
                transforms.RandomErasing(
                    p=erasing_prob,
                    scale=_as_tuple(random_erasing.get("scale", [0.02, 0.12]), float),
                    ratio=_as_tuple(random_erasing.get("ratio", [0.3, 3.3]), float),
                    value=erasing_value,
                )
            )
    ops.append(transforms.Normalize(mean=mean, std=std))
    return transforms.Compose(ops)
