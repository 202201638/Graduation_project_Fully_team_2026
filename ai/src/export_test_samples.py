import argparse
import json
import os
import random
import shutil
from typing import List, Tuple

from src.config import YOLO_DATASET_DIR


def _label_for_file(label_path: str) -> str:
    if not os.path.exists(label_path):
        return "no_pneumonia"
    with open(label_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return "pneumonia" if lines else "no_pneumonia"


def _collect_split_samples(split: str) -> List[Tuple[str, str]]:
    img_dir = os.path.join(YOLO_DATASET_DIR, split, "images")
    label_dir = os.path.join(YOLO_DATASET_DIR, split, "labels")
    if not os.path.isdir(img_dir):
        return []

    samples: List[Tuple[str, str]] = []
    for name in sorted(os.listdir(img_dir)):
        if not name.lower().endswith(".png"):
            continue
        img_path = os.path.join(img_dir, name)
        label_path = os.path.join(label_dir, name.replace(".png", ".txt"))
        label = _label_for_file(label_path)
        samples.append((img_path, label))
    return samples


def export_test_samples(
    out_dir: str = "artifacts/app_test_samples",
    positives: int = 2,
    negatives: int = 2,
    seed: int = 42,
) -> str:
    random.seed(seed)
    all_samples: List[Tuple[str, str]] = []
    for split in ["val", "test", "train"]:
        all_samples.extend(_collect_split_samples(split))

    positive_samples = [s for s in all_samples if s[1] == "pneumonia"]
    negative_samples = [s for s in all_samples if s[1] == "no_pneumonia"]

    if len(positive_samples) < positives:
        raise RuntimeError(f"Requested {positives} pneumonia samples but found only {len(positive_samples)}")
    if len(negative_samples) < negatives:
        raise RuntimeError(f"Requested {negatives} no_pneumonia samples but found only {len(negative_samples)}")

    selected = random.sample(positive_samples, positives) + random.sample(negative_samples, negatives)
    random.shuffle(selected)

    os.makedirs(out_dir, exist_ok=True)
    manifest = {"samples": []}
    for idx, (src_path, label) in enumerate(selected, start=1):
        new_name = f"{idx:02d}_{label}{os.path.splitext(src_path)[1].lower()}"
        dst_path = os.path.join(out_dir, new_name)
        shutil.copy2(src_path, dst_path)
        manifest["samples"].append(
            {
                "file_name": new_name,
                "label": label,
                "source_path": src_path,
            }
        )

    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return out_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export balanced app test samples (pneumonia / no_pneumonia).")
    parser.add_argument("--out", type=str, default="artifacts/app_test_samples")
    parser.add_argument("--positives", type=int, default=2)
    parser.add_argument("--negatives", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out_dir = export_test_samples(
        out_dir=args.out,
        positives=args.positives,
        negatives=args.negatives,
        seed=args.seed,
    )
    print(f"Exported test samples to: {out_dir}")
