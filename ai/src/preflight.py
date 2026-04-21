import os
from typing import Dict

from src.config import DATASET_ROOT, INPUT_DIR, LABEL_PATH, PNG_DIR, PROJECT_ROOT, YOLO_DATASET_DIR, YOLO_DATA_YAML


def run_preflight_checks() -> Dict[str, bool]:
    checks = {
        "input_dir_exists": os.path.isdir(INPUT_DIR),
        "label_csv_exists": os.path.isfile(LABEL_PATH),
        "png_dir_exists": os.path.isdir(PNG_DIR),
        "yolo_dataset_exists": os.path.isdir(YOLO_DATASET_DIR),
        "yolo_data_yaml_exists": os.path.isfile(YOLO_DATA_YAML),
    }
    print("Preflight checks:")
    print(f"- project_root: {PROJECT_ROOT}")
    print(f"- dataset_root: {DATASET_ROOT}")
    for k, v in checks.items():
        print(f"- {k}: {v}")
    return checks
