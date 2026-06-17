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
    builder = build_fasterrcnn_detector
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


def _attribution_cam(attribution: torch.Tensor) -> np.ndarray:
    """Collapse a (C, H, W) pixel attribution into a normalized 0-1 saliency map."""
    cam = attribution.abs().sum(dim=0)
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    return cam.detach().cpu().numpy()


def _integrated_gradients(model, image_path, out_path, steps: int = 24, chunk: int = 8):
    """Integrated Gradients saliency for the pneumonia class (index 1)."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    x, image_rgb = _load_cls_tensor(image_path, device)
    baseline = torch.zeros_like(x)
    delta = x - baseline
    alphas = torch.linspace(1.0 / steps, 1.0, steps, device=device).view(steps, 1, 1, 1)

    grad_accum = torch.zeros_like(x)
    for start in range(0, steps, chunk):
        sub_path = (baseline + alphas[start : start + chunk] * delta).detach().requires_grad_(True)
        score = model(sub_path)[:, 1].sum()
        grads = torch.autograd.grad(score, sub_path)[0]
        grad_accum = grad_accum + grads.sum(dim=0, keepdim=True)

    ig = (delta * (grad_accum / steps))[0]
    _save_overlay(image_rgb, _attribution_cam(ig), out_path)
    return {"type": "integrated_gradients", "image": out_path}


def _gradient_shap(model, image_path, out_path, n_samples: int = 8, stdev: float = 0.15):
    """GradientSHAP saliency for the pneumonia class (index 1)."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    x, image_rgb = _load_cls_tensor(image_path, device)
    baseline = torch.zeros_like(x)
    shap_accum = torch.zeros_like(x)
    for _ in range(n_samples):
        alpha = float(torch.rand(1).item())
        noised = x + torch.randn_like(x) * stdev
        interpolated = (baseline + alpha * (noised - baseline)).detach().requires_grad_(True)
        score = model(interpolated)[:, 1].sum()
        grads = torch.autograd.grad(score, interpolated)[0]
        shap_accum = shap_accum + (noised - baseline) * grads

    shap_values = (shap_accum / n_samples)[0]
    _save_overlay(image_rgb, _attribution_cam(shap_values), out_path)
    return {"type": "gradient_shap", "image": out_path}


def _eigen_cam_from_activation(activation: np.ndarray) -> np.ndarray:
    """First principal component of a (C, H, W) activation, normalized to 0-1."""
    channels, height, width = activation.shape
    reshaped = np.nan_to_num(activation.reshape(channels, -1).T)
    reshaped = reshaped - reshaped.mean(axis=0, keepdims=True)
    try:
        _u, _s, vt = np.linalg.svd(reshaped, full_matrices=False)
        projection = reshaped @ vt[0]
    except np.linalg.LinAlgError:
        projection = reshaped.mean(axis=1)
    cam = projection.reshape(height, width)
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    return cam.astype(np.float32)


def _eigen_cam_detector(model_name: str, checkpoint_path: str, image_path: str, out_path: str):
    """Eigen-CAM saliency for a detector backbone (activation-based, no gradients)."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    captured = {}

    def _hook(_module, _inputs, output):
        captured["value"] = output

    img = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(cv2.resize(img, (IMG_SIZE, IMG_SIZE)), cv2.COLOR_BGR2RGB)

    if model_name in ("yolo",):
        from ultralytics import YOLO

        model = YOLO(resolve_latest_yolo_checkpoint(checkpoint_path))
        handle = model.model.model[-2].register_forward_hook(_hook)
        try:
            model.predict(source=image_path, imgsz=IMG_SIZE, conf=0.25, verbose=False)
        finally:
            handle.remove()
    else:
        model, _ = build_fasterrcnn_detector()
        load_checkpoint_if_available(model, checkpoint_path)
        model = model.to(device).eval()
        tensor = torch.from_numpy(image_rgb).permute(2, 0, 1).float().to(device) / 255.0
        handle = model.backbone.body.layer4[-1].register_forward_hook(_hook)
        try:
            with torch.no_grad():
                model([tensor])
        finally:
            handle.remove()

    activation = captured.get("value")
    if isinstance(activation, (list, tuple)):
        activation = activation[0]
    if activation is None:
        raise RuntimeError(f"No activation captured for Eigen-CAM ({model_name}).")
    activation = activation.detach().float().cpu().numpy()[0]
    cam = _eigen_cam_from_activation(activation)
    _save_overlay(image_rgb, cam, out_path)
    return {"type": "eigen_cam", "image": out_path}


def _score_cam(model, target_layer, image_path, out_path, top_k: int = 96, batch: int = 16):
    """Score-CAM saliency for the pneumonia class (gradient-free, class-discriminative)."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    x, image_rgb = _load_cls_tensor(image_path, device)

    captured = {}

    def _hook(_module, _inputs, output):
        captured["value"] = output

    handle = target_layer.register_forward_hook(_hook)
    try:
        with torch.no_grad():
            model(x)
    finally:
        handle.remove()

    activations = captured["value"][0].float()  # (C, H, W)
    k = min(top_k, activations.shape[0])
    top_idx = torch.topk(activations.mean(dim=(1, 2)), k).indices
    size = tuple(x.shape[-2:])
    maps = F.interpolate(
        activations[top_idx].unsqueeze(1), size=size, mode="bilinear", align_corners=False
    )
    flat = maps.view(k, -1)
    mins = flat.min(dim=1, keepdim=True).values
    maxs = flat.max(dim=1, keepdim=True).values
    maps = ((flat - mins) / (maxs - mins + 1e-8)).view(k, 1, *size)

    scores = torch.zeros(k, device=device)
    with torch.no_grad():
        for start in range(0, k, batch):
            scores[start : start + batch] = torch.softmax(
                model(x * maps[start : start + batch]), dim=1
            )[:, 1]

    weights = torch.relu(scores).view(k, 1, 1)
    cam = torch.relu((weights * maps.squeeze(1)).sum(dim=0))
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    _save_overlay(image_rgb, cam.detach().cpu().numpy(), out_path)
    return {"type": "score_cam", "image": out_path}


