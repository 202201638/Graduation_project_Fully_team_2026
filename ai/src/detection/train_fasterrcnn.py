import torch
import time
import os
from torch.optim import SGD
from torchvision.ops import box_iou

from src.config import CHECKPOINT_DIR
from src.detection.data import create_dataloaders
from src.model_utils import build_fasterrcnn_detector


def _evaluate(model, data_loader, device):
    model.eval()
    total_gt = 0
    total_tp = 0

    with torch.no_grad():
        for images, targets in data_loader:
            images = [img.to(device) for img in images]
            outputs = model(images)

            for output, target in zip(outputs, targets):
                gt_boxes = target["boxes"].to(device)
                if gt_boxes.numel() == 0:
                    continue

                total_gt += gt_boxes.shape[0]
                if output["boxes"].numel() == 0:
                    continue

                ious = box_iou(gt_boxes, output["boxes"].to(device))
                max_iou, _ = ious.max(dim=1)
                total_tp += (max_iou >= 0.5).sum().item()

    recall = total_tp / total_gt if total_gt > 0 else 0.0
    return recall


def train_fasterrcnn(
    epochs: int = 2,
    lr: float = 0.005,
    batch_size: int = 4,
    weight_decay: float = 0.0005,
    checkpoint_path: str = os.path.join(CHECKPOINT_DIR, "fasterrcnn.pt"),
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, _ = build_fasterrcnn_detector()
    model = model.to(device)

    train_loader, val_loader = create_dataloaders(batch_size=batch_size)

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = SGD(params, lr=lr, momentum=0.9, weight_decay=weight_decay)

    print(
        f"Starting Faster R-CNN training on {device} | epochs={epochs}, batch_size={batch_size}, lr={lr}",
        flush=True,
    )

    last_recall = 0.0
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        epoch_start = time.time()
        num_batches = len(train_loader)

        for batch_idx, (images, targets) in enumerate(train_loader, start=1):
            images = [img.to(device) for img in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

            loss_dict = model(images, targets)
            losses = sum(loss for loss in loss_dict.values())

            optimizer.zero_grad()
            losses.backward()
            optimizer.step()

            epoch_loss += losses.item()

            if batch_idx % 20 == 0 or batch_idx == num_batches:
                elapsed = time.time() - epoch_start
                print(
                    f"[FasterRCNN] Epoch {epoch+1}/{epochs} | batch {batch_idx}/{num_batches} | "
                    f"batch_loss={losses.item():.4f} | elapsed={elapsed:.1f}s",
                    flush=True,
                )

        avg_loss = epoch_loss / max(1, len(train_loader))
        recall = _evaluate(model, val_loader, device)
        last_recall = recall
        print(
            f"Epoch {epoch+1}/{epochs} - loss: {avg_loss:.4f} - val_recall@0.5: {recall:.4f}",
            flush=True,
        )

    print("Faster R-CNN training finished", flush=True)
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)
    print(f"Saved Faster R-CNN checkpoint to {checkpoint_path}", flush=True)
    return {"recall": float(last_recall), "model_path": os.path.normpath(checkpoint_path)}
