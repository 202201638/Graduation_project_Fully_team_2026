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


BEST_PARAMS_PATH = os.path.join(ARTIFACT_DIR, "phase4_best_hyperparameters.json")
RETRAIN_RESULTS_PATH = os.path.join(ARTIFACT_DIR, "phase5_retrain_results.json")


def _load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_phase5_retrain(full_epochs_detection: int = 20, full_epochs_classification: int = 8):
    print("Phase 5: Retraining with optimized hyperparameters")
    if not os.path.exists(BEST_PARAMS_PATH):
        raise FileNotFoundError(
            f"Missing optimized parameters file: {BEST_PARAMS_PATH}. "
            "Run Phase 4 optimization first."
        )
    best = _load_json(BEST_PARAMS_PATH)
    out: Dict[str, Dict] = {}
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    # Retrain only models available in optimized params.
    if "yolo" in best:
        yolo_p = best["yolo"]["best_hyperparameters"]
        try:
            out["yolo"] = train_yolo(
                epochs=full_epochs_detection,
                lr=float(yolo_p["lr"]),
                batch_size=int(yolo_p["batch_size"]),
                weight_decay=float(yolo_p["weight_decay"]),
                anchor_size=int(yolo_p["anchor_size"]),
                run_name="phase5_yolov8_optimized",
            )
        except Exception as exc:
            out["yolo"] = {"status": "failed", "error": str(exc)}
        _save_json(RETRAIN_RESULTS_PATH, out)

    if "fasterrcnn" in best:
        frcnn_p = best["fasterrcnn"]["best_hyperparameters"]
        try:
            out["fasterrcnn"] = train_fasterrcnn(
                epochs=full_epochs_detection,
                lr=float(frcnn_p["lr"]),
                batch_size=int(frcnn_p["batch_size"]),
                weight_decay=float(frcnn_p["weight_decay"]),
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "fasterrcnn_phase5.pt"),
            )
        except Exception as exc:
            out["fasterrcnn"] = {"status": "failed", "error": str(exc)}
        _save_json(RETRAIN_RESULTS_PATH, out)

    if "retinanet" in best:
        retina_p = best["retinanet"]["best_hyperparameters"]
        try:
            out["retinanet"] = train_retinanet(
                epochs=full_epochs_detection,
                lr=float(retina_p["lr"]),
                batch_size=int(retina_p["batch_size"]),
                weight_decay=float(retina_p["weight_decay"]),
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "retinanet_phase5.pt"),
            )
        except Exception as exc:
            out["retinanet"] = {"status": "failed", "error": str(exc)}
        _save_json(RETRAIN_RESULTS_PATH, out)

    if "resnet50" in best:
        res_p = best["resnet50"]["best_hyperparameters"]
        try:
            out["resnet50"] = train_resnet(
                epochs=full_epochs_classification,
                lr=float(res_p["lr"]),
                batch_size=int(res_p["batch_size"]),
                dropout=float(res_p["dropout"]),
                weight_decay=float(res_p["weight_decay"]),
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "resnet50_phase5.pt"),
            )
        except Exception as exc:
            out["resnet50"] = {"status": "failed", "error": str(exc)}
        _save_json(RETRAIN_RESULTS_PATH, out)

    if "densenet121" in best:
        den_p = best["densenet121"]["best_hyperparameters"]
        try:
            out["densenet121"] = train_densenet(
                epochs=full_epochs_classification,
                lr=float(den_p["lr"]),
                batch_size=int(den_p["batch_size"]),
                dropout=float(den_p["dropout"]),
                weight_decay=float(den_p["weight_decay"]),
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "densenet121_phase5.pt"),
            )
        except Exception as exc:
            out["densenet121"] = {"status": "failed", "error": str(exc)}
        _save_json(RETRAIN_RESULTS_PATH, out)

    if "efficientnet_b0" in best:
        eff_p = best["efficientnet_b0"]["best_hyperparameters"]
        try:
            out["efficientnet_b0"] = train_efficientnet(
                epochs=full_epochs_classification,
                lr=float(eff_p["lr"]),
                batch_size=int(eff_p["batch_size"]),
                dropout=float(eff_p["dropout"]),
                weight_decay=float(eff_p["weight_decay"]),
                checkpoint_path=os.path.join(CHECKPOINT_DIR, "efficientnet_b0_phase5.pt"),
            )
        except Exception as exc:
            out["efficientnet_b0"] = {"status": "failed", "error": str(exc)}
        _save_json(RETRAIN_RESULTS_PATH, out)

    _save_json(RETRAIN_RESULTS_PATH, out)
    print(f"Phase 5 results saved to {RETRAIN_RESULTS_PATH}")
    return out
