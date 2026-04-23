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
from torchvision.models.detection import fasterrcnn_resnet50_fpn, retinanet_resnet50_fpn
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
TORCH_DEVICE = "cpu"
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

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
    "retinanet": ModelCatalogSpec(
        key="retinanet",
        display_name="RetinaNet",
        family=MODEL_FAMILY_DETECTION,
        model_type="torchvision_retinanet_detection",
        task="pneumonia_detection",
        weights_file="retinanet.pt",
        class_names=("pneumonia",),
        default_conf=0.10,
        confirmed_conf=0.25,
        description="Torchvision RetinaNet detector that returns pneumonia boxes.",
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
        }
        filename = mapping.get(key)
        return self._load_json_asset(filename) if filename else None

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
        baseline = self.get_raw_metadata("baseline") or {}
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
        if model_name == "yolo":
            return (
                "mAP50",
                self._float_or_none(metrics.get("map50")),
                "Recall",
                self._float_or_none(metrics.get("recall")),
            )

        if model_name in {"fasterrcnn", "retinanet"}:
            return "Recall", self._float_or_none(metrics.get("recall")), None, None

        return (
            "Accuracy",
            self._float_or_none(metrics.get("accuracy")),
            "F1",
            self._float_or_none(metrics.get("f1")),
        )

    def _build_available_models(self) -> list[Dict[str, Any]]:
        baseline = self.get_raw_metadata("baseline") or {}
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
        elif model_name == "retinanet":
            model = retinanet_resnet50_fpn(weights=None, weights_backbone=None, num_classes=2)
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
                if model_name == "yolo":
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
    ) -> list[dict[str, Any]]:
        if not detections:
            return []

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
        model = self._ensure_model_loaded("yolo")
        if model is None:
            raise RuntimeError(self._load_errors.get("yolo") or "Selected model is unavailable.")

        with self._model_lock:
            started_at = time.perf_counter()
            prediction_results = model.predict(
                source=str(saved_upload.file_path),
                conf=config["default_conf"],
                imgsz=config.get("default_imgsz") or 640,
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
        rendered_filename = self._save_rendered_image(rendered_image, saved_upload, "yolo")

        return {
            "confidence_score": confidence_score,
            "processing_time": processing_time,
            "detections": detections,
            "confirmed_detections_count": len(confirmed_detections),
            "rendered_image_url": f"/uploads/rendered/{rendered_filename}",
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
        rendered_filename = self._save_rendered_image(rendered_image, saved_upload, model_name)

        return {
            "confidence_score": confidence_score,
            "processing_time": processing_time,
            "detections": detections,
            "confirmed_detections_count": len(confirmed_detections),
            "rendered_image_url": f"/uploads/rendered/{rendered_filename}",
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

        with self._model_lock, torch.inference_mode():
            started_at = time.perf_counter()
            logits = model(input_tensor)
            probabilities = torch.softmax(logits, dim=1)[0]
            processing_time = time.perf_counter() - started_at

        pneumonia_probability = float(probabilities[-1].item())
        normal_probability = float(probabilities[0].item())
        diagnosis_status = self._score_to_status(
            pneumonia_probability,
            config["default_conf"],
            config["confirmed_conf"],
        )

        rendered_image = self._load_image_bgr(saved_upload)
        rendered_image = self._draw_banner(
            rendered_image,
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
            "analysis_extras": {
                "pneumonia_probability": round(pneumonia_probability, 4),
                "normal_probability": round(normal_probability, 4),
            },
        }

    def _run_model_prediction(
        self,
        saved_upload: SavedUpload,
        model_name: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        if model_name == "yolo":
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
            },
            "status": "completed",
            "processing_time": round(processing_time, 4),
            "created_at": timestamp,
        }


xray_inference_service = XRayInferenceService()
