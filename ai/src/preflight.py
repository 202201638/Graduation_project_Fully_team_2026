import json
from pathlib import Path
from typing import Dict

from src.config import (
    ARTIFACT_DIR,
    CHECKPOINT_DIR,
    DATASET_ROOT,
    INPUT_DIR,
    LABEL_PATH,
    PNG_DIR,
    PROJECT_ROOT,
    YOLO_DATASET_DIR,
    YOLO_DATA_YAML,
)


BACKEND_ASSETS_DIR = PROJECT_ROOT.parent / "Backend" / "model_assets"
EXPECTED_CHECKPOINTS = (
    "fasterrcnn.pt",
    "retinanet.pt",
    "resnet50.pt",
    "densenet121.pt",
    "efficientnet_b0.pt",
)
EXPECTED_BACKEND_ASSETS = (
    "manifest.json",
    "fasterrcnn.pt",
    "phase3_baseline_results.json",
    "web_result.json",
    "demo_output.png",
)


def _json_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def run_preflight_checks() -> Dict[str, bool]:
    artifact_dir = Path(ARTIFACT_DIR)
    checkpoint_dir = Path(CHECKPOINT_DIR)
    app_test_samples_dir = artifact_dir / "app_test_samples"
    manifest = _json_file(BACKEND_ASSETS_DIR / "manifest.json")
    default_model_key = manifest.get("default_model_key")
    model_configs = manifest.get("model_configs") if isinstance(manifest, dict) else {}
    default_model_config = (
        model_configs.get(default_model_key, {}) if isinstance(model_configs, dict) else {}
    )
    default_weights = default_model_config.get("weights_file") or manifest.get("weights_file")

    checks = {
        "input_dir_exists": Path(INPUT_DIR).is_dir(),
        "label_csv_exists": Path(LABEL_PATH).is_file(),
        "png_dir_exists": Path(PNG_DIR).is_dir(),
        "yolo_dataset_exists": Path(YOLO_DATASET_DIR).is_dir(),
        "yolo_data_yaml_exists": Path(YOLO_DATA_YAML).is_file(),
        "artifact_dir_exists": artifact_dir.is_dir(),
        "checkpoint_dir_exists": checkpoint_dir.is_dir(),
        "expected_checkpoints_exist": all(
            (checkpoint_dir / filename).is_file() for filename in EXPECTED_CHECKPOINTS
        ),
        "backend_assets_dir_exists": BACKEND_ASSETS_DIR.is_dir(),
        "backend_expected_assets_exist": all(
            (BACKEND_ASSETS_DIR / filename).is_file() for filename in EXPECTED_BACKEND_ASSETS
        ),
        "backend_manifest_exists": (BACKEND_ASSETS_DIR / "manifest.json").is_file(),
        "backend_default_model_is_fasterrcnn": default_model_key == "fasterrcnn",
        "backend_default_weights_exist": bool(default_weights)
        and (BACKEND_ASSETS_DIR / str(default_weights)).is_file(),
        "app_test_samples_exist": app_test_samples_dir.is_dir()
        and any(app_test_samples_dir.glob("*.png")),
        "app_test_samples_manifest_exists": (app_test_samples_dir / "manifest.json").is_file(),
    }

    print("Preflight checks:")
    print(f"- project_root: {PROJECT_ROOT}")
    print(f"- dataset_root: {DATASET_ROOT}")
    print(f"- backend_assets_dir: {BACKEND_ASSETS_DIR}")
    print(f"- default_model_key: {default_model_key}")
    print(f"- default_weights: {default_weights}")
    for key, value in checks.items():
        print(f"- {key}: {value}")
    return checks
