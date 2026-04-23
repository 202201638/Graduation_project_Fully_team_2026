import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import ARTIFACT_DIR, CHECKPOINT_DIR, PROJECT_ROOT


DETECTION_MODELS = {"yolo", "fasterrcnn", "retinanet"}
CLASSIFICATION_MODELS = {"resnet50", "densenet121", "efficientnet_b0"}
MODEL_CONFIGS = {
    "yolo": {
        "display_name": "YOLO",
        "model_type": "ultralytics_yolo_detection",
        "task": "pneumonia_detection",
        "weights_file": "yolo_best.pt",
        "class_names": ["pneumonia"],
        "default_imgsz": 640,
        "default_conf": 0.1,
        "confirmed_conf": 0.25,
    },
    "fasterrcnn": {
        "display_name": "Faster R-CNN",
        "model_type": "torchvision_fasterrcnn_detection",
        "task": "pneumonia_detection",
        "weights_file": "fasterrcnn.pt",
        "class_names": ["pneumonia"],
        "default_conf": 0.1,
        "confirmed_conf": 0.25,
    },
    "retinanet": {
        "display_name": "RetinaNet",
        "model_type": "torchvision_retinanet_detection",
        "task": "pneumonia_detection",
        "weights_file": "retinanet.pt",
        "class_names": ["pneumonia"],
        "default_conf": 0.1,
        "confirmed_conf": 0.25,
    },
    "resnet50": {
        "display_name": "ResNet50",
        "model_type": "torchvision_resnet50_classification",
        "task": "pneumonia_classification",
        "weights_file": "resnet50.pt",
        "class_names": ["normal", "pneumonia"],
        "input_size": 224,
        "default_conf": 0.5,
        "confirmed_conf": 0.75,
    },
    "densenet121": {
        "display_name": "DenseNet121",
        "model_type": "torchvision_densenet121_classification",
        "task": "pneumonia_classification",
        "weights_file": "densenet121.pt",
        "class_names": ["normal", "pneumonia"],
        "input_size": 224,
        "default_conf": 0.5,
        "confirmed_conf": 0.75,
    },
    "efficientnet_b0": {
        "display_name": "EfficientNet-B0",
        "model_type": "torchvision_efficientnet_b0_classification",
        "task": "pneumonia_classification",
        "weights_file": "efficientnet_b0.pt",
        "class_names": ["normal", "pneumonia"],
        "input_size": 224,
        "default_conf": 0.5,
        "confirmed_conf": 0.75,
    },
}
HANDOFF_JSON_FILES = (
    "phase3_baseline_results.json",
    "phase8_demo_result.json",
    "web_result.json",
    "kaggle_notebook_summary.json",
)
HANDOFF_IMAGE_FILES = ("demo_output.png",)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _metric_value(metrics: Any, metric_name: str) -> float | None:
    if not isinstance(metrics, dict):
        return None
    value = metrics.get(metric_name)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def choose_default_detection_model(
    baseline: dict[str, Any],
    metric_name: str = "recall",
) -> str:
    scored_models: list[tuple[float, str]] = []
    for model_name in DETECTION_MODELS:
        value = _metric_value(baseline.get(model_name), metric_name)
        if value is not None:
            scored_models.append((value, model_name))

    if not scored_models:
        return "fasterrcnn"

    scored_models.sort(reverse=True)
    return scored_models[0][1]


def _source_for_weights(model_name: str, artifacts_dir: Path, checkpoint_dir: Path) -> Path:
    if model_name == "yolo":
        return artifacts_dir.parent / "runs" / "phase3_yolo_baseline" / "weights" / "best.pt"
    return checkpoint_dir / MODEL_CONFIGS[model_name]["weights_file"]


def build_manifest(default_model_key: str) -> dict[str, Any]:
    default_config = MODEL_CONFIGS[default_model_key]
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "default_model_key": default_model_key,
        "model_type": default_config["model_type"],
        "weights_file": default_config["weights_file"],
        "task": default_config["task"],
        "class_names": default_config["class_names"],
        "default_imgsz": default_config.get("default_imgsz"),
        "default_conf": default_config["default_conf"],
        "confirmed_conf": default_config["confirmed_conf"],
        "model_configs": MODEL_CONFIGS,
        "status": "COMPLETED",
        "handoff_files": sorted(
            {
                "manifest.json",
                *HANDOFF_JSON_FILES,
                *HANDOFF_IMAGE_FILES,
                *(config["weights_file"] for config in MODEL_CONFIGS.values()),
            }
        ),
        "limitations": {
            "detection_models": "YOLO, Faster R-CNN, and RetinaNet can draw pneumonia boxes.",
            "classification_models": "ResNet50, DenseNet121, and EfficientNet-B0 produce image-level probabilities only.",
        },
    }


def promote_model_assets(
    backend_assets_dir: Path | None = None,
    metric_name: str = "recall",
    apply_changes: bool = False,
) -> dict[str, Any]:
    artifacts_dir = Path(ARTIFACT_DIR)
    checkpoint_dir = Path(CHECKPOINT_DIR)
    backend_dir = backend_assets_dir or PROJECT_ROOT.parent / "Backend" / "model_assets"
    baseline = _load_json(artifacts_dir / "phase3_baseline_results.json")
    default_model_key = choose_default_detection_model(baseline, metric_name)
    manifest = build_manifest(default_model_key)

    copy_plan: list[tuple[Path, Path]] = []
    for filename in HANDOFF_JSON_FILES + HANDOFF_IMAGE_FILES:
        source = artifacts_dir / filename
        if source.is_file():
            copy_plan.append((source, backend_dir / filename))

    for model_name in MODEL_CONFIGS:
        source = _source_for_weights(model_name, artifacts_dir, checkpoint_dir)
        if source.is_file():
            copy_plan.append((source, backend_dir / MODEL_CONFIGS[model_name]["weights_file"]))

    if apply_changes:
        backend_dir.mkdir(parents=True, exist_ok=True)
        for source, destination in copy_plan:
            shutil.copy2(source, destination)
        with (backend_dir / "manifest.json").open("w", encoding="utf-8") as file:
            json.dump(manifest, file, indent=2)

    return {
        "apply_changes": apply_changes,
        "backend_assets_dir": str(backend_dir),
        "default_model_key": default_model_key,
        "metric_name": metric_name,
        "files_to_copy": [
            {"source": str(source), "destination": str(destination)}
            for source, destination in copy_plan
        ],
        "manifest": manifest,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote deployable model artifacts.")
    parser.add_argument("--metric", default="recall", help="Metric used to choose detection default.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually copy files and write manifest. Default is dry-run.",
    )
    parser.add_argument(
        "--backend-assets-dir",
        type=Path,
        default=None,
        help="Override Backend/model_assets destination.",
    )
    args = parser.parse_args()
    result = promote_model_assets(
        backend_assets_dir=args.backend_assets_dir,
        metric_name=args.metric,
        apply_changes=args.apply,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
