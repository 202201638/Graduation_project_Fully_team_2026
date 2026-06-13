from typing import Dict, List, Optional
import copy
import time
import os

import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def _compute_class_weights(train_loader: DataLoader, device: torch.device) -> Optional[torch.Tensor]:
    dataset = train_loader.dataset
    if not hasattr(dataset, "get_labels"):
        return None
    labels = dataset.get_labels()
    n0 = labels.count(0)
    n1 = labels.count(1)
    total = n0 + n1
    if n0 == 0 or n1 == 0:
        return None
    # inverse-frequency weights, normalized so the mean weight is ~1
    w = torch.tensor([total / (2.0 * n0), total / (2.0 * n1)], dtype=torch.float32)
    print(f"Class counts: normal={n0}, pneumonia={n1} | class_weights={w.tolist()}", flush=True)
    return w.to(device)


def _head_param_ids(model: nn.Module) -> set:
    ids = set()
    for attr in ("fc", "classifier"):
        head = getattr(model, attr, None)
        if head is not None:
            ids |= {id(p) for p in head.parameters()}
    return ids


def _set_backbone_frozen(model: nn.Module, frozen: bool) -> None:
    head_ids = _head_param_ids(model)
    for p in model.parameters():
        p.requires_grad = True if (id(p) in head_ids) else (not frozen)


@torch.no_grad()
def _evaluate(model, loader, criterion, device, max_batches: Optional[int] = None) -> Dict:
    model.eval()
    targets: List[int] = []
    preds: List[int] = []
    probs: List[float] = []
    loss_sum = 0.0
    batches = 0
    for images, labels in loader:
        if max_batches is not None and batches >= max_batches:
            break
        batches += 1
        images = images.to(device)
        labels = labels.to(device)
        logits = model(images)
        loss_sum += criterion(logits, labels).item()
        p = torch.softmax(logits, dim=1)[:, 1]
        targets.extend(labels.cpu().tolist())
        preds.extend((p >= 0.5).long().cpu().tolist())
        probs.extend(p.cpu().tolist())

    try:
        auc = roc_auc_score(targets, probs)
    except ValueError:
        auc = 0.5
    cm = confusion_matrix(targets, preds, labels=[0, 1]).tolist()
    return {
        "loss": loss_sum / max(1, batches),
        "accuracy": accuracy_score(targets, preds),
        "precision": precision_score(targets, preds, zero_division=0),
        "recall": recall_score(targets, preds, zero_division=0),
        "f1": f1_score(targets, preds, zero_division=0),
        "auc": auc,
        "confusion_matrix": cm,
    }


