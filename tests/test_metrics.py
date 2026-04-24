from __future__ import annotations

from ear_classifier.evaluation.metrics import classification_metrics


def test_classification_metrics_returns_core_metrics() -> None:
    metrics = classification_metrics(
        y_true=[0, 1, 1, 0],
        y_prob=[
            [0.9, 0.1],
            [0.2, 0.8],
            [0.7, 0.3],
            [0.6, 0.4],
        ],
        class_names=["normal", "otitis_media"],
    )

    assert metrics["accuracy"] == 0.75
    assert "macro_f1" in metrics
    assert metrics["confusion_matrix"] == [[2, 0], [1, 1]]

