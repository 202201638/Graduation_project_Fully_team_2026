import os
import json

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as T

from src.config import (
    ARTIFACT_DIR,
    CHECKPOINT_DIR,
    CLS_IMG_SIZE,
    IMG_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    YOLO_DATASET_DIR,
)
from src.model_utils import (
    build_densenet121_classifier,
    build_efficientnet_b0_classifier,
    build_fasterrcnn_detector,
    build_resnet50_classifier,
    build_retinanet_detector,
    load_checkpoint_if_available,
    resolve_latest_yolo_checkpoint,
)

CLASSIFICATION_MODELS = {"resnet50", "densenet121", "efficientnet_b0"}
_NORMALIZE = T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)


def _first_positive_test_image() -> str:
    """Prefer a pneumonia-positive test image so explanations are meaningful."""
    for split in ("test", "val"):
        img_dir = os.path.join(YOLO_DATASET_DIR, split, "images")
        label_dir = os.path.join(YOLO_DATASET_DIR, split, "labels")
        if not os.path.isdir(img_dir):
            continue
        files = sorted(f for f in os.listdir(img_dir) if f.endswith(".png"))
        for f in files:
            label_path = os.path.join(label_dir, f.replace(".png", ".txt"))
            if os.path.exists(label_path) and os.path.getsize(label_path) > 0:
                return os.path.join(img_dir, f)
        if files:
            return os.path.join(img_dir, files[0])
    raise FileNotFoundError("No test/val images found. Build the YOLO dataset first.")


def _load_cls_tensor(image_path: str, device: torch.device):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Failed to read image: {image_path}")
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    img = cv2.resize(img, (CLS_IMG_SIZE, CLS_IMG_SIZE))
    rgb = img.copy()
    tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
    tensor = _NORMALIZE(tensor).unsqueeze(0).to(device)
    return tensor, rgb


def _save_overlay(image_rgb: np.ndarray, heatmap: np.ndarray, out_path: str):
    heatmap_uint8 = np.uint8(np.clip(heatmap, 0, 1) * 255)
    color_map = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    color_map = cv2.cvtColor(color_map, cv2.COLOR_BGR2RGB)
    overlay = np.uint8(0.4 * color_map + 0.6 * image_rgb)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.figure(figsize=(6, 6))
    plt.imshow(overlay)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def _grad_cam(model, target_layer, image_path, out_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    x, image_rgb = _load_cls_tensor(image_path, device)

    activations, gradients = [], []

    def _fwd(_, __, output):
        activations.append(output)

    def _bwd(_, grad_input, grad_output):
        del grad_input
        gradients.append(grad_output[0])

    fh = target_layer.register_forward_hook(_fwd)
    bh = target_layer.register_full_backward_hook(_bwd)
    try:
        logits = model(x)
        pred_class = int(torch.argmax(logits, dim=1).item())
        prob = float(torch.softmax(logits, dim=1)[0, 1].item())
        score = logits[:, pred_class].sum()
        model.zero_grad()
        score.backward()

        acts = activations[-1]
        grads = gradients[-1]
        weights = grads.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * acts).sum(dim=1, keepdim=True))
        cam = F.interpolate(cam, size=(CLS_IMG_SIZE, CLS_IMG_SIZE), mode="bilinear", align_corners=False)
        cam = cam.squeeze().detach().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        _save_overlay(image_rgb, cam, out_path)
    finally:
        fh.remove()
        bh.remove()
    return {"type": "grad_cam", "image": out_path, "predicted_class": pred_class, "pneumonia_probability": prob}


def _classifier_factory(model_name: str):
    if model_name == "resnet50":
        model, _ = build_resnet50_classifier(dropout=0.0)
        return model, model.layer4[-1]
    if model_name == "densenet121":
        model, _ = build_densenet121_classifier(dropout=0.0)
        return model, model.features[-2]
    if model_name == "efficientnet_b0":
        model, _ = build_efficientnet_b0_classifier(dropout=0.0)
        return model, model.features[-1]
    raise ValueError(f"Unknown classifier {model_name}")


def _detection_overlay(model_name: str, checkpoint_path: str, image_path: str, out_path: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    builder = build_fasterrcnn_detector if model_name == "fasterrcnn" else build_retinanet_detector
    model, _ = builder()
    load_checkpoint_if_available(model, checkpoint_path)
    model = model.to(device).eval()

    img = cv2.imread(image_path)
    rgb = cv2.cvtColor(cv2.resize(img, (IMG_SIZE, IMG_SIZE)), cv2.COLOR_BGR2RGB)
    tensor = torch.from_numpy(rgb).permute(2, 0, 1).float().to(device) / 255.0

    with torch.no_grad():
        output = model([tensor])[0]

    canvas = rgb.copy()
    drawn = 0
    for box, score in zip(output["boxes"].cpu(), output["scores"].cpu()):
        if float(score) < 0.3:
            continue
        x1, y1, x2, y2 = [int(v) for v in box.tolist()]
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(canvas, f"{float(score)*100:.0f}%", (x1, max(15, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        drawn += 1

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
    return {"type": "detection_overlay", "image": out_path, "boxes_drawn": drawn}


def _yolo_overlay(checkpoint_path: str, image_path: str, out_path: str):
    from ultralytics import YOLO

    model = YOLO(resolve_latest_yolo_checkpoint(checkpoint_path))
    results = model.predict(source=image_path, imgsz=IMG_SIZE, conf=0.25, verbose=False)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plotted = results[0].plot()  # BGR np array with boxes
    cv2.imwrite(out_path, plotted)
    n = len(results[0].boxes) if results[0].boxes is not None else 0
    return {"type": "detection_overlay", "image": out_path, "boxes_drawn": int(n)}


def run_explainability_for_model(model_name: str, checkpoint_path: str = "") -> dict:
    """Grad-CAM for classifiers, predicted-box overlay for detectors (single model)."""
    print(f"Phase 6: explainability for {model_name}", flush=True)
    image_path = _first_positive_test_image()
    out_dir = os.path.join(ARTIFACT_DIR, "explainability")
    out_path = os.path.join(out_dir, f"{model_name}_explain.png")

    if model_name in CLASSIFICATION_MODELS:
        model, target_layer = _classifier_factory(model_name)
        ckpt = checkpoint_path or os.path.join(CHECKPOINT_DIR, f"{model_name}.pt")
        load_checkpoint_if_available(model, ckpt)
        result = _grad_cam(model, target_layer, image_path, out_path)
    elif model_name == "yolo":
        result = _yolo_overlay(checkpoint_path, image_path, out_path)
    else:
        ckpt = checkpoint_path or os.path.join(CHECKPOINT_DIR, f"{model_name}.pt")
        result = _detection_overlay(model_name, ckpt, image_path, out_path)

    result["source_image"] = image_path
    return result


def run_phase6_gradcam():
    """All-classifier Grad-CAM (used by the local all-models pipeline in main.py)."""
    outputs = {}
    for model_name in ("resnet50", "efficientnet_b0", "densenet121"):
        ckpt = os.path.join(CHECKPOINT_DIR, f"{model_name}.pt")
        if not os.path.exists(ckpt):
            continue
        try:
            outputs[model_name] = run_explainability_for_model(model_name, ckpt)
        except Exception as exc:
            print(f"Grad-CAM failed for {model_name}: {exc}", flush=True)
    summary_path = os.path.join(ARTIFACT_DIR, "phase6_gradcam_results.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2)
    print(f"Phase 6 summary saved to {summary_path}")
    return outputs
