"""Shared training loop for the TorchVision detector (Faster R-CNN).

Adds the pieces the original 2-epoch loops lacked: linear LR warmup + cosine
decay, AMP, frozen-backbone warmup, mAP (via torchmetrics) alongside recall@0.5,
early stopping on the monitored metric, and best-checkpoint restore. Final metrics
are reported on the held-out test split.
"""
from typing import Dict, List, Optional, Callable
import copy
import os
import time

import torch
from torch.optim import SGD
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
from torchvision.ops import box_iou

from src.config import IMG_SIZE
from src.detection.data import create_dataloaders, create_detection_test_loader


def _try_make_map_metric():
    try:
        from torchmetrics.detection.mean_ap import MeanAveragePrecision

        return MeanAveragePrecision(box_format="xyxy", iou_type="bbox")
    except Exception as exc:  # torchmetrics/pycocotools missing or incompatible
        print(f"[Detector] torchmetrics mAP unavailable ({exc}); using recall@0.5 only.", flush=True)
        return None


def _freeze_backbone(model: torch.nn.Module, frozen: bool) -> None:
    backbone = getattr(model, "backbone", None)
    if backbone is None:
        return
    for p in backbone.parameters():
        p.requires_grad = not frozen


def sanitize_targets(targets: List[Dict]) -> List[Dict]:
    sanitized = []
    for t in targets:
        boxes = t["boxes"]
        labels = t["labels"]
        if boxes.numel() == 0:
            sanitized.append(t)
            continue
        finite_mask = torch.isfinite(boxes).all(dim=1)
        wh_mask = (boxes[:, 2] > boxes[:, 0]) & (boxes[:, 3] > boxes[:, 1])
        keep = finite_mask & wh_mask
        t["boxes"] = boxes[keep]
        t["labels"] = labels[keep]
        if "area" in t:
            t["area"] = t["area"][keep]
        if "iscrowd" in t:
            t["iscrowd"] = t["iscrowd"][keep]
        sanitized.append(t)
    return sanitized


@torch.no_grad()
def evaluate_detector(
    model, loader, device, iou_thr: float = 0.5, score_thr: float = 0.05, max_batches: Optional[int] = None
) -> Dict:
    model.eval()
    total_gt = 0
    total_tp = 0
    metric = _try_make_map_metric()

    for batch_idx, (images, targets) in enumerate(loader, start=1):
        if max_batches is not None and batch_idx > max_batches:
            break
        images = [img.to(device) for img in images]
        outputs = model(images)
        for output, target in zip(outputs, targets):
            gt_boxes = target["boxes"].to(device)
            pred_boxes = output["boxes"]
            pred_scores = output["scores"]

            if gt_boxes.numel() > 0:
                total_gt += gt_boxes.shape[0]
                keep = pred_scores >= score_thr
                kept_boxes = pred_boxes[keep] if keep.any() else pred_boxes
                if kept_boxes.numel() > 0:
                    ious = box_iou(gt_boxes, kept_boxes)
                    max_iou, _ = ious.max(dim=1)
                    total_tp += (max_iou >= iou_thr).sum().item()

            if metric is not None:
                metric.update(
                    [{
                        "boxes": pred_boxes.detach().cpu(),
                        "scores": pred_scores.detach().cpu(),
                        "labels": output["labels"].detach().cpu(),
                    }],
                    [{
                        "boxes": target["boxes"].detach().cpu(),
                        "labels": target["labels"].detach().cpu(),
                    }],
                )

    result = {"recall": total_tp / total_gt if total_gt > 0 else 0.0}
    if metric is not None:
        try:
            computed = metric.compute()
            result["map50"] = float(computed["map_50"])
            result["map"] = float(computed["map"])
        except Exception as exc:
            print(f"[Detector] mAP compute failed: {exc}", flush=True)
    return result


