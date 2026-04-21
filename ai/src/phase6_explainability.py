import os
import json

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F

from src.config import ARTIFACT_DIR, CHECKPOINT_DIR, IMG_SIZE, YOLO_DATASET_DIR
from src.model_utils import (
    build_densenet121_classifier,
    build_efficientnet_b0_classifier,
    build_resnet50_classifier,
    load_checkpoint_if_available,
)


def _load_image_tensor(image_path: str, device: torch.device) -> torch.Tensor:
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Failed to read image: {image_path}")
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
    return tensor.unsqueeze(0).to(device)


def _first_val_image() -> str:
    img_dir = os.path.join(YOLO_DATASET_DIR, "val", "images")
    if not os.path.isdir(img_dir):
        raise FileNotFoundError(
            f"Missing validation image folder: {img_dir}. Build the YOLO dataset first."
        )
    files = sorted([f for f in os.listdir(img_dir) if f.endswith(".png")])
    if not files:
        raise RuntimeError("No images found for Grad-CAM in val/images.")
    return os.path.join(img_dir, files[0])


def _save_overlay(
    image_rgb: np.ndarray,
    heatmap: np.ndarray,
    out_path: str,
):
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


def _grad_cam_for_model(
    model: torch.nn.Module,
    target_layer: torch.nn.Module,
    image_path: str,
    out_path: str,
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    x = _load_image_tensor(image_path, device)
    image_rgb = (x.squeeze(0).permute(1, 2, 0).detach().cpu().numpy() * 255).astype(np.uint8)

    activations = []
    gradients = []

    def _forward_hook(_, __, output):
        activations.append(output)

    def _backward_hook(_, grad_input, grad_output):
        del grad_input
        gradients.append(grad_output[0])

    fh = target_layer.register_forward_hook(_forward_hook)
    bh = target_layer.register_full_backward_hook(_backward_hook)
    try:
        logits = model(x)
        pred_class = torch.argmax(logits, dim=1).item()
        score = logits[:, pred_class].sum()
        model.zero_grad()
        score.backward()

        acts = activations[-1]
        grads = gradients[-1]
        weights = grads.mean(dim=(2, 3), keepdim=True)
        cam = (weights * acts).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = F.interpolate(cam, size=(IMG_SIZE, IMG_SIZE), mode="bilinear", align_corners=False)
        cam = cam.squeeze().detach().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        _save_overlay(image_rgb, cam, out_path)
    finally:
        fh.remove()
        bh.remove()


def _checkpoint_candidates(model_name: str):
    return [
        os.path.join(CHECKPOINT_DIR, f"{model_name}_phase5.pt"),
        os.path.join(CHECKPOINT_DIR, f"{model_name}_phase3.pt"),
        os.path.join(CHECKPOINT_DIR, f"{model_name}.pt"),
    ]


def _load_best_checkpoint(model_name: str, model: torch.nn.Module) -> str:
    for checkpoint_path in _checkpoint_candidates(model_name):
        try:
            if load_checkpoint_if_available(model, checkpoint_path):
                return checkpoint_path
        except Exception as exc:
            print(f"Failed to load checkpoint {checkpoint_path}: {exc}")

    print(f"No trained checkpoint found for {model_name}. Using current model weights.")
    return ""


def run_phase6_gradcam():
    print("Phase 6: Grad-CAM explainability")
    image_path = _first_val_image()
    out_dir = os.path.join(ARTIFACT_DIR, "gradcam")
    os.makedirs(out_dir, exist_ok=True)

    models = []

    resnet, _ = build_resnet50_classifier(dropout=0.0)
    _load_best_checkpoint("resnet50", resnet)
    models.append(("resnet50", resnet, resnet.layer4[-1]))

    efficientnet, _ = build_efficientnet_b0_classifier(dropout=0.0)
    _load_best_checkpoint("efficientnet_b0", efficientnet)
    models.append(("efficientnet_b0", efficientnet, efficientnet.features[-1]))

    if any(os.path.exists(path) for path in _checkpoint_candidates("densenet121")):
        densenet, _ = build_densenet121_classifier(dropout=0.0)
        _load_best_checkpoint("densenet121", densenet)
        models.append(("densenet121", densenet, densenet.features[-2]))

    outputs = {}
    for model_name, model, target_layer in models:
        out_path = os.path.join(out_dir, f"{model_name}_gradcam.png")
        _grad_cam_for_model(
            model=model,
            target_layer=target_layer,
            image_path=image_path,
            out_path=out_path,
        )
        outputs[model_name] = out_path

    summary_path = os.path.join(ARTIFACT_DIR, "phase6_gradcam_results.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2)

    print(f"Grad-CAM images saved in {out_dir}")
    print(f"Phase 6 summary saved to {summary_path}")
    return outputs
