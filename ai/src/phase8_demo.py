from typing import Dict

import cv2
import numpy as np
import os
import json

from src.config import ARTIFACT_DIR
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
