from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader
from tqdm.auto import tqdm

from ear_classifier.config import get_device, load_training_config, set_seed
from ear_classifier.data.dataset import OtoscopyImageDataset
from ear_classifier.data.transforms import build_transforms
from ear_classifier.evaluation.metrics import classification_metrics
from ear_classifier.models.classifier import build_model


def _resolve_project_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else Path.cwd() / path


def _build_dataset(cfg: dict[str, Any], split: str) -> OtoscopyImageDataset:
    data_cfg = cfg["data"]
    columns = data_cfg.get("columns", {})
    split_csv = _resolve_project_path(data_cfg["splits_dir"]) / f"{split}.csv"
    return OtoscopyImageDataset(
        labels=split_csv,
        image_root=_resolve_project_path(data_cfg["image_root"]),
        class_names=data_cfg["classes"],
        image_col=columns.get("image_path", "image_path"),
        label_col=columns.get("label", "label"),
        transform=build_transforms(data_cfg, train=split == "train"),
    )


def _class_weights(
    dataset: OtoscopyImageDataset,
    mode: str,
    device: torch.device,
) -> torch.Tensor | None:
    if mode != "balanced":
        return None
    labels = dataset.df[dataset.label_col].map(dataset.class_to_idx).to_numpy()
    observed_classes = np.unique(labels)
    weights = np.ones(len(dataset.class_names), dtype=np.float32)
    if len(observed_classes) == 0:
        return torch.tensor(weights, dtype=torch.float32, device=device)
    observed_weights = compute_class_weight(
        class_weight="balanced",
        classes=observed_classes,
        y=labels,
    )
    weights[observed_classes] = observed_weights.astype(np.float32)
    return torch.tensor(weights, dtype=torch.float32, device=device)


def _mlflow_context(cfg: dict[str, Any], run_name: str):
    mlflow_cfg = cfg.get("tracking", {}).get("mlflow", {})
    if not mlflow_cfg.get("enabled", False):
        return nullcontext(None)
    try:
        import mlflow
    except ImportError as exc:
        raise ImportError(
            "MLflow tracking is enabled in the training config, but the 'mlflow' package "
            'is not installed. Install it with `python -m pip install -e ".[tracking]"` '
            "or disable `tracking.mlflow.enabled` in the config."
        ) from exc

    mlflow.set_experiment(mlflow_cfg.get("experiment_name", "ear-disease-classifier"))
    return mlflow.start_run(run_name=run_name)


def _log_mlflow_epoch(epoch: int, record: dict[str, Any]) -> None:
    try:
        import mlflow
    except ImportError:
        return

    mlflow.log_metric("train_loss", record["train"]["loss"], step=epoch)
    mlflow.log_metric("train_accuracy", record["train"]["accuracy"], step=epoch)
    mlflow.log_metric("val_loss", record["val"]["loss"], step=epoch)
    for key in ["accuracy", "macro_f1", "weighted_f1", "balanced_accuracy"]:
        if key in record["val"]:
            mlflow.log_metric(f"val_{key}", record["val"][key], step=epoch)
    mlflow.log_metric("learning_rate", record["lr"], step=epoch)


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    amp: bool,
) -> dict[str, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    scaler = torch.cuda.amp.GradScaler(enabled=amp)

    for images, targets, _meta in tqdm(loader, desc="train", leave=False):
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)
        with torch.cuda.amp.autocast(enabled=amp):
            logits = model(images)
            loss = criterion(logits, targets)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        batch_size = targets.size(0)
        running_loss += float(loss.item()) * batch_size
        correct += int((logits.argmax(dim=1) == targets).sum().item())
        total += batch_size

    return {"loss": running_loss / total, "accuracy": correct / total}


@torch.inference_mode()
def evaluate_loader(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    class_names: list[str],
) -> dict[str, Any]:
    model.eval()
    running_loss = 0.0
    total = 0
    y_true: list[int] = []
    y_prob: list[list[float]] = []

    for images, targets, _meta in tqdm(loader, desc="eval", leave=False):
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)
        logits = model(images)
        loss = criterion(logits, targets)
        probs = torch.softmax(logits, dim=1)

        batch_size = targets.size(0)
        running_loss += float(loss.item()) * batch_size
        total += batch_size
        y_true.extend(targets.cpu().tolist())
        y_prob.extend(probs.cpu().tolist())

    metrics = classification_metrics(y_true, y_prob, class_names)
    metrics["loss"] = running_loss / total
    return metrics


def _save_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    cfg: dict[str, Any],
    metrics: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "model_config": cfg["model"],
            "class_names": cfg["data"]["classes"],
            "metrics": metrics,
        },
        path,
    )


