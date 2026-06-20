from __future__ import annotations

import io
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image, UnidentifiedImageError
from torchvision import transforms
from torchvision.models import densenet121, efficientnet_b0, resnet50
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.ops import nms
from torchvision.transforms import functional as transforms_functional

from app.utils.security import generate_analysis_id

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_ASSETS_DIR = BASE_DIR / "model_assets"


def _backend_path_from_env(name: str, default_relative: str) -> Path:
    raw_value = os.getenv(name)
    path = Path(raw_value) if raw_value else BASE_DIR / default_relative
    return path if path.is_absolute() else BASE_DIR / path


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


UPLOADS_DIR = _backend_path_from_env("UPLOAD_DIR", "uploads")
RENDERED_DIR = UPLOADS_DIR / "rendered"
ULTRALYTICS_CONFIG_DIR = BASE_DIR / ".ultralytics"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
MAX_FILE_SIZE = _int_env("MAX_FILE_SIZE", 10 * 1024 * 1024)
# Use the GPU automatically when a CUDA-enabled torch build is present; fall back to CPU.
# Set XRAY_FORCE_CPU=1 to force CPU even when CUDA is available.
TORCH_DEVICE = "cuda" if (torch.cuda.is_available() and os.getenv("XRAY_FORCE_CPU") != "1") else "cpu"
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
# Grad-CAM heatmap weight when blending over the original X-ray (0..1).
GRADCAM_BLEND_ALPHA = 0.40

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)
ULTRALYTICS_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(ULTRALYTICS_CONFIG_DIR))

DIAGNOSIS_STATUS_CONFIRMED = "pneumonia_detected"
DIAGNOSIS_STATUS_SUSPECTED = "suspected_pneumonia"
DIAGNOSIS_STATUS_CLEAR = "no_pneumonia_detected"
MODEL_FAMILY_DETECTION = "detection"
MODEL_FAMILY_CLASSIFICATION = "classification"
DEFAULT_MODEL_KEY = "fasterrcnn"
DETECTION_NMS_IOU_THRESHOLD = 0.30
MAX_RENDERED_DETECTIONS = 3
# Ultralytics YOLO-family models share one load + predict path.
YOLO_MODEL_KEYS = {"yolo"}


@dataclass(frozen=True)
class ModelCatalogSpec:
    key: str
    display_name: str
    family: str
    model_type: str
    task: str
    weights_file: str
    class_names: tuple[str, ...]
    default_conf: float
    confirmed_conf: float
    default_imgsz: Optional[int] = None
    input_size: Optional[int] = None
    description: str = ""


MODEL_REGISTRY: dict[str, ModelCatalogSpec] = {
    "yolo": ModelCatalogSpec(
        key="yolo",
        display_name="YOLO",
        family=MODEL_FAMILY_DETECTION,
        model_type="ultralytics_yolo_detection",
        task="pneumonia_detection",
        weights_file="yolo_best.pt",
        class_names=("pneumonia",),
        default_conf=0.10,
        confirmed_conf=0.25,
        default_imgsz=640,
        description="Ultralytics YOLO detector that returns pneumonia regions.",
    ),
    "fasterrcnn": ModelCatalogSpec(
        key="fasterrcnn",
        display_name="Faster R-CNN",
        family=MODEL_FAMILY_DETECTION,
        model_type="torchvision_fasterrcnn_detection",
        task="pneumonia_detection",
        weights_file="fasterrcnn.pt",
        class_names=("pneumonia",),
        default_conf=0.10,
        confirmed_conf=0.25,
        description="Torchvision Faster R-CNN detector that returns pneumonia boxes.",
    ),
    "resnet50": ModelCatalogSpec(
        key="resnet50",
        display_name="ResNet50",
        family=MODEL_FAMILY_CLASSIFICATION,
        model_type="torchvision_resnet50_classification",
        task="pneumonia_classification",
        weights_file="resnet50.pt",
        class_names=("normal", "pneumonia"),
        default_conf=0.50,
        confirmed_conf=0.75,
        input_size=224,
        description="ResNet50 classifier that predicts whole-image pneumonia probability.",
    ),
    "densenet121": ModelCatalogSpec(
        key="densenet121",
        display_name="DenseNet121",
        family=MODEL_FAMILY_CLASSIFICATION,
        model_type="torchvision_densenet121_classification",
        task="pneumonia_classification",
        weights_file="densenet121.pt",
        class_names=("normal", "pneumonia"),
        default_conf=0.50,
        confirmed_conf=0.75,
        input_size=224,
        description="DenseNet121 classifier that predicts whole-image pneumonia probability.",
    ),
    "efficientnet_b0": ModelCatalogSpec(
        key="efficientnet_b0",
        display_name="EfficientNet-B0",
        family=MODEL_FAMILY_CLASSIFICATION,
        model_type="torchvision_efficientnet_b0_classification",
        task="pneumonia_classification",
        weights_file="efficientnet_b0.pt",
        class_names=("normal", "pneumonia"),
        default_conf=0.50,
        confirmed_conf=0.75,
        input_size=224,
        description="EfficientNet-B0 classifier that predicts whole-image pneumonia probability.",
    ),
}


@dataclass
class SavedUpload:
    original_filename: str
    stored_filename: str
    file_path: Path
    image_url: str
    file_size_bytes: int
    image_width: int
    image_height: int