def train_torchvision_detector(
    model: torch.nn.Module,
    model_name: str,
    *,
    epochs: int,
    lr: float,
    batch_size: int,
    weight_decay: float,
    checkpoint_path: str,
    momentum: float = 0.9,
    patience: int = 3,
    freeze_epochs: int = 1,
    grad_clip: Optional[float] = None,
    sanitize: bool = False,
    eval_on_test: bool = True,
    num_workers: int = 2,
    max_train_batches: Optional[int] = None,
    max_eval_batches: Optional[int] = None,
) -> Dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    train_loader, val_loader = create_dataloaders(batch_size=batch_size, num_workers=num_workers)
    test_loader = create_detection_test_loader(batch_size=batch_size, num_workers=num_workers) if eval_on_test else None

    # optimizer holds ALL params; requires_grad toggling handles freeze/unfreeze
    optimizer = SGD(model.parameters(), lr=lr, momentum=momentum, weight_decay=weight_decay)

    steps_per_epoch = max(1, len(train_loader))
    total_iters = epochs * steps_per_epoch
    warmup_iters = max(1, min(500, total_iters // 20))
    warmup = LinearLR(optimizer, start_factor=0.01, total_iters=warmup_iters)
    cosine = CosineAnnealingLR(optimizer, T_max=max(1, total_iters - warmup_iters))
    scheduler = SequentialLR(optimizer, [warmup, cosine], milestones=[warmup_iters])

    use_amp = device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    backbone_frozen = freeze_epochs > 0
    _freeze_backbone(model, backbone_frozen)

    print(
        f"Starting {model_name} on {device} | epochs={epochs}, batch_size={batch_size}, lr={lr}, "
        f"weight_decay={weight_decay}, freeze_epochs={freeze_epochs}, warmup_iters={warmup_iters}",
        flush=True,
    )

    history: List[Dict] = []
    best_metric = -1.0
    best_metric_name = "map50"
    best_epoch = -1
    best_state = copy.deepcopy(model.state_dict())
    epochs_no_improve = 0

    for epoch in range(epochs):
        if backbone_frozen and epoch >= freeze_epochs:
            _freeze_backbone(model, False)
            backbone_frozen = False
            print(f"[{model_name}] Unfroze backbone at epoch {epoch+1}", flush=True)

        model.train()
        epoch_loss = 0.0
        epoch_start = time.time()
        num_batches = len(train_loader)

        for batch_idx, (images, targets) in enumerate(train_loader, start=1):
            if max_train_batches is not None and batch_idx > max_train_batches:
                break
            images = [img.to(device) for img in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            if sanitize:
                targets = sanitize_targets(targets)

            optimizer.zero_grad()
            with torch.amp.autocast("cuda", enabled=use_amp):
                loss_dict = model(images, targets)
                losses = sum(loss for loss in loss_dict.values())

            if not torch.isfinite(losses):
                print(f"[{model_name}] Skipping non-finite loss batch", flush=True)
                scheduler.step()
                continue

            scaler.scale(losses).backward()
            if grad_clip is not None:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=grad_clip)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            epoch_loss += losses.item()
            if batch_idx % 50 == 0 or batch_idx == num_batches:
                elapsed = time.time() - epoch_start
                print(
                    f"[{model_name}] Epoch {epoch+1}/{epochs} | batch {batch_idx}/{num_batches} | "
                    f"loss={losses.item():.4f} | lr={optimizer.param_groups[0]['lr']:.2e} | elapsed={elapsed:.1f}s",
                    flush=True,
                )

        ran_batches = min(num_batches, max_train_batches) if max_train_batches else num_batches
        avg_loss = epoch_loss / max(1, ran_batches)
        val = evaluate_detector(model, val_loader, device, max_batches=max_eval_batches)
        monitor = val.get("map50", val["recall"])
        best_metric_name = "map50" if "map50" in val else "recall"
        history.append(
            {
                "epoch": epoch + 1,
                "train_loss": avg_loss,
                "val_recall": val["recall"],
                "val_map50": val.get("map50"),
                "val_map": val.get("map"),
                "lr": optimizer.param_groups[0]["lr"],
            }
        )
        print(
            f"Epoch {epoch+1}/{epochs} - loss={avg_loss:.4f} - val_recall@0.5={val['recall']:.4f}"
            + (f" - val_map50={val['map50']:.4f}" if "map50" in val else ""),
            flush=True,
        )

        if monitor > best_metric + 1e-4:
            best_metric = monitor
            best_epoch = epoch + 1
            best_state = copy.deepcopy(model.state_dict())
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping at epoch {epoch+1} (best {best_metric_name}={best_metric:.4f} @ epoch {best_epoch})", flush=True)
                break

    model.load_state_dict(best_state)

    eval_split = "test" if test_loader is not None else "val"
    final = evaluate_detector(
        model, test_loader if test_loader is not None else val_loader, device, max_batches=max_eval_batches
    )
    print(
        f"Final ({eval_split}) {model_name} - recall@0.5={final['recall']:.4f}"
        + (f" - map50={final['map50']:.4f} - map={final['map']:.4f}" if "map50" in final else ""),
        flush=True,
    )

    if checkpoint_path:
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        torch.save(model.state_dict(), checkpoint_path)
        print(f"Saved best {model_name} checkpoint to {checkpoint_path}", flush=True)

    return {
        "model": model_name,
        "task": "detection",
        "recall": float(final["recall"]),
        "map50": float(final.get("map50", 0.0)),
        "map": float(final.get("map", 0.0)),
        "eval_split": eval_split,
        "best_val_metric": float(best_metric),
        "best_val_metric_name": best_metric_name,
        "best_epoch": best_epoch,
        "epochs_ran": len(history),
        "history": history,
        "model_path": os.path.normpath(checkpoint_path) if checkpoint_path else None,
        "num_parameters": int(sum(p.numel() for p in model.parameters())),
        "hyperparameters": {
            "epochs": epochs,
            "lr": lr,
            "batch_size": batch_size,
            "weight_decay": weight_decay,
            "momentum": momentum,
            "img_size": IMG_SIZE,
            "optimizer": "SGD",
            "lr_scheduler": "LinearLR warmup + CosineAnnealingLR",
            "freeze_epochs": freeze_epochs,
            "grad_clip": grad_clip,
            "patience": patience,
            "augmentation": "train-only: box-aware hflip + photometric jitter",
        },
    }