def train_classifier(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
    epochs: int = 8,
    lr: float = 1e-4,
    weight_decay: float = 1e-4,
    checkpoint_path: Optional[str] = None,
    patience: int = 4,
    freeze_epochs: int = 0,
    test_loader: Optional[DataLoader] = None,
    use_class_weights: bool = True,
    max_train_batches: Optional[int] = None,
    max_eval_batches: Optional[int] = None,
) -> Dict:
    """Train a binary classifier with class weighting, AMP, LR scheduling on val
    AUC, early stopping, best-checkpoint restore, and full per-epoch history.
    Final metrics are reported on `test_loader` if given, else on `val_loader`."""
    model.to(device)

    class_weights = _compute_class_weights(train_loader, device) if use_class_weights else None
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)

    use_amp = device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    print(
        f"Starting classifier training on {device} | epochs={epochs}, lr={lr}, "
        f"weight_decay={weight_decay}, patience={patience}, freeze_epochs={freeze_epochs}",
        flush=True,
    )

    history: List[Dict] = []
    best_auc = -1.0
    best_epoch = -1
    best_state = copy.deepcopy(model.state_dict())
    epochs_no_improve = 0
    backbone_frozen = freeze_epochs > 0
    if backbone_frozen:
        _set_backbone_frozen(model, True)

    for epoch in range(epochs):
        if backbone_frozen and epoch >= freeze_epochs:
            _set_backbone_frozen(model, False)
            backbone_frozen = False
            print(f"[Classifier] Unfroze backbone at epoch {epoch+1}", flush=True)

        model.train()
        running_loss = 0.0
        epoch_start = time.time()
        num_batches = len(train_loader)

        for batch_idx, (images, labels) in enumerate(train_loader, start=1):
            if max_train_batches is not None and batch_idx > max_train_batches:
                break
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            with torch.amp.autocast("cuda", enabled=use_amp):
                logits = model(images)
                loss = criterion(logits, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item()
            if batch_idx % 50 == 0 or batch_idx == num_batches:
                elapsed = time.time() - epoch_start
                print(
                    f"[Classifier] Epoch {epoch+1}/{epochs} | batch {batch_idx}/{num_batches} | "
                    f"loss={loss.item():.4f} | elapsed={elapsed:.1f}s",
                    flush=True,
                )

        ran_batches = min(num_batches, max_train_batches) if max_train_batches else num_batches
        train_loss = running_loss / max(1, ran_batches)
        val = _evaluate(model, val_loader, criterion, device, max_batches=max_eval_batches)
        scheduler.step(val["auc"])
        history.append(
            {
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "val_loss": val["loss"],
                "val_accuracy": val["accuracy"],
                "val_f1": val["f1"],
                "val_auc": val["auc"],
                "lr": optimizer.param_groups[0]["lr"],
            }
        )
        print(
            f"Epoch {epoch+1}/{epochs} - train_loss={train_loss:.4f} - val_loss={val['loss']:.4f} "
            f"- val_acc={val['accuracy']:.4f} - val_f1={val['f1']:.4f} - val_auc={val['auc']:.4f}",
            flush=True,
        )

        if val["auc"] > best_auc + 1e-4:
            best_auc = val["auc"]
            best_epoch = epoch + 1
            best_state = copy.deepcopy(model.state_dict())
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping at epoch {epoch+1} (best val_auc={best_auc:.4f} @ epoch {best_epoch})", flush=True)
                break

    # restore best weights before final eval / checkpoint
    model.load_state_dict(best_state)

    eval_split = "test" if test_loader is not None else "val"
    final = _evaluate(
        model,
        test_loader if test_loader is not None else val_loader,
        criterion,
        device,
        max_batches=max_eval_batches,
    )
    print(
        f"Final ({eval_split}) - acc={final['accuracy']:.4f} - precision={final['precision']:.4f} "
        f"- recall={final['recall']:.4f} - f1={final['f1']:.4f} - auc={final['auc']:.4f}",
        flush=True,
    )

    if checkpoint_path:
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        torch.save(model.state_dict(), checkpoint_path)
        print(f"Saved best classifier checkpoint to {checkpoint_path}", flush=True)

    return {
        "accuracy": float(final["accuracy"]),
        "precision": float(final["precision"]),
        "recall": float(final["recall"]),
        "f1": float(final["f1"]),
        "auc": float(final["auc"]),
        "confusion_matrix": final["confusion_matrix"],
        "eval_split": eval_split,
        "best_val_auc": float(best_auc),
        "best_epoch": best_epoch,
        "epochs_ran": len(history),
        "history": history,
    }


def run_classifier_training(
    model: nn.Module,
    model_name: str,
    *,
    epochs: int,
    lr: float,
    batch_size: int,
    dropout: float,
    weight_decay: float,
    checkpoint_path: Optional[str],
    patience: int = 4,
    freeze_epochs: int = 0,
    num_workers: int = 2,
    eval_on_test: bool = True,
    max_train_batches: Optional[int] = None,
    max_eval_batches: Optional[int] = None,
) -> Dict:
    """Build dataloaders, train, and return a thesis-ready metrics + parameters dict
    for a single classifier. Shared by all classification wrappers."""
    from src.classification.data import (
        create_classification_dataloaders,
        create_classification_test_loader,
    )
    from src.config import CLS_IMG_SIZE

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, val_loader = create_classification_dataloaders(
        batch_size=batch_size, num_workers=num_workers
    )
    test_loader = (
        create_classification_test_loader(batch_size=batch_size, num_workers=num_workers)
        if eval_on_test
        else None
    )

    metrics = train_classifier(
        model,
        train_loader,
        val_loader,
        device,
        epochs=epochs,
        lr=lr,
        weight_decay=weight_decay,
        checkpoint_path=checkpoint_path,
        patience=patience,
        freeze_epochs=freeze_epochs,
        test_loader=test_loader,
        max_train_batches=max_train_batches,
        max_eval_batches=max_eval_batches,
    )

    metrics.update(
        {
            "model": model_name,
            "task": "classification",
            "model_path": os.path.normpath(checkpoint_path) if checkpoint_path else None,
            "num_parameters": int(sum(p.numel() for p in model.parameters())),
            "hyperparameters": {
                "epochs": epochs,
                "lr": lr,
                "batch_size": batch_size,
                "dropout": dropout,
                "weight_decay": weight_decay,
                "img_size": CLS_IMG_SIZE,
                "optimizer": "Adam",
                "loss": "CrossEntropyLoss (class-weighted)",
                "lr_scheduler": "ReduceLROnPlateau(mode=max, factor=0.5, patience=2)",
                "patience": patience,
                "freeze_epochs": freeze_epochs,
                "augmentation": "train-only: hflip, rotate(10), color jitter; ImageNet-normalized",
            },
        }
    )
    print(
        f"{model_name} [{metrics['eval_split']}] - Accuracy: {metrics['accuracy']:.4f}, "
        f"F1: {metrics['f1']:.4f}, AUC: {metrics['auc']:.4f}",
        flush=True,
    )
    return metrics