def _occlusion_detector(model_name, checkpoint_path, image_path, out_path, grid: int = 12):
    """Occlusion-sensitivity saliency for a detector (gradient-free, uniform across families)."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    size = IMG_SIZE
    base = cv2.imread(image_path)
    img = cv2.cvtColor(cv2.resize(base, (size, size)), cv2.COLOR_BGR2RGB)
    mean_color = tuple(int(c) for c in img.reshape(-1, 3).mean(axis=0))

    if model_name in ("yolo",):
        from ultralytics import YOLO

        model = YOLO(resolve_latest_yolo_checkpoint(checkpoint_path))

        def _top_conf(images):
            results = model.predict(
                source=[cv2.cvtColor(im, cv2.COLOR_RGB2BGR) for im in images],
                imgsz=size,
                conf=0.001,
                verbose=False,
            )
            return [
                float(r.boxes.conf.max().item()) if (r.boxes is not None and len(r.boxes) > 0) else 0.0
                for r in results
            ]

        batch = 16
    else:
        model, _ = build_fasterrcnn_detector()
        load_checkpoint_if_available(model, checkpoint_path)
        model = model.to(device).eval()

        def _top_conf(images):
            tensors = [
                torch.from_numpy(im).permute(2, 0, 1).float().to(device) / 255.0 for im in images
            ]
            with torch.no_grad():
                outputs = model(tensors)
            return [
                float(o["scores"].max().item()) if o["scores"].numel() else 0.0 for o in outputs
            ]

        batch = 4

    baseline = _top_conf([img])[0]
    cell = size // grid
    occluded, cells = [], []
    for gy in range(grid):
        for gx in range(grid):
            patch = img.copy()
            patch[gy * cell : (gy + 1) * cell, gx * cell : (gx + 1) * cell] = mean_color
            occluded.append(patch)
            cells.append((gy, gx))

    importance = np.zeros((grid, grid), dtype=np.float32)
    for start in range(0, len(occluded), batch):
        for (gy, gx), conf in zip(cells[start : start + batch], _top_conf(occluded[start : start + batch])):
            importance[gy, gx] = max(0.0, baseline - conf)

    cam = importance - importance.min()
    cam = cam / (cam.max() + 1e-8)
    cam = cv2.resize(cam, (size, size))
    _save_overlay(img, cam, out_path)
    return {"type": "occlusion", "image": out_path}


def run_explainability_for_model(model_name: str, checkpoint_path: str = "") -> dict:
    """Grad-CAM for classifiers, predicted-box overlay for detectors (single model)."""
    print(f"Phase 6: explainability for {model_name}", flush=True)
    image_path = _first_positive_test_image()
    out_dir = os.path.join(ARTIFACT_DIR, "explainability")
    out_path = os.path.join(out_dir, f"{model_name}_explain.png")

    extra_maps = []
    if model_name in CLASSIFICATION_MODELS:
        model, target_layer = _classifier_factory(model_name)
        ckpt = checkpoint_path or os.path.join(CHECKPOINT_DIR, f"{model_name}.pt")
        load_checkpoint_if_available(model, ckpt)
        result = _grad_cam(model, target_layer, image_path, out_path)
        # Two extra gradient-based attributions on the same loaded classifier.
        for suffix, fn in (
            ("integrated_gradients", _integrated_gradients),
            ("gradient_shap", _gradient_shap),
        ):
            extra_path = os.path.join(out_dir, f"{model_name}_{suffix}.png")
            try:
                extra_maps.append(fn(model, image_path, extra_path))
            except Exception as exc:
                print(f"{suffix} failed for {model_name}: {exc}", flush=True)
        # Gradient-free Score-CAM (different paradigm from the three gradient methods).
        sc_path = os.path.join(out_dir, f"{model_name}_score_cam.png")
        try:
            extra_maps.append(_score_cam(model, target_layer, image_path, sc_path))
        except Exception as exc:
            print(f"score_cam failed for {model_name}: {exc}", flush=True)
    else:
        if model_name in ("yolo",):
            result = _yolo_overlay(checkpoint_path, image_path, out_path)
            det_ckpt = checkpoint_path
        else:
            det_ckpt = checkpoint_path or os.path.join(CHECKPOINT_DIR, f"{model_name}.pt")
            result = _detection_overlay(model_name, det_ckpt, image_path, out_path)
        # Eigen-CAM backbone saliency, the detector-appropriate analogue.
        eigen_path = os.path.join(out_dir, f"{model_name}_eigencam.png")
        try:
            extra_maps.append(_eigen_cam_detector(model_name, det_ckpt, image_path, eigen_path))
        except Exception as exc:
            print(f"eigen_cam failed for {model_name}: {exc}", flush=True)
        # Gradient-free occlusion sensitivity.
        occ_path = os.path.join(out_dir, f"{model_name}_occlusion.png")
        try:
            extra_maps.append(_occlusion_detector(model_name, det_ckpt, image_path, occ_path))
        except Exception as exc:
            print(f"occlusion failed for {model_name}: {exc}", flush=True)

    result["extra_maps"] = extra_maps
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
