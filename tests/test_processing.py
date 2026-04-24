from __future__ import annotations

from PIL import Image

from ear_classifier.data.processing import content_crop_box


def test_content_crop_box_keeps_reasonable_content() -> None:
    image = Image.new("RGB", (20, 20), color=(0, 0, 0))
    for x in range(5, 15):
        for y in range(6, 16):
            image.putpixel((x, y), (120, 120, 120))

    assert content_crop_box(image, threshold=8, padding_ratio=0.0, min_content_area_ratio=0.1) == (
        5,
        6,
        15,
        16,
    )