class XRayInferenceService:
    def __init__(self) -> None:
        self._models: Dict[str, Any] = {}
        self._model_lock = threading.Lock()
        self._load_errors: Dict[str, str] = {}
        self._json_cache: Dict[str, Optional[Dict[str, Any]]] = {}

    def _load_json_asset(self, filename: str) -> Optional[Dict[str, Any]]:
        if filename not in self._json_cache:
            asset_path = MODEL_ASSETS_DIR / filename
            if asset_path.exists():
                with asset_path.open("r", encoding="utf-8") as file:
                    self._json_cache[filename] = json.load(file)
            else:
                self._json_cache[filename] = None
        return self._json_cache[filename]

    def get_manifest(self) -> Dict[str, Any]:
        return self._load_json_asset("manifest.json") or {}

    def get_raw_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        mapping = {
            "manifest": "manifest.json",
            "baseline": "phase3_baseline_results.json",
            "web_result": "web_result.json",
            "demo_result": "phase8_demo_result.json",
            "model_metrics": "model_metrics.json",
        }
        filename = mapping.get(key)
        return self._load_json_asset(filename) if filename else None

    def _all_model_metrics(self) -> Dict[str, Any]:
        """Per-model honest held-out test metrics for the deployed checkpoints.

        Prefers model_metrics.json (the deployed/validation-best metrics); falls back to
        the legacy phase3_baseline_results.json so older asset bundles still render.
        """
        metrics = self._load_json_asset("model_metrics.json")
        if isinstance(metrics, dict) and metrics:
            return metrics
        return self.get_raw_metadata("baseline") or {}

    def get_model_metrics(self, model_name: str) -> Dict[str, Any]:
        entry = self._all_model_metrics().get(model_name)
        return entry if isinstance(entry, dict) else {}

    def resolve_model_name(self, model_name: Optional[str] = None) -> str:
        requested_name = (
            model_name or self.get_manifest().get("default_model_key") or DEFAULT_MODEL_KEY
        )
        normalized_name = str(requested_name).strip().lower()

        if normalized_name not in MODEL_REGISTRY:
            available_keys = ", ".join(sorted(MODEL_REGISTRY))
            raise ValueError(
                f"Unsupported model '{requested_name}'. Available models: {available_keys}."
            )

        return normalized_name

    def _get_model_overrides(self, model_name: str) -> Dict[str, Any]:
        manifest = self.get_manifest()
        model_configs = manifest.get("model_configs")
        if isinstance(model_configs, dict):
            overrides = model_configs.get(model_name)
            if isinstance(overrides, dict):
                return overrides
        return {}

    def _get_model_config(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        resolved_name = self.resolve_model_name(model_name)
        spec = MODEL_REGISTRY[resolved_name]
        overrides = self._get_model_overrides(resolved_name)

        config = {
            "key": spec.key,
            "display_name": spec.display_name,
            "family": spec.family,
            "model_type": spec.model_type,
            "task": spec.task,
            "weights_file": spec.weights_file,
            "class_names": list(spec.class_names),
            "default_conf": spec.default_conf,
            "confirmed_conf": spec.confirmed_conf,
            "default_imgsz": spec.default_imgsz,
            "input_size": spec.input_size,
            "description": spec.description,
        }
        config.update(overrides)

        class_names = config.get("class_names")
        if isinstance(class_names, list):
            config["class_names"] = [str(name) for name in class_names]
        else:
            config["class_names"] = list(spec.class_names)

        default_conf = float(config.get("default_conf", spec.default_conf))
        confirmed_conf = float(config.get("confirmed_conf", spec.confirmed_conf))
        if confirmed_conf < default_conf:
            confirmed_conf = default_conf

        config["default_conf"] = default_conf
        config["confirmed_conf"] = confirmed_conf
        config["default_imgsz"] = (
            int(config["default_imgsz"]) if config.get("default_imgsz") is not None else None
        )
        config["input_size"] = (
            int(config["input_size"]) if config.get("input_size") is not None else None
        )

        return config

    def _float_or_none(self, value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _summarize_baseline(self) -> Dict[str, Any]:
        baseline = self._all_model_metrics()
        summary: Dict[str, Any] = {}

        for model_name in MODEL_REGISTRY:
            model_metrics = baseline.get(model_name)
            if isinstance(model_metrics, dict):
                summary[model_name] = model_metrics

        return summary

    def _select_metric_summary(
        self,
        model_name: str,
        metrics: Dict[str, Any],
    ) -> tuple[Optional[str], Optional[float], Optional[str], Optional[float]]:
        if model_name in {"yolo", "fasterrcnn"}:
            return (
                "mAP@0.5",
                self._float_or_none(metrics.get("map50")),
                "Recall",
                self._float_or_none(metrics.get("recall")),
            )

        return (
            "AUC",
            self._float_or_none(metrics.get("auc")),
            "Sensitivity",
            self._float_or_none(metrics.get("recall")),
        )

    def _build_available_models(self) -> list[Dict[str, Any]]:
        baseline = self._all_model_metrics()
        available_models: list[Dict[str, Any]] = []

        for model_name in MODEL_REGISTRY:
            config = self._get_model_config(model_name)
            weights_path = MODEL_ASSETS_DIR / config["weights_file"]
            metrics = baseline.get(model_name)
            metrics = metrics if isinstance(metrics, dict) else {}
            primary_label, primary_value, secondary_label, secondary_value = (
                self._select_metric_summary(model_name, metrics)
            )

            available_models.append(
                {
                    "key": model_name,
                    "display_name": config["display_name"],
                    "model_family": config["family"],
                    "model_type": config["model_type"],
                    "task": config["task"],
                    "weights_file": config["weights_file"],
                    "available": weights_path.exists(),
                    "loaded": model_name in self._models,
                    "class_names": config["class_names"],
                    "default_conf": config["default_conf"],
                    "confirmed_conf": config["confirmed_conf"],
                    "default_imgsz": config.get("default_imgsz"),
                    "input_size": config.get("input_size"),
                    "description": config.get("description"),
                    "metrics": metrics,
                    "primary_metric_label": primary_label,
                    "primary_metric_value": primary_value,
                    "secondary_metric_label": secondary_label,
                    "secondary_metric_value": secondary_value,
                    "load_error": self._load_errors.get(model_name),
                }
            )

        return available_models

    def get_metadata_summary(self) -> Dict[str, Any]:
        summary = {
            "manifest": self.get_manifest(),
            "baseline": self._summarize_baseline(),
            "web_result": self.get_raw_metadata("web_result") or {},
            "available_models": self._build_available_models(),
            "default_model_key": self.resolve_model_name(),
        }
        demo_result = self.get_raw_metadata("demo_result")
        if demo_result is not None:
            summary["demo_result"] = demo_result
        return summary

    def get_status(self) -> Dict[str, Any]:
        config = self._get_model_config()
        weights_path = MODEL_ASSETS_DIR / config["weights_file"]
        model_name = config["key"]
        model_loaded = model_name in self._models
        load_error = self._load_errors.get(model_name)

        if model_loaded:
            runtime_status = "ready"
        elif load_error:
            runtime_status = "degraded"
        else:
            runtime_status = "idle"

        return {
            "status": runtime_status,
            "model_loaded": model_loaded,
            "weights_file": config["weights_file"],
            "weights_exists": weights_path.exists(),
            "model_type": config["model_type"],
            "task": config["task"],
            "class_names": config["class_names"],
            "default_conf": config["default_conf"],
            "confirmed_conf": config["confirmed_conf"],
            "default_imgsz": config.get("default_imgsz"),
            "default_model_key": model_name,
            "display_name": config["display_name"],
            "model_family": config["family"],
            "available_models": self._build_available_models(),
            "metadata_available": {
                "manifest": (MODEL_ASSETS_DIR / "manifest.json").exists(),
                "baseline": (MODEL_ASSETS_DIR / "phase3_baseline_results.json").exists(),
                "web_result": (MODEL_ASSETS_DIR / "web_result.json").exists(),
                "demo_result": (MODEL_ASSETS_DIR / "phase8_demo_result.json").exists(),
            },
            "load_error": load_error,
        }

    def warmup(self) -> Dict[str, Any]:
        self._ensure_model_loaded(self.resolve_model_name())
        return self.get_status()

    def validate_and_save_upload(self, filename: str, contents: bytes) -> SavedUpload:
        if not filename:
            raise ValueError("A file name is required.")

        file_extension = Path(filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise ValueError(
                "Invalid file format. Supported formats: JPG, JPEG, PNG, BMP, TIFF."
            )

        if not contents:
            raise ValueError("Uploaded file is empty.")

        if len(contents) > MAX_FILE_SIZE:
            raise ValueError("Uploaded file exceeds the 10MB size limit.")

        try:
            with Image.open(io.BytesIO(contents)) as image:
                image.verify()
            with Image.open(io.BytesIO(contents)) as image:
                width, height = image.size
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError("Uploaded file is not a valid image.") from exc

        stored_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOADS_DIR / stored_filename
        file_path.write_bytes(contents)

        return SavedUpload(
            original_filename=filename,
            stored_filename=stored_filename,
            file_path=file_path,
            image_url=f"/uploads/{stored_filename}",
            file_size_bytes=len(contents),
            image_width=width,
            image_height=height,
        )

    def _torch_load_state_dict(self, weights_path: Path) -> Dict[str, Any]:
        try:
            return torch.load(str(weights_path), map_location=TORCH_DEVICE, weights_only=True)
        except TypeError:
            return torch.load(str(weights_path), map_location=TORCH_DEVICE)

    def _build_classification_transform(self, input_size: int):
        return transforms.Compose(
            [
                transforms.Resize((input_size, input_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ]
        )

    def _gradcam_target_layer(self, model, model_name: str):
        """Last convolutional feature map to explain, per architecture."""
        if model_name == "resnet50":
            return model.layer4[-1]
        if model_name == "densenet121":
            return model.features[-2]
        if model_name == "efficientnet_b0":
            return model.features[-1]
        return None

    def _write_attribution_overlay(
        self,
        cam: np.ndarray,
        base_bgr: np.ndarray,
        model_name: str,
        saved_upload: SavedUpload,
        suffix: str = "gradcam",
    ) -> str:
        """Blend a normalized 0-1 saliency map over the X-ray as a JET heatmap.

        Shared by every pixel-attribution method (Grad-CAM, Integrated Gradients,
        GradientSHAP, Eigen-CAM); `suffix` keeps the rendered files distinct.
        """
        height, width = base_bgr.shape[:2]
        cam_resized = cv2.resize(cam.astype(np.float32), (width, height))
        heatmap = cv2.applyColorMap(np.uint8(255 * np.clip(cam_resized, 0.0, 1.0)), cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(
            heatmap, GRADCAM_BLEND_ALPHA, base_bgr, 1.0 - GRADCAM_BLEND_ALPHA, 0.0
        )
        filename = f"{saved_upload.file_path.stem}_{model_name}_{suffix}.png"
        out_path = RENDERED_DIR / filename
        if not cv2.imwrite(str(out_path), overlay):
            raise RuntimeError(f"Failed to write {suffix} overlay image.")
        return f"/uploads/rendered/{filename}"

    @staticmethod
    def _attribution_to_cam(attribution: "torch.Tensor") -> np.ndarray:
        """Collapse a (C, H, W) pixel attribution into a normalized 0-1 saliency map."""
        cam = attribution.abs().sum(dim=0)
        cam = cam - cam.min()
        cam_max = float(cam.max())
        if cam_max > 0:
            cam = cam / cam_max
        return cam.detach().cpu().numpy()

    def _integrated_gradients(
        self,
        model,
        model_name: str,
        input_tensor: "torch.Tensor",
        base_bgr: np.ndarray,
        saved_upload: SavedUpload,
        steps: int = 24,
        chunk: int = 8,
    ) -> str:
        """Integrated Gradients saliency for the pneumonia class (index 1).

        Integrates the gradient of the pneumonia logit along a straight path from a
        black baseline to the input, batched in small chunks to bound memory.
        """
        model.zero_grad(set_to_none=True)
        baseline = torch.zeros_like(input_tensor)
        delta = input_tensor - baseline
        alphas = torch.linspace(
            1.0 / steps, 1.0, steps, device=input_tensor.device
        ).view(steps, 1, 1, 1)

        grad_accum = torch.zeros_like(input_tensor)
        for start in range(0, steps, chunk):
            sub_path = (baseline + alphas[start : start + chunk] * delta).detach().requires_grad_(True)
            logits = model(sub_path)
            score = logits[:, 1].sum()
            grads = torch.autograd.grad(score, sub_path)[0]
            grad_accum = grad_accum + grads.sum(dim=0, keepdim=True)

        ig = (delta * (grad_accum / steps))[0]
        cam = self._attribution_to_cam(ig)
        return self._write_attribution_overlay(
            cam, base_bgr, model_name, saved_upload, "integrated_gradients"
        )

    def _gradient_shap(
        self,
        model,
        model_name: str,
        input_tensor: "torch.Tensor",
        base_bgr: np.ndarray,
        saved_upload: SavedUpload,
        n_samples: int = 8,
        stdev: float = 0.15,
    ) -> str:
        """GradientSHAP saliency for the pneumonia class (index 1).

        Averages (input - baseline) * gradient over several noisy, randomly
        interpolated samples (the gradient-based SHAP estimator).
        """
        model.zero_grad(set_to_none=True)
        baseline = torch.zeros_like(input_tensor)
        shap_accum = torch.zeros_like(input_tensor)
        for _ in range(n_samples):
            alpha = float(torch.rand(1).item())
            noised = input_tensor + torch.randn_like(input_tensor) * stdev
            interpolated = (baseline + alpha * (noised - baseline)).detach().requires_grad_(True)
            logits = model(interpolated)
            score = logits[:, 1].sum()
            grads = torch.autograd.grad(score, interpolated)[0]
            shap_accum = shap_accum + (noised - baseline) * grads

        shap_values = (shap_accum / n_samples)[0]
        cam = self._attribution_to_cam(shap_values)
        return self._write_attribution_overlay(
            cam, base_bgr, model_name, saved_upload, "gradient_shap"
        )

    def _score_cam(
        self,
        model,
        model_name: str,
        input_tensor: "torch.Tensor",
        base_bgr: np.ndarray,
        saved_upload: SavedUpload,
        top_k: int = 96,
        batch: int = 16,
    ) -> str:
        """Score-CAM saliency for the pneumonia class (gradient-free, class-discriminative).

        Masks the input with each upsampled activation channel and weights that channel
        by the resulting pneumonia score. Limited to the top-K channels (by mean
        activation) and batched so it stays fast on the GPU.
        """
        target_layer = self._gradcam_target_layer(model, model_name)
        if target_layer is None:
            raise RuntimeError(f"No Score-CAM target layer for {model_name}.")

        captured: Dict[str, Any] = {}

        def _hook(_module, _inputs, output):
            captured["value"] = output

        handle = target_layer.register_forward_hook(_hook)
        try:
            with torch.inference_mode():
                model(input_tensor)
        finally:
            handle.remove()

        activations = captured.get("value")
        if activations is None:
            raise RuntimeError("Score-CAM captured no activation.")
        activations = activations[0].float()  # (C, H, W)
        channels = activations.shape[0]
        k = min(top_k, channels)

        # Keep the most active channels, then upsample + min-max normalize each to [0, 1].
        energy = activations.mean(dim=(1, 2))
        top_idx = torch.topk(energy, k).indices
        size = tuple(input_tensor.shape[-2:])
        maps = nn.functional.interpolate(
            activations[top_idx].unsqueeze(1), size=size, mode="bilinear", align_corners=False
        )  # (k, 1, Hin, Win)
        flat = maps.view(k, -1)
        mins = flat.min(dim=1, keepdim=True).values
        maxs = flat.max(dim=1, keepdim=True).values
        maps = ((flat - mins) / (maxs - mins + 1e-8)).view(k, 1, *size)

        scores = torch.zeros(k, device=input_tensor.device)
        with torch.inference_mode():
            for start in range(0, k, batch):
                masked = input_tensor * maps[start : start + batch]  # (b, C, Hin, Win)
                logits = model(masked)
                scores[start : start + batch] = torch.softmax(logits, dim=1)[:, 1]

        weights = torch.relu(scores).view(k, 1, 1)
        cam = torch.relu((weights * maps.squeeze(1)).sum(dim=0))
        cam = cam - cam.min()
        cam_max = float(cam.max())
        if cam_max > 0:
            cam = cam / cam_max
        return self._write_attribution_overlay(
            cam.detach().cpu().numpy(), base_bgr, model_name, saved_upload, "score_cam"
        )

    def _eigencam_target_layer(self, model, model_name: str):
        """Last high-level conv block to read for Eigen-CAM, per detector architecture."""
        if model_name == "fasterrcnn":
            return model.backbone.body.layer4[-1]
        if model_name in YOLO_MODEL_KEYS:
            # ultralytics DetectionModel: the block just before the Detect head.
            return model.model.model[-2]
        return None

    @staticmethod
    def _eigen_cam_from_activation(activation: np.ndarray) -> np.ndarray:
        """First principal component of a (C, H, W) activation, normalized to 0-1."""
        channels, height, width = activation.shape
        reshaped = np.nan_to_num(activation.reshape(channels, -1).T)  # (H*W, C)
        reshaped = reshaped - reshaped.mean(axis=0, keepdims=True)
        try:
            _u, _s, vt = np.linalg.svd(reshaped, full_matrices=False)
            projection = reshaped @ vt[0]
        except np.linalg.LinAlgError:
            projection = reshaped.mean(axis=1)
        cam = projection.reshape(height, width)
        cam = cam - cam.min()
        cam_max = float(cam.max())
        if cam_max > 0:
            cam = cam / cam_max
        return cam.astype(np.float32)

    def _detector_eigencam(
        self,
        model,
        model_name: str,
        base_bgr: np.ndarray,
        saved_upload: SavedUpload,
    ) -> Optional[str]:
        """Eigen-CAM saliency for a detector (activation-based, target-free, no gradients)."""
        target_layer = self._eigencam_target_layer(model, model_name)
        if target_layer is None:
            return None

        captured: Dict[str, Any] = {}

        def _hook(_module, _inputs, output):
            captured["value"] = output

        handle = target_layer.register_forward_hook(_hook)
        try:
            if model_name in YOLO_MODEL_KEYS:
                model.predict(
                    source=str(saved_upload.file_path),
                    imgsz=640,
                    device=0 if TORCH_DEVICE == "cuda" else "cpu",
                    verbose=False,
                )
            else:
                with Image.open(saved_upload.file_path) as pil_image:
                    rgb_image = pil_image.convert("RGB")
                tensor = transforms_functional.to_tensor(rgb_image).to(TORCH_DEVICE)
                with torch.inference_mode():
                    model([tensor])
        finally:
            handle.remove()

        activation = captured.get("value")
        if isinstance(activation, dict):
            activation = list(activation.values())[-1]
        if isinstance(activation, (list, tuple)):
            activation = activation[0]
        if activation is None:
            return None

        activation = activation.detach().float().cpu().numpy()[0]
        cam = self._eigen_cam_from_activation(activation)
        return self._write_attribution_overlay(cam, base_bgr, model_name, saved_upload, "eigencam")

    def _detector_top_confidence(self, model, model_name: str, images_rgb: list) -> list:
        """Top detection confidence for a batch of RGB uint8 images (gradient-free)."""
        if model_name in YOLO_MODEL_KEYS:
            sources = [cv2.cvtColor(img, cv2.COLOR_RGB2BGR) for img in images_rgb]
            results = model.predict(
                source=sources,
                imgsz=640,
                conf=0.001,
                device=0 if TORCH_DEVICE == "cuda" else "cpu",
                verbose=False,
            )
            confidences = []
            for result in results:
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    confidences.append(float(boxes.conf.max().item()))
                else:
                    confidences.append(0.0)
            return confidences

        tensors = [
            torch.from_numpy(img).permute(2, 0, 1).float().to(TORCH_DEVICE) / 255.0
            for img in images_rgb
        ]
        with torch.inference_mode():
            outputs = model(tensors)
        confidences = []
        for output in outputs:
            scores = output.get("scores")
            confidences.append(
                float(scores.max().item()) if scores is not None and scores.numel() else 0.0
            )
        return confidences

    def _detector_occlusion(
        self,
        model,
        model_name: str,
        base_bgr: np.ndarray,
        saved_upload: SavedUpload,
        grid: int = 10,
    ) -> Optional[str]:
        """Occlusion-sensitivity saliency for a detector (gradient-free, uniform across families).

        Blanks each cell of a coarse grid and measures the drop in the top detection
        confidence; larger drops mean the region mattered more. Batched to stay fast on GPU.
        """
        size = 640
        img = cv2.cvtColor(cv2.resize(base_bgr, (size, size)), cv2.COLOR_BGR2RGB)
        mean_color = tuple(int(c) for c in img.reshape(-1, 3).mean(axis=0))

        baseline_conf = self._detector_top_confidence(model, model_name, [img])[0]
        if baseline_conf <= 0.0:
            return None  # nothing detected to explain

        cell = size // grid
        occluded, cells = [], []
        for gy in range(grid):
            for gx in range(grid):
                patch = img.copy()
                patch[gy * cell : (gy + 1) * cell, gx * cell : (gx + 1) * cell] = mean_color
                occluded.append(patch)
                cells.append((gy, gx))

        # Keep Faster R-CNN batches small: larger ones thrash the 3050 Ti's 4 GB into
        # shared host memory and become ~50x slower, so 4 is the safe sweet spot.
        batch = 4 if model_name == "fasterrcnn" else 16
        importance = np.zeros((grid, grid), dtype=np.float32)
        for start in range(0, len(occluded), batch):
            confidences = self._detector_top_confidence(model, model_name, occluded[start : start + batch])
            for (gy, gx), conf in zip(cells[start : start + batch], confidences):
                importance[gy, gx] = max(0.0, baseline_conf - conf)

        cam = importance - importance.min()
        cam_max = float(cam.max())
        if cam_max > 0:
            cam = cam / cam_max
        return self._write_attribution_overlay(cam, base_bgr, model_name, saved_upload, "occlusion")

    def _detector_explainability_maps(
        self,
        model,
        model_name: str,
        base_bgr: np.ndarray,
        saved_upload: SavedUpload,
    ) -> list[dict[str, str]]:
        """Eigen-CAM + Occlusion heatmaps for a detector, each best-effort so it can't break the prediction."""
        maps: list[dict[str, str]] = []
        try:
            eigen_url = self._detector_eigencam(model, model_name, base_bgr, saved_upload)
            if eigen_url:
                maps.append(
                    {
                        "key": "eigencam",
                        "label": "Eigen-CAM",
                        "image_url": eigen_url,
                        "caption": "Eigen-CAM: principal activation of the detector backbone (where the network focuses).",
                    }
                )
        except Exception as exc:
            print(f"Eigen-CAM failed for {model_name}: {exc}")
        try:
            occlusion_url = self._detector_occlusion(model, model_name, base_bgr, saved_upload)
            if occlusion_url:
                maps.append(
                    {
                        "key": "occlusion",
                        "label": "Occlusion",
                        "image_url": occlusion_url,
                        "caption": "Occlusion sensitivity: regions where hiding the image most reduces the model's detection confidence.",
                    }
                )
        except Exception as exc:
            print(f"Occlusion failed for {model_name}: {exc}")
        return maps

    def _classify_with_gradcam(
        self,
        model,
        model_name: str,
        input_tensor: "torch.Tensor",
        base_bgr: np.ndarray,
        saved_upload: SavedUpload,
    ) -> tuple["torch.Tensor", Optional[str]]:
        """One grad-enabled forward that yields both the softmax and a Grad-CAM overlay.

        The CAM targets the pneumonia class (index 1) so the heatmap always shows the
        regions that pushed the model toward a pneumonia decision. Returns
        (detached_probabilities, heatmap_url). heatmap_url is None if no target layer.
        """
        target_layer = self._gradcam_target_layer(model, model_name)
        activations: Dict[str, Any] = {}
        gradients: Dict[str, Any] = {}

        def _forward_hook(_module, _inputs, output):
            activations["value"] = output

        def _backward_hook(_module, _grad_in, grad_out):
            gradients["value"] = grad_out[0]

        handles = []
        if target_layer is not None:
            handles.append(target_layer.register_forward_hook(_forward_hook))
            handles.append(target_layer.register_full_backward_hook(_backward_hook))

        try:
            model.zero_grad(set_to_none=True)
            logits = model(input_tensor)
            probabilities = torch.softmax(logits, dim=1)[0].detach()

            heatmap_url: Optional[str] = None
            if target_layer is not None:
                score = logits[:, 1].sum()
                score.backward()
                acts = activations.get("value")
                grads = gradients.get("value")
                if acts is not None and grads is not None:
                    weights = grads.detach().mean(dim=(2, 3), keepdim=True)
                    cam = torch.relu((weights * acts.detach()).sum(dim=1, keepdim=True))[0, 0]
                    cam = cam - cam.min()
                    cam_max = float(cam.max())
                    if cam_max > 0:
                        cam = cam / cam_max
                    heatmap_url = self._write_attribution_overlay(
                        cam.cpu().numpy(), base_bgr, model_name, saved_upload, "gradcam"
                    )
        finally:
            for handle in handles:
                handle.remove()
            model.zero_grad(set_to_none=True)

        return probabilities, heatmap_url

    def _load_classification_model(self, model_name: str, weights_path: Path):
        if model_name == "resnet50":
            model = resnet50(weights=None)
            model.fc = nn.Sequential(nn.Dropout(0.2), nn.Linear(model.fc.in_features, 2))
        elif model_name == "densenet121":
            model = densenet121(weights=None)
            model.classifier = nn.Sequential(
                nn.Dropout(0.2),
                nn.Linear(model.classifier.in_features, 2),
            )
        elif model_name == "efficientnet_b0":
            model = efficientnet_b0(weights=None)
            model.classifier = nn.Sequential(
                nn.Dropout(0.2),
                nn.Linear(model.classifier[1].in_features, 2),
            )
        else:
            raise RuntimeError(f"Unsupported classification model '{model_name}'.")

        model.load_state_dict(self._torch_load_state_dict(weights_path), strict=True)
        model.to(TORCH_DEVICE)
        model.eval()
        return model

    def _load_detection_model(self, model_name: str, weights_path: Path):
        if model_name == "fasterrcnn":
            model = fasterrcnn_resnet50_fpn(weights=None, weights_backbone=None, num_classes=2)
        else:
            raise RuntimeError(f"Unsupported detection model '{model_name}'.")

        model.load_state_dict(self._torch_load_state_dict(weights_path), strict=True)
        model.to(TORCH_DEVICE)
        model.eval()
        return model

    def _load_yolo_model(self, weights_path: Path):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "ultralytics is not installed. Install Backend requirements before running inference."
            ) from exc

        return YOLO(str(weights_path))

    def _ensure_model_loaded(self, model_name: str):
        if model_name in self._models:
            return self._models[model_name]

        config = self._get_model_config(model_name)
        weights_path = MODEL_ASSETS_DIR / config["weights_file"]

        if not weights_path.exists():
            self._load_errors[model_name] = (
                f"Required weights file not found: {weights_path.name}"
            )
            return None

        with self._model_lock:
            if model_name in self._models:
                return self._models[model_name]

            try:
                if model_name in YOLO_MODEL_KEYS:
                    model = self._load_yolo_model(weights_path)
                elif config["family"] == MODEL_FAMILY_CLASSIFICATION:
                    model = self._load_classification_model(model_name, weights_path)
                else:
                    model = self._load_detection_model(model_name, weights_path)
            except Exception as exc:
                self._load_errors[model_name] = f"Failed to load model weights: {exc}"
                return None

            self._models[model_name] = model
            self._load_errors.pop(model_name, None)
            return model

    def _load_image_bgr(self, saved_upload: SavedUpload) -> np.ndarray:
        image = cv2.imread(str(saved_upload.file_path))
        if image is not None:
            return image

        with Image.open(saved_upload.file_path) as pil_image:
            rgb_image = pil_image.convert("RGB")
        return cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)

    def _save_rendered_image(
        self,
        image: np.ndarray,
        saved_upload: SavedUpload,
        model_name: str,
    ) -> str:
        rendered_filename = f"{saved_upload.file_path.stem}_{model_name}_rendered.png"
        rendered_path = RENDERED_DIR / rendered_filename
        if not cv2.imwrite(str(rendered_path), image):
            raise RuntimeError("Failed to write rendered prediction image.")
        return rendered_filename

    def _draw_banner(
        self,
        image: np.ndarray,
        title: str,
        subtitle: str,
        color: tuple[int, int, int],
    ) -> np.ndarray:
        output = image.copy()
        banner_height = 80
        output = cv2.copyMakeBorder(
            output,
            banner_height,
            0,
            0,
            0,
            cv2.BORDER_CONSTANT,
            value=(15, 23, 42),
        )
        cv2.putText(
            output,
            title,
            (24, 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            color,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            output,
            subtitle,
            (24, 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (226, 232, 240),
            1,
            cv2.LINE_AA,
        )
        return output

    def _status_color(self, diagnosis_status: str) -> tuple[int, int, int]:
        if diagnosis_status == DIAGNOSIS_STATUS_CONFIRMED:
            return (60, 76, 231)
        if diagnosis_status == DIAGNOSIS_STATUS_SUSPECTED:
            return (9, 179, 245)
        return (34, 197, 94)

    def _postprocess_detections(
        self,
        detections: list[dict[str, Any]],
        nms_iou_threshold: float = DETECTION_NMS_IOU_THRESHOLD,
        apply_nms: bool = True,
    ) -> list[dict[str, Any]]:
        if not detections:
            return []

        # Torchvision detectors (Faster R-CNN) already run NMS internally; a second
        # pass here would merge valid adjacent regions. Only YOLO output needs this safety NMS.
        if not apply_nms:
            return sorted(detections, key=lambda item: item["confidence"], reverse=True)

        boxes = torch.tensor(
            [
                [
                    detection["bbox"]["x1"],
                    detection["bbox"]["y1"],
                    detection["bbox"]["x2"],
                    detection["bbox"]["y2"],
                ]
                for detection in detections
            ],
            dtype=torch.float32,
        )
        scores = torch.tensor(
            [detection["confidence"] for detection in detections],
            dtype=torch.float32,
        )

        keep_indices = nms(boxes, scores, nms_iou_threshold).tolist()
        filtered_detections = [detections[index] for index in keep_indices]
        filtered_detections.sort(key=lambda item: item["confidence"], reverse=True)
        return filtered_detections

    def _select_detections_for_render(
        self,
        detections: list[dict[str, Any]],
        confirmed_confidence_threshold: float,
    ) -> list[dict[str, Any]]:
        if not detections:
            return []

        confirmed_detections = [
            detection
            for detection in detections
            if detection["confidence"] >= confirmed_confidence_threshold
        ]
        if confirmed_detections:
            return confirmed_detections[:MAX_RENDERED_DETECTIONS]

        return detections[:1]

    def _render_detection_overlay(
        self,
        image: np.ndarray,
        detections: list[dict[str, Any]],
        diagnosis_status: str,
        model_display_name: str,
        confidence_score: float,
    ) -> np.ndarray:
        rendered_image = image.copy()

        for detection in detections:
            bbox = detection["bbox"]
            box_status = (
                DIAGNOSIS_STATUS_CONFIRMED
                if diagnosis_status == DIAGNOSIS_STATUS_CONFIRMED
                else DIAGNOSIS_STATUS_SUSPECTED
            )
            color = self._status_color(box_status)
            cv2.rectangle(
                rendered_image,
                (int(bbox["x1"]), int(bbox["y1"])),
                (int(bbox["x2"]), int(bbox["y2"])),
                color,
                2,
            )
            cv2.putText(
                rendered_image,
                f"{detection['label']} {detection['confidence'] * 100:.1f}%",
                (int(bbox["x1"]), max(24, int(bbox["y1"]) - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )

        return self._draw_banner(
            rendered_image,
            model_display_name,
            f"{diagnosis_status.replace('_', ' ').title()} | Top score {confidence_score * 100:.1f}%",
            self._status_color(diagnosis_status),
        )

    def _score_to_status(
        self,
        score: float,
        inference_conf: float,
        confirmed_conf: float,
    ) -> str:
        if score >= confirmed_conf:
            return DIAGNOSIS_STATUS_CONFIRMED
        if score >= inference_conf:
            return DIAGNOSIS_STATUS_SUSPECTED
        return DIAGNOSIS_STATUS_CLEAR

    def _build_findings(
        self,
        diagnosis_status: str,
        model_family: str,
        confidence_score: float,
        detection_count: int,
        confirmed_detection_count: int,
        model_display_name: str,
    ) -> str:
        if model_family == MODEL_FAMILY_CLASSIFICATION:
            confidence_label = f"{confidence_score * 100:.1f}%"
            if diagnosis_status == DIAGNOSIS_STATUS_CONFIRMED:
                return (
                    f"{model_display_name} classified the uploaded chest X-ray as pneumonia"
                    f" with {confidence_label} confidence."
                )
            if diagnosis_status == DIAGNOSIS_STATUS_SUSPECTED:
                return (
                    f"{model_display_name} assigned an intermediate pneumonia probability of"
                    f" {confidence_label} to the uploaded chest X-ray."
                )
            return (
                f"{model_display_name} did not classify the uploaded chest X-ray as pneumonia"
                " above the configured threshold."
            )

        if diagnosis_status == DIAGNOSIS_STATUS_CONFIRMED:
            if confirmed_detection_count == 1:
                return "A pneumonia region was detected in the uploaded chest X-ray."
            return (
                f"{confirmed_detection_count} pneumonia regions were detected in the uploaded"
                " chest X-ray."
            )

        if diagnosis_status == DIAGNOSIS_STATUS_SUSPECTED:
            if detection_count == 1:
                return (
                    "A low-confidence region suspicious for pneumonia was detected in the"
                    " uploaded chest X-ray."
                )
            return (
                f"{detection_count} low-confidence regions suspicious for pneumonia were detected"
                " in the uploaded chest X-ray."
            )

        return "No pneumonia regions were detected in the uploaded chest X-ray."

    def _build_recommendations(self, diagnosis_status: str, model_family: str) -> str:
        if model_family == MODEL_FAMILY_CLASSIFICATION:
            if diagnosis_status == DIAGNOSIS_STATUS_CONFIRMED:
                return (
                    "The classifier indicates pneumonia with high confidence. Review the scan,"
                    " correlate with the clinical presentation, and confirm with a radiologist."
                )
            if diagnosis_status == DIAGNOSIS_STATUS_SUSPECTED:
                return (
                    "The classifier indicates a possible pneumonia pattern below the confirmation"
                    " threshold. Perform targeted image review and correlate with symptoms or"
                    " follow-up imaging."
                )
            return (
                "The classifier did not indicate pneumonia above threshold. Continue with standard"
                " clinical review."
            )

        if diagnosis_status == DIAGNOSIS_STATUS_CONFIRMED:
            return (
                "Review the highlighted region with a radiologist and confirm the finding with the"
                " full clinical context."
            )

        if diagnosis_status == DIAGNOSIS_STATUS_SUSPECTED:
            return (
                "Possible pneumonia features were found below the confirmation threshold. Review"
                " the highlighted area with a radiologist and correlate with symptoms or follow-up"
                " imaging."
            )

        return "No pneumonia detection was produced by the model. Continue with standard clinical review."

    def _predict_with_yolo(self, saved_upload: SavedUpload, config: Dict[str, Any]) -> Dict[str, Any]:
        model_key = config["key"]
        model = self._ensure_model_loaded(model_key)
        if model is None:
            raise RuntimeError(self._load_errors.get(model_key) or "Selected model is unavailable.")

        with self._model_lock:
            started_at = time.perf_counter()
            prediction_results = model.predict(
                source=str(saved_upload.file_path),
                conf=config["default_conf"],
                imgsz=config.get("default_imgsz") or 640,
                device=0 if TORCH_DEVICE == "cuda" else "cpu",
                verbose=False,
            )
            processing_time = time.perf_counter() - started_at

        prediction = prediction_results[0]
        class_names = getattr(prediction, "names", {}) or {}
        detections = []

        if prediction.boxes is not None:
            for box in prediction.boxes:
                class_id = int(box.cls[0].item()) if box.cls is not None else 0
                confidence = float(box.conf[0].item()) if box.conf is not None else 0.0
                x1, y1, x2, y2 = [round(float(value), 2) for value in box.xyxy[0].tolist()]

                detections.append(
                    {
                        "label": class_names.get(class_id, "pneumonia"),
                        "class_id": class_id,
                        "confidence": round(confidence, 4),
                        "bbox": {
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                        },
                    }
                )

        detections = self._postprocess_detections(detections)
        confirmed_detections = [
            detection
            for detection in detections
            if detection["confidence"] >= config["confirmed_conf"]
        ]
        diagnosis_status = (
            DIAGNOSIS_STATUS_CONFIRMED
            if confirmed_detections
            else DIAGNOSIS_STATUS_SUSPECTED
            if detections
            else DIAGNOSIS_STATUS_CLEAR
        )
        confidence_score = detections[0]["confidence"] if detections else 0.0
        render_detections = self._select_detections_for_render(
            detections,
            config["confirmed_conf"],
        )
        rendered_source = self._load_image_bgr(saved_upload)
        rendered_image = self._render_detection_overlay(
            rendered_source,
            render_detections,
            diagnosis_status,
            config["display_name"],
            confidence_score,
        )
        rendered_filename = self._save_rendered_image(rendered_image, saved_upload, model_key)
        explainability_maps = self._detector_explainability_maps(
            model, model_key, rendered_source, saved_upload
        )

        return {
            "confidence_score": confidence_score,
            "processing_time": processing_time,
            "detections": detections,
            "confirmed_detections_count": len(confirmed_detections),
            "rendered_image_url": f"/uploads/rendered/{rendered_filename}",
            "explainability_maps": explainability_maps,
            "analysis_extras": {},
        }

    def _predict_with_torchvision_detector(
        self,
        saved_upload: SavedUpload,
        model_name: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        model = self._ensure_model_loaded(model_name)
        if model is None:
            raise RuntimeError(
                self._load_errors.get(model_name) or "Selected model is unavailable."
            )

        with Image.open(saved_upload.file_path) as pil_image:
            rgb_image = pil_image.convert("RGB")
        input_tensor = transforms_functional.to_tensor(rgb_image).to(TORCH_DEVICE)

        with self._model_lock, torch.inference_mode():
            started_at = time.perf_counter()
            output = model([input_tensor])[0]
            processing_time = time.perf_counter() - started_at

        raw_boxes = output.get("boxes")
        raw_scores = output.get("scores")
        raw_labels = output.get("labels")
        detections = []
        class_names = config["class_names"]

        if raw_boxes is not None and raw_scores is not None and raw_labels is not None:
            for box, score, label in zip(raw_boxes, raw_scores, raw_labels):
                confidence = float(score.item())
                class_id = int(label.item())
                if confidence < config["default_conf"] or class_id <= 0:
                    continue

                positive_class_index = class_id - 1
                label_text = (
                    class_names[positive_class_index]
                    if 0 <= positive_class_index < len(class_names)
                    else "pneumonia"
                )
                x1, y1, x2, y2 = [round(float(value), 2) for value in box.tolist()]
                detections.append(
                    {
                        "label": label_text,
                        "class_id": positive_class_index,
                        "confidence": round(confidence, 4),
                        "bbox": {
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                        },
                    }
                )

        detections = self._postprocess_detections(detections, apply_nms=False)
        confirmed_detections = [
            detection
            for detection in detections
            if detection["confidence"] >= config["confirmed_conf"]
        ]

        diagnosis_status = (
            DIAGNOSIS_STATUS_CONFIRMED
            if confirmed_detections
            else DIAGNOSIS_STATUS_SUSPECTED
            if detections
            else DIAGNOSIS_STATUS_CLEAR
        )
        confidence_score = detections[0]["confidence"] if detections else 0.0

        render_detections = self._select_detections_for_render(
            detections,
            config["confirmed_conf"],
        )
        rendered_source = self._load_image_bgr(saved_upload)
        rendered_image = self._render_detection_overlay(
            rendered_source,
            render_detections,
            diagnosis_status,
            config["display_name"],
            confidence_score,
        )
        rendered_filename = self._save_rendered_image(rendered_image, saved_upload, model_name)
        explainability_maps = self._detector_explainability_maps(
            model, model_name, rendered_source, saved_upload
        )

        return {
            "confidence_score": confidence_score,
            "processing_time": processing_time,
            "detections": detections,
            "confirmed_detections_count": len(confirmed_detections),
            "rendered_image_url": f"/uploads/rendered/{rendered_filename}",
            "explainability_maps": explainability_maps,
            "analysis_extras": {},
        }

    def _predict_with_classifier(
        self,
        saved_upload: SavedUpload,
        model_name: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        model = self._ensure_model_loaded(model_name)
        if model is None:
            raise RuntimeError(
                self._load_errors.get(model_name) or "Selected model is unavailable."
            )

        input_size = config.get("input_size") or 224
        preprocess = self._build_classification_transform(input_size)

        with Image.open(saved_upload.file_path) as pil_image:
            rgb_image = pil_image.convert("RGB")
        input_tensor = preprocess(rgb_image).unsqueeze(0).to(TORCH_DEVICE)
        base_bgr = self._load_image_bgr(saved_upload)

        heatmap_url: Optional[str] = None
        explainability_maps: list[dict[str, str]] = []
        with self._model_lock:
            started_at = time.perf_counter()
            try:
                probabilities, heatmap_url = self._classify_with_gradcam(
                    model, model_name, input_tensor, base_bgr, saved_upload
                )
            except Exception as exc:  # explainability must never break the prediction
                print(f"Grad-CAM failed for {model_name}: {exc}")
                with torch.inference_mode():
                    probabilities = torch.softmax(model(input_tensor), dim=1)[0]

            if heatmap_url:
                explainability_maps.append(
                    {
                        "key": "gradcam",
                        "label": "Grad-CAM",
                        "image_url": heatmap_url,
                        "caption": "Grad-CAM: lung regions that most increased the pneumonia score.",
                    }
                )
            # Two extra attribution methods, each best-effort so one failure can't break the result.
            for key, label, method, caption in (
                (
                    "integrated_gradients",
                    "Integrated Gradients",
                    self._integrated_gradients,
                    "Integrated Gradients: per-pixel attribution accumulated from a black baseline to this image.",
                ),
                (
                    "gradient_shap",
                    "GradientSHAP",
                    self._gradient_shap,
                    "GradientSHAP: SHAP-style pixel attribution averaged over several noisy baselines.",
                ),
                (
                    "score_cam",
                    "Score-CAM",
                    self._score_cam,
                    "Score-CAM: gradient-free class-discriminative map; regions whose activations most raise the pneumonia score.",
                ),
            ):
                try:
                    url = method(model, model_name, input_tensor, base_bgr, saved_upload)
                    explainability_maps.append(
                        {"key": key, "label": label, "image_url": url, "caption": caption}
                    )
                except Exception as exc:
                    print(f"{label} failed for {model_name}: {exc}")
            processing_time = time.perf_counter() - started_at

        pneumonia_probability = float(probabilities[-1].item())
        normal_probability = float(probabilities[0].item())
        diagnosis_status = self._score_to_status(
            pneumonia_probability,
            config["default_conf"],
            config["confirmed_conf"],
        )

        rendered_image = self._draw_banner(
            base_bgr.copy(),
            config["display_name"],
            f"Pneumonia probability {pneumonia_probability * 100:.1f}% | Normal {normal_probability * 100:.1f}%",
            self._status_color(diagnosis_status),
        )
        rendered_filename = self._save_rendered_image(rendered_image, saved_upload, model_name)

        return {
            "confidence_score": pneumonia_probability,
            "processing_time": processing_time,
            "detections": [],
            "confirmed_detections_count": 0,
            "rendered_image_url": f"/uploads/rendered/{rendered_filename}",
            "heatmap_image_url": heatmap_url,
            "explainability_maps": explainability_maps,
            "analysis_extras": {
                "pneumonia_probability": round(pneumonia_probability, 4),
                "normal_probability": round(normal_probability, 4),
                "explainability": [entry["key"] for entry in explainability_maps] or None,
            },
        }

    def _run_model_prediction(
        self,
        saved_upload: SavedUpload,
        model_name: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        if model_name in YOLO_MODEL_KEYS:
            return self._predict_with_yolo(saved_upload, config)

        if config["family"] == MODEL_FAMILY_CLASSIFICATION:
            return self._predict_with_classifier(saved_upload, model_name, config)

        return self._predict_with_torchvision_detector(saved_upload, model_name, config)

    def predict(
        self,
        saved_upload: SavedUpload,
        patient_id: Optional[str] = None,
        scan_type: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        resolved_model_name = self.resolve_model_name(model_name)
        config = self._get_model_config(resolved_model_name)
        model = self._ensure_model_loaded(resolved_model_name)
        if model is None:
            raise RuntimeError(
                self._load_errors.get(resolved_model_name) or "Selected model is unavailable."
            )

        prediction = self._run_model_prediction(saved_upload, resolved_model_name, config)
        detections = prediction["detections"]
        confidence_score = float(prediction["confidence_score"])
        diagnosis_status = self._score_to_status(
            confidence_score,
            config["default_conf"],
            config["confirmed_conf"],
        )
        if config["family"] == MODEL_FAMILY_DETECTION and detections:
            diagnosis_status = (
                DIAGNOSIS_STATUS_CONFIRMED
                if prediction["confirmed_detections_count"] > 0
                else DIAGNOSIS_STATUS_SUSPECTED
            )
        elif config["family"] == MODEL_FAMILY_DETECTION:
            diagnosis_status = DIAGNOSIS_STATUS_CLEAR

        pneumonia_detected = diagnosis_status == DIAGNOSIS_STATUS_CONFIRMED
        suspected_pneumonia = diagnosis_status == DIAGNOSIS_STATUS_SUSPECTED
        processing_time = float(prediction["processing_time"])
        timestamp = datetime.now(UTC)

        analysis_details = {
            "model_name": resolved_model_name,
            "model_display_name": config["display_name"],
            "model_family": config["family"],
            "model_type": config["model_type"],
            "task": config["task"],
            "weights_file": config["weights_file"],
            "processing_time_seconds": round(processing_time, 4),
            "image_width": saved_upload.image_width,
            "image_height": saved_upload.image_height,
            "file_size_bytes": saved_upload.file_size_bytes,
            "default_conf": config["default_conf"],
            "confirmed_conf": config["confirmed_conf"],
            "default_imgsz": config.get("default_imgsz"),
            "input_size": config.get("input_size"),
            "detections_count": len(detections),
            "confirmed_detections_count": prediction["confirmed_detections_count"],
            "device": TORCH_DEVICE,
            "supports_bounding_boxes": config["family"] == MODEL_FAMILY_DETECTION,
        }
        analysis_details.update(prediction["analysis_extras"])

        return {
            "analysis_id": generate_analysis_id(),
            "patient_id": patient_id or None,
            "scan_type": scan_type or None,
            "model_name": resolved_model_name,
            "model_display_name": config["display_name"],
            "model_family": config["family"],
            "image_filename": saved_upload.original_filename,
            "result": {
                "pneumonia_detected": pneumonia_detected,
                "suspected_pneumonia": suspected_pneumonia,
                "diagnosis_status": diagnosis_status,
                "confidence_score": round(confidence_score, 4),
                "findings": self._build_findings(
                    diagnosis_status,
                    config["family"],
                    confidence_score,
                    len(detections),
                    prediction["confirmed_detections_count"],
                    config["display_name"],
                ),
                "recommendations": self._build_recommendations(
                    diagnosis_status,
                    config["family"],
                ),
                "analysis_details": analysis_details,
                "detections": detections,
                "original_image_url": saved_upload.image_url,
                "rendered_image_url": prediction["rendered_image_url"],
                "heatmap_image_url": prediction.get("heatmap_image_url"),
                "explainability_maps": prediction.get("explainability_maps", []),
                "model_metrics": self.get_model_metrics(resolved_model_name),
            },
            "status": "completed",
            "processing_time": round(processing_time, 4),
            "created_at": timestamp,
        }


xray_inference_service = XRayInferenceService()
