from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)


def classification_metrics(
    y_true: list[int] | np.ndarray,
    y_prob: list[list[float]] | np.ndarray,
    class_names: list[str],
) -> dict[str, Any]:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    y_pred = y_prob.argmax(axis=1)

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=list(range(len(class_names))),
            target_names=class_names,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(
            y_true,
            y_pred,
            labels=list(range(len(class_names))),
        ).tolist(),
    }

    try:
        if len(class_names) == 2:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob[:, 1]))
        else:
            metrics["roc_auc_ovr_macro"] = float(
                roc_auc_score(y_true, y_prob, multi_class="ovr", average="macro")
            )
    except ValueError:
        metrics["roc_auc_note"] = "ROC-AUC unavailable because at least one class is missing."

    return metrics