def run_training(config_path: str | Path) -> dict[str, Any]:
    cfg = load_training_config(config_path)
    train_cfg = cfg.get("train", {})
    output_cfg = cfg.get("output", {})
    set_seed(int(train_cfg.get("seed", cfg["data"].get("seed", 42))))

    run_name = train_cfg.get("run_name", "baseline")
    device = get_device(train_cfg.get("device", "auto"))
    amp = bool(train_cfg.get("amp", True)) and device.type == "cuda"

    train_ds = _build_dataset(cfg, "train")
    val_ds = _build_dataset(cfg, "val")
    pin_memory = device.type == "cuda"
    train_loader = DataLoader(
        train_ds,
        batch_size=int(train_cfg.get("batch_size", 32)),
        shuffle=True,
        num_workers=int(train_cfg.get("num_workers", 4)),
        pin_memory=pin_memory,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=int(train_cfg.get("batch_size", 32)),
        shuffle=False,
        num_workers=int(train_cfg.get("num_workers", 4)),
        pin_memory=pin_memory,
    )

    model_cfg = cfg["model"]
    model = build_model(
        model_name=model_cfg.get("name", "efficientnet_b0"),
        num_classes=len(cfg["data"]["classes"]),
        pretrained=bool(model_cfg.get("pretrained", True)),
        dropout=float(model_cfg.get("dropout", 0.0)),
        library=model_cfg.get("library", "auto"),
        head_hidden_dim=model_cfg.get("head_hidden_dim", 256),
        cbam_reduction=model_cfg.get("cbam_reduction", 16),
        spatial_kernel_size=model_cfg.get("spatial_kernel_size", 7),
    ).to(device)
    criterion = nn.CrossEntropyLoss(
        weight=_class_weights(train_ds, train_cfg.get("class_weights", "none"), device)
    )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(train_cfg.get("learning_rate", 3e-4)),
        weight_decay=float(train_cfg.get("weight_decay", 1e-4)),
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=int(train_cfg.get("epochs", 30)),
    )

    checkpoint_dir = _resolve_project_path(output_cfg.get("checkpoint_dir", "models/checkpoints")) / run_name
    metrics_dir = _resolve_project_path(output_cfg.get("metrics_dir", "reports/metrics")) / run_name
    metrics_dir.mkdir(parents=True, exist_ok=True)

    monitor = train_cfg.get("monitor", "macro_f1")
    patience = int(train_cfg.get("early_stopping_patience", 8))
    best_score = -float("inf")
    epochs_without_improvement = 0
    history: list[dict[str, Any]] = []

    with _mlflow_context(cfg, run_name) as mlflow_run:
        if mlflow_run is not None:
            import mlflow

            mlflow.log_params(
                {
                    "model_name": model_cfg.get("name", "efficientnet_b0"),
                    "model_library": model_cfg.get("library", "auto"),
                    "epochs": train_cfg.get("epochs", 30),
                    "batch_size": train_cfg.get("batch_size", 32),
                    "learning_rate": train_cfg.get("learning_rate", 3e-4),
                    "weight_decay": train_cfg.get("weight_decay", 1e-4),
                    "num_classes": len(cfg["data"]["classes"]),
                }
            )

        for epoch in range(1, int(train_cfg.get("epochs", 30)) + 1):
            train_metrics = train_one_epoch(model, train_loader, criterion, optimizer, device, amp)
            val_metrics = evaluate_loader(model, val_loader, criterion, device, cfg["data"]["classes"])
            scheduler.step()

            score = float(val_metrics.get(monitor, -val_metrics["loss"]))
            record = {
                "epoch": epoch,
                "train": train_metrics,
                "val": val_metrics,
                "lr": optimizer.param_groups[0]["lr"],
            }
            history.append(record)

            _save_checkpoint(checkpoint_dir / "latest.pt", model, optimizer, epoch, cfg, val_metrics)
            if score > best_score:
                best_score = score
                epochs_without_improvement = 0
                _save_checkpoint(checkpoint_dir / "best.pt", model, optimizer, epoch, cfg, val_metrics)
            else:
                epochs_without_improvement += 1

            with (metrics_dir / "history.json").open("w", encoding="utf-8") as file:
                json.dump(history, file, indent=2)

            if mlflow_run is not None:
                _log_mlflow_epoch(epoch, record)

            print(
                f"epoch={epoch} train_loss={train_metrics['loss']:.4f} "
                f"val_loss={val_metrics['loss']:.4f} val_{monitor}={score:.4f}"
            )

            if epochs_without_improvement >= patience:
                print(f"Early stopping after {epoch} epochs.")
                break

    return {"best_score": best_score, "history": history, "checkpoint_dir": str(checkpoint_dir)}


def run_evaluation(config_path: str | Path, checkpoint_path: str | Path, split: str = "test") -> dict[str, Any]:
    cfg = load_training_config(config_path)
    train_cfg = cfg.get("train", {})
    device = get_device(train_cfg.get("device", "auto"))

    dataset = _build_dataset(cfg, split)
    loader = DataLoader(
        dataset,
        batch_size=int(train_cfg.get("batch_size", 32)),
        shuffle=False,
        num_workers=int(train_cfg.get("num_workers", 4)),
        pin_memory=device.type == "cuda",
    )

    checkpoint = torch.load(checkpoint_path, map_location=device)
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
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])

    criterion = nn.CrossEntropyLoss()
    metrics = evaluate_loader(model, loader, criterion, device, cfg["data"]["classes"])

    metrics_base_dir = _resolve_project_path(cfg.get("output", {}).get("metrics_dir", "reports/metrics"))
    run_name = train_cfg.get("run_name", Path(checkpoint_path).parent.name)
    output_dir = metrics_base_dir / run_name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{split}_metrics.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)
    return metrics
