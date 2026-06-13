from typing import Dict, Optional

import cv2
import numpy as np
import os
import json

import torch

from src.config import ARTIFACT_DIR, CHECKPOINT_DIR, CLS_IMG_SIZE, IMG_SIZE
from src.model_utils import resolve_latest_yolo_checkpoint

PHASE8_RESULTS_PATH = os.path.join(ARTIFACT_DIR, "phase8_demo_result.json")

def _resolve_model_path(explicit_path: str) -> str:
    return resolve_latest_yolo_checkpoint(explicit_path)


def run_phase8_demo(image_path: str, model_path: str = "runs/phase5_yolov8_optimized/weights/best.pt") -> Dict:
    """
    Demo:
    Input: Chest X-ray image path
    Output: Pneumonia detected, bounding box, confidence%
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Demo image not found: {image_path}")
    model_path = _resolve_model_path(model_path)

    from ultralytics import YOLO

    model = YOLO(model_path)
    results = model.predict(source=image_path, imgsz=640, conf=0.25, verbose=False)
    if not results:
        payload = {
            "detected": False,
            "confidence": 0.0,
            "output_image": None,
            "model_path": model_path,
            "input_image": image_path,
        }
        os.makedirs(os.path.dirname(PHASE8_RESULTS_PATH), exist_ok=True)
        with open(PHASE8_RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return payload

    result = results[0]
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Failed to read image {image_path}")

    detected = False
    best_conf = 0.0
    if result.boxes is not None and len(result.boxes) > 0:
        for b in result.boxes:
            conf = float(b.conf.item())
            if conf > best_conf:
                best_conf = conf
            x1, y1, x2, y2 = [int(v) for v in b.xyxy[0].tolist()]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                img,
                f"Pneumonia {conf*100:.1f}%",
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )
            detected = True

    out_path = os.path.join(ARTIFACT_DIR, "demo_output.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, img)
    payload = {
        "detected": detected,
        "confidence": float(np.round(best_conf * 100.0, 2)),
        "output_image": out_path,
        "model_path": model_path,
        "input_image": image_path,
    }
    with open(PHASE8_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload


def _sample_test_image() -> str:
    from src.config import YOLO_DATASET_DIR

    for split in ("test", "val"):
        img_dir = os.path.join(YOLO_DATASET_DIR, split, "images")
        if os.path.isdir(img_dir):
            files = sorted(f for f in os.listdir(img_dir) if f.endswith(".png"))
            if files:
                return os.path.join(img_dir, files[0])
    raise FileNotFoundError("No demo image found; build the YOLO dataset first.")


def run_demo_for_model(model_name: str, checkpoint_path: str = "", image_path: Optional[str] = None) -> Dict:
    """Single-image inference demo for one model (classifier prob or detector boxes)."""
    from src.phase6_explainability import (
        CLASSIFICATION_MODELS,
        _classifier_factory,
        _load_cls_tensor,
        _detection_overlay,
        _yolo_overlay,
    )
    from src.model_utils import load_checkpoint_if_available

    image_path = image_path or _sample_test_image()
    out_path = os.path.join(ARTIFACT_DIR, f"{model_name}_demo.png")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if model_name in CLASSIFICATION_MODELS:
        model, _ = _classifier_factory(model_name)
        ckpt = checkpoint_path or os.path.join(CHECKPOINT_DIR, f"{model_name}.pt")
        load_checkpoint_if_available(model, ckpt)
        model = model.to(device).eval()
        x, _ = _load_cls_tensor(image_path, device)
        with torch.no_grad():
            prob = float(torch.softmax(model(x), dim=1)[0, 1].item())
        img = cv2.imread(image_path)
        label = "PNEUMONIA" if prob >= 0.5 else "NORMAL"
        cv2.putText(img, f"{label} {prob*100:.1f}%", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255) if prob >= 0.5 else (0, 180, 0), 2)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        cv2.imwrite(out_path, img)
        payload = {
            "model": model_name,
            "task": "classification",
            "pneumonia_probability": round(prob, 4),
            "predicted": label.lower(),
            "output_image": out_path,
            "input_image": image_path,
        }
    elif model_name == "yolo":
        info = _yolo_overlay(checkpoint_path, image_path, out_path)
        payload = {"model": model_name, "task": "detection", "boxes": info["boxes_drawn"],
                   "output_image": out_path, "input_image": image_path}
    else:
        ckpt = checkpoint_path or os.path.join(CHECKPOINT_DIR, f"{model_name}.pt")
        info = _detection_overlay(model_name, ckpt, image_path, out_path)
        payload = {"model": model_name, "task": "detection", "boxes": info["boxes_drawn"],
                   "output_image": out_path, "input_image": image_path}

    result_path = os.path.join(ARTIFACT_DIR, f"{model_name}_demo_result.json")
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload
