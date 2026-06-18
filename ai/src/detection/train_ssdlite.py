import os
from typing import Dict

from src.config import CHECKPOINT_DIR
from src.detection.train_utils import train_torchvision_detector
from src.model_utils import build_ssdlite_detector


def train_ssdlite(
    epochs: int = 30,
    lr: float = 3e-3,
    batch_size: int = 8,
    weight_decay: float = 5e-4,
    patience: int = 5,
    freeze_epochs: int = 1,
    fraction: float = 1.0,
    checkpoint_path: str = os.path.join(CHECKPOINT_DIR, "ssdlite.pt"),
    **train_kwargs,
) -> Dict:
    """Train SSDlite320 MobileNetV3-Large, the lightweight fast-to-train detector.

    Shares the TorchVision detection loop with Faster R-CNN (warmup + cosine LR, AMP,
    frozen-backbone warmup, mAP/recall, early stopping, best-checkpoint restore). The
    model resizes inputs to 320px internally, and ``fraction`` (<1.0) trains on part of
    the data to finish even faster.
    """
    model, _ = build_ssdlite_detector()
    return train_torchvision_detector(
        model,
        "ssdlite",
        epochs=epochs,
        lr=lr,
        batch_size=batch_size,
        weight_decay=weight_decay,
        checkpoint_path=checkpoint_path,
        patience=patience,
        freeze_epochs=freeze_epochs,
        fraction=fraction,
        **train_kwargs,
    )
