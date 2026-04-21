import json
import os
from typing import Dict

from src.classification.train_densenet import train_densenet
from src.classification.train_efficientnet import train_efficientnet
from src.classification.train_resnet import train_resnet
from src.config import ARTIFACT_DIR, CHECKPOINT_DIR
from src.detection.train_fasterrcnn import train_fasterrcnn
from src.detection.train_retinanet import train_retinanet
from src.detection.train_yolo import train_yolo


BASELINE_RESULTS_PATH = os.path.join(ARTIFACT_DIR, "phase3_baseline_results.json")


def _save_json(path: str, data: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_phase3_baseline(det_epochs: int = 2, cls_epochs: int = 3):
    print("Phase 3 baseline training (all models)")
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    results: Dict[str, Dict] = {}
    runs = [
        ("yolo", lambda: train_yolo(epochs=det_epochs, run_name="phase3_yolo_baseline")),
        (
            "fasterrcnn",
            lambda: train_fasterrcnn(
                epochs=det_epochs,
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "fasterrcnn_phase3.pt"),
            ),
        ),
        (
            "retinanet",
            lambda: train_retinanet(
                epochs=det_epochs,
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "retinanet_phase3.pt"),
            ),
        ),
        (
            "resnet50",
            lambda: train_resnet(
                epochs=cls_epochs,
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "resnet50_phase3.pt"),
            ),
        ),
        (
            "densenet121",
            lambda: train_densenet(
                epochs=cls_epochs,
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "densenet121_phase3.pt"),
            ),
        ),
        (
            "efficientnet_b0",
            lambda: train_efficientnet(
                epochs=cls_epochs,
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "efficientnet_b0_phase3.pt"),
            ),
        ),
    ]

    for model_name, runner in runs:
        try:
            metrics = runner()
            results[model_name] = metrics
        except Exception as exc:
            print(f"[Phase3] {model_name} failed: {exc}")
            results[model_name] = {"status": "failed", "error": str(exc)}
        _save_json(BASELINE_RESULTS_PATH, results)

    _save_json(BASELINE_RESULTS_PATH, results)
    print(f"Saved baseline metrics to {BASELINE_RESULTS_PATH}")
    return results
