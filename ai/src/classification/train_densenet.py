import torch
from typing import Dict
import os

from src.classification.data import create_classification_dataloaders
from src.classification.train_utils import train_classifier
from src.config import CHECKPOINT_DIR
from src.model_utils import build_densenet121_classifier


def train_densenet(
    epochs: int = 3,
    lr: float = 1e-4,
    batch_size: int = 4,
    dropout: float = 0.3,
    weight_decay: float = 1e-4,
    checkpoint_path: str = os.path.join(CHECKPOINT_DIR, "densenet121.pt"),
) -> Dict[str, float]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model, _ = build_densenet121_classifier(dropout=dropout)

    train_loader, val_loader = create_classification_dataloaders(
        batch_size=batch_size
    )

    acc, f1, auc = train_classifier(
        model,
        train_loader,
        val_loader,
        device,
        epochs=epochs,
        lr=lr,
        weight_decay=weight_decay,
        checkpoint_path=checkpoint_path,
    )

    print(
        f"DenseNet121 validation - Accuracy: {acc:.4f}, F1: {f1:.4f}, AUC: {auc:.4f}"
    )
    return {"accuracy": acc, "f1": f1, "auc": auc, "model_path": os.path.normpath(checkpoint_path)}
