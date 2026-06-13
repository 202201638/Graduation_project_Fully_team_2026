import os
from typing import Dict

from src.config import CHECKPOINT_DIR
from src.detection.train_utils import train_torchvision_detector
from src.model_utils import build_retinanet_detector


def train_retinanet(
    epochs: int = 10,
    lr: float = 5e-3,
    batch_size: int = 4,
    weight_decay: float = 5e-4,
    patience: int = 3,
    freeze_epochs: int = 1,
    checkpoint_path: str = os.path.join(CHECKPOINT_DIR, "retinanet.pt"),
    **train_kwargs,
) -> Dict:
    model, _ = build_retinanet_detector()
    # RetinaNet needs target sanitization + gradient clipping for stable focal-loss training
    return train_torchvision_detector(
        model,
        "retinanet",
        epochs=epochs,
        lr=lr,
        batch_size=batch_size,
        weight_decay=weight_decay,
        checkpoint_path=checkpoint_path,
        patience=patience,
        freeze_epochs=freeze_epochs,
        grad_clip=5.0,
        sanitize=True,
        **train_kwargs,
    )
