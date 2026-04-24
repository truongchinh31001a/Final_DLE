from __future__ import annotations

import pandas as pd
from PIL import Image
from torchvision import transforms

from ear_classifier.data.dataset import OtoscopyImageDataset


def test_dataset_loads_image_and_label(tmp_path) -> None:
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    image_path = image_dir / "sample.jpg"
    Image.new("RGB", (16, 16), color=(255, 0, 0)).save(image_path)

    labels = pd.DataFrame(
        [
            {
                "image_id": "sample",
                "image_path": "sample.jpg",
                "patient_id": "P001",
                "label": "normal",
            }
        ]
    )
    dataset = OtoscopyImageDataset(
        labels=labels,
        image_root=image_dir,
        class_names=["normal", "otitis_media"],
        transform=transforms.ToTensor(),
    )

    image, target, meta = dataset[0]

    assert tuple(image.shape) == (3, 16, 16)
    assert int(target) == 0
    assert meta["patient_id"] == "P001"

