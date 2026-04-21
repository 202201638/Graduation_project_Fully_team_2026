import os
from glob import glob
from typing import Callable, Tuple

import torch
import torch.nn as nn
import torchvision
from torchvision.models import DenseNet121_Weights, EfficientNet_B0_Weights, ResNet50_Weights
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights, RetinaNet_ResNet50_FPN_Weights
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.retinanet import RetinaNetClassificationHead

from src.config import DEFAULT_YOLO_WEIGHTS, RUNS_DIR


def _build_with_optional_weights(
    label: str,
    pretrained_builder: Callable[[], torch.nn.Module],
    fallback_builder: Callable[[], torch.nn.Module],
    prefer_pretrained: bool = True,
) -> Tuple[torch.nn.Module, bool]:
    if prefer_pretrained:
        try:
            return pretrained_builder(), True
        except Exception as exc:
            print(
                f"[{label}] pretrained weights unavailable ({exc}). Falling back to randomly initialized weights.",
                flush=True,
            )
    return fallback_builder(), False


def build_resnet50_classifier(
    dropout: float = 0.3, num_classes: int = 2, prefer_pretrained: bool = True
) -> Tuple[torch.nn.Module, bool]:
    def configure(model: torch.nn.Module) -> torch.nn.Module:
        model.fc = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(model.fc.in_features, num_classes),
        )
        return model

    return _build_with_optional_weights(
        label="ResNet50",
        pretrained_builder=lambda: configure(
            torchvision.models.resnet50(weights=ResNet50_Weights.DEFAULT)
        ),
        fallback_builder=lambda: configure(torchvision.models.resnet50(weights=None)),
        prefer_pretrained=prefer_pretrained,
    )


def build_densenet121_classifier(
    dropout: float = 0.3, num_classes: int = 2, prefer_pretrained: bool = True
) -> Tuple[torch.nn.Module, bool]:
    def configure(model: torch.nn.Module) -> torch.nn.Module:
        model.classifier = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(model.classifier.in_features, num_classes),
        )
        return model

    return _build_with_optional_weights(
        label="DenseNet121",
        pretrained_builder=lambda: configure(
            torchvision.models.densenet121(weights=DenseNet121_Weights.DEFAULT)
        ),
        fallback_builder=lambda: configure(torchvision.models.densenet121(weights=None)),
        prefer_pretrained=prefer_pretrained,
    )


def build_efficientnet_b0_classifier(
    dropout: float = 0.3, num_classes: int = 2, prefer_pretrained: bool = True
) -> Tuple[torch.nn.Module, bool]:
    def configure(model: torch.nn.Module) -> torch.nn.Module:
        model.classifier[0] = nn.Dropout(p=dropout)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        return model

    return _build_with_optional_weights(
        label="EfficientNet-B0",
        pretrained_builder=lambda: configure(
            torchvision.models.efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
        ),
        fallback_builder=lambda: configure(torchvision.models.efficientnet_b0(weights=None)),
        prefer_pretrained=prefer_pretrained,
    )


def build_fasterrcnn_detector(
    num_classes: int = 2, prefer_pretrained: bool = True
) -> Tuple[torch.nn.Module, bool]:
    def configure(model: torch.nn.Module) -> torch.nn.Module:
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        return model

    return _build_with_optional_weights(
        label="FasterRCNN",
        pretrained_builder=lambda: configure(
            torchvision.models.detection.fasterrcnn_resnet50_fpn(
                weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT
            )
        ),
        fallback_builder=lambda: configure(
            torchvision.models.detection.fasterrcnn_resnet50_fpn(
                weights=None,
                weights_backbone=None,
            )
        ),
        prefer_pretrained=prefer_pretrained,
    )


def build_retinanet_detector(
    num_classes: int = 2, prefer_pretrained: bool = True
) -> Tuple[torch.nn.Module, bool]:
    def configure(model: torch.nn.Module) -> torch.nn.Module:
        num_anchors = model.head.classification_head.num_anchors
        model.head.classification_head = RetinaNetClassificationHead(
            model.backbone.out_channels,
            num_anchors,
            num_classes,
        )
        return model

    return _build_with_optional_weights(
        label="RetinaNet",
        pretrained_builder=lambda: configure(
            torchvision.models.detection.retinanet_resnet50_fpn(
                weights=RetinaNet_ResNet50_FPN_Weights.DEFAULT
            )
        ),
        fallback_builder=lambda: configure(
            torchvision.models.detection.retinanet_resnet50_fpn(
                weights=None,
                weights_backbone=None,
            )
        ),
        prefer_pretrained=prefer_pretrained,
    )


def load_checkpoint_if_available(
    model: torch.nn.Module,
    checkpoint_path: str,
    map_location: str = "cpu",
) -> bool:
    if not checkpoint_path or not os.path.exists(checkpoint_path):
        return False

    state = torch.load(checkpoint_path, map_location=map_location)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]

    model.load_state_dict(state)
    print(f"Loaded checkpoint: {checkpoint_path}", flush=True)
    return True


def resolve_yolo_base_weights() -> str:
    candidates = [DEFAULT_YOLO_WEIGHTS]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return os.path.normpath(candidate)

    print(
        "[YOLO] Local base weights not found. Falling back to yolov8n.yaml so training can start without a download.",
        flush=True,
    )
    return "yolov8n.yaml"


def resolve_latest_yolo_checkpoint(preferred_path: str = "") -> str:
    candidates = []
    if preferred_path:
        candidates.append(preferred_path)

    discovered = glob(os.path.join(RUNS_DIR, "**", "weights", "best.pt"), recursive=True)
    discovered.sort(key=os.path.getmtime, reverse=True)
    candidates.extend(discovered)

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return os.path.normpath(candidate)

    raise FileNotFoundError(
        f"YOLO model weights not found at {preferred_path or '<auto>'} and no {RUNS_DIR}/**/weights/best.pt discovered."
    )
