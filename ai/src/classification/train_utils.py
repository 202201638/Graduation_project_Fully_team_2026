from typing import Optional, Tuple
import time
import os

import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data import DataLoader

from src.evaluation import evaluate_classification


def train_classifier(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
    epochs: int = 3,
    lr: float = 1e-4,
    weight_decay: float = 1e-4,
    checkpoint_path: Optional[str] = None,
) -> Tuple[float, float, float]:
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    best_acc = 0.0
    best_f1 = 0.0
    best_auc = 0.0

    print(
        f"Starting classifier training on {device} | epochs={epochs}, lr={lr}, weight_decay={weight_decay}",
        flush=True,
    )

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        epoch_start = time.time()
        num_batches = len(train_loader)

        for batch_idx, (images, labels) in enumerate(train_loader, start=1):
            images = images.to(device)
            labels = labels.to(device)

            logits = model(images)
            loss = criterion(logits, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

            if batch_idx % 20 == 0 or batch_idx == num_batches:
                elapsed = time.time() - epoch_start
                print(
                    f"[Classifier] Epoch {epoch+1}/{epochs} | batch {batch_idx}/{num_batches} | "
                    f"batch_loss={loss.item():.4f} | elapsed={elapsed:.1f}s",
                    flush=True,
                )

        avg_loss = running_loss / max(1, len(train_loader))

        model.eval()
        all_targets = []
        all_preds = []
        all_probs = []

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)

                logits = model(images)
                probs = torch.softmax(logits, dim=1)[:, 1]
                preds = (probs >= 0.5).long()

                all_targets.extend(labels.cpu().tolist())
                all_preds.extend(preds.cpu().tolist())
                all_probs.extend(probs.cpu().tolist())

        print(f"Epoch {epoch+1}/{epochs} - train_loss: {avg_loss:.4f} - val metrics:", flush=True)
        try:
            evaluate_classification(all_targets, all_preds, all_probs)
        except Exception as e:
            print(f"Failed to compute classification metrics: {e}")

    # final metrics on full validation set
    # recompute once more for return
    model.eval()
    all_targets = []
    all_preds = []
    all_probs = []
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            probs = torch.softmax(logits, dim=1)[:, 1]
            preds = (probs >= 0.5).long()

            all_targets.extend(labels.cpu().tolist())
            all_preds.extend(preds.cpu().tolist())
            all_probs.extend(probs.cpu().tolist())

    try:
        # evaluate_classification already prints, but we want numbers here
        from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

        best_acc = accuracy_score(all_targets, all_preds)
        best_f1 = f1_score(all_targets, all_preds)
        best_auc = roc_auc_score(all_targets, all_probs)
    except Exception:
        pass

    if checkpoint_path:
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        torch.save(model.state_dict(), checkpoint_path)
        print(f"Saved classifier checkpoint to {checkpoint_path}", flush=True)

    return best_acc, best_f1, best_auc

