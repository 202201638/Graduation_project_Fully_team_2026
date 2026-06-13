from typing import Dict
import os

from src.classification.train_utils import run_classifier_training
from src.config import CHECKPOINT_DIR
from src.model_utils import build_resnet50_classifier


def train_resnet(
    epochs: int = 8,
    lr: float = 1e-4,
    batch_size: int = 32,
    dropout: float = 0.3,
    weight_decay: float = 1e-4,
    patience: int = 4,
    freeze_epochs: int = 0,
    checkpoint_path: str = os.path.join(CHECKPOINT_DIR, "resnet50.pt"),
    **train_kwargs,
) -> Dict:
    model, _ = build_resnet50_classifier(dropout=dropout)
    return run_classifier_training(
        model,
        "resnet50",
        epochs=epochs,
        lr=lr,
        batch_size=batch_size,
        dropout=dropout,
        weight_decay=weight_decay,
        checkpoint_path=checkpoint_path,
        patience=patience,
        freeze_epochs=freeze_epochs,
        **train_kwargs,
    )
