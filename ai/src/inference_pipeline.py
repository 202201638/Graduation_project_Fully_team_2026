import argparse
import os
from glob import glob
from typing import Dict, List

from src.config import RUNS_DIR
from src.phase8_demo import run_phase8_demo


def _resolve_input_images(source: str) -> List[str]:
    if os.path.isfile(source):
        return [source]
    if os.path.isdir(source):
        images = sorted(glob(os.path.join(source, "*.png")))
        images += sorted(glob(os.path.join(source, "*.jpg")))
        images += sorted(glob(os.path.join(source, "*.jpeg")))
        return images
    raise FileNotFoundError(f"Input not found: {source}")


def run_inference(source: str, model_path: str = os.path.join(RUNS_DIR, "phase5_yolov8_optimized", "weights", "best.pt")) -> Dict[str, Dict]:
    images = _resolve_input_images(source)
    if not images:
        raise RuntimeError(f"No images found in {source}")
    outputs: Dict[str, Dict] = {}
    for img_path in images:
        outputs[img_path] = run_phase8_demo(img_path, model_path=model_path)
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Final pneumonia inference pipeline")
    parser.add_argument("--source", type=str, required=True, help="Image path or folder path")
    parser.add_argument(
        "--model",
        type=str,
        default=os.path.join(RUNS_DIR, "phase5_yolov8_optimized", "weights", "best.pt"),
    )
    args = parser.parse_args()

    results = run_inference(source=args.source, model_path=args.model)
    for path, out in results.items():
        print(f"{path} -> detected={out['detected']} confidence={out['confidence']} output={out['output_image']}")
