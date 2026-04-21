import os
from pathlib import Path
from typing import Iterable, Union


PathLike = Union[str, os.PathLike]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_NAME = os.getenv("RSNA_DATASET_NAME", "rsna-pneumonia-detection-challenge")


def _existing_path(candidates: Iterable[PathLike], fallback: PathLike) -> Path:
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.exists():
            return path
    return Path(fallback).expanduser()


def _project_output_path(env_key: str, default_relative: str) -> Path:
    raw_value = os.getenv(env_key)
    if raw_value:
        return Path(raw_value).expanduser()
    return PROJECT_ROOT / default_relative


DATASET_ROOT = _existing_path(
    candidates=[
        os.getenv("RSNA_DATA_DIR"),
        PROJECT_ROOT / "data" / DATASET_NAME,
        Path("/kaggle/input") / DATASET_NAME,
        Path("/kaggle/input/competitions") / DATASET_NAME,
    ],
    fallback=PROJECT_ROOT / "data" / DATASET_NAME,
)

INPUT_DIR = os.fspath(DATASET_ROOT / "stage_2_train_images")
LABEL_PATH = os.fspath(DATASET_ROOT / "stage_2_train_labels.csv")

PNG_DIR = os.fspath(_project_output_path("PNG_DIR", "png_images"))
YOLO_DATASET_DIR = os.fspath(_project_output_path("YOLO_DATASET_DIR", "yolo_dataset"))
YOLO_DATA_YAML = os.fspath(Path(YOLO_DATASET_DIR) / "data.yaml")
RUNS_DIR = os.fspath(_project_output_path("RUNS_DIR", "runs"))
ARTIFACT_DIR = os.fspath(_project_output_path("ARTIFACT_DIR", "artifacts"))
CHECKPOINT_DIR = os.fspath(Path(ARTIFACT_DIR) / "checkpoints")

DEFAULT_YOLO_WEIGHTS = os.fspath(
    _existing_path(
        candidates=[
            os.getenv("YOLO_WEIGHTS_PATH"),
            PROJECT_ROOT / "yolov8n.pt",
            PROJECT_ROOT / "yolo26n.pt",
        ],
        fallback=PROJECT_ROOT / "yolov8n.pt",
    )
)

IMG_SIZE = 640
MAX_IMAGES = 12000

