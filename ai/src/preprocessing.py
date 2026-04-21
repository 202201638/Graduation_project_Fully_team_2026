import os
import json
import cv2
import pydicom
import numpy as np
from tqdm import tqdm
from src.config import ARTIFACT_DIR, INPUT_DIR, PNG_DIR, MAX_IMAGES


def _normalize_xray(img: np.ndarray) -> np.ndarray:

    # robust intensity normalization for chest X-rays
    img = img.astype(np.float32)
    p2, p98 = np.percentile(img, (2, 98))
    if p98 > p2:
        img = np.clip(img, p2, p98)
        img = (img - p2) / (p98 - p2)
    else:
        img = cv2.normalize(img, None, 0.0, 1.0, cv2.NORM_MINMAX)

    img = (img * 255.0).clip(0, 255).astype(np.uint8)
    return img


def convert_dicom_to_png():

    os.makedirs(PNG_DIR, exist_ok=True)

    files = os.listdir(INPUT_DIR)[:MAX_IMAGES]
    summary = {
        "input_dir": INPUT_DIR,
        "output_dir": PNG_DIR,
        "total_candidates": len(files),
        "converted": 0,
        "skipped_corrupt": 0,
    }

    for file in tqdm(files, desc="Converting DICOM to PNG"):

        dicom_path = os.path.join(INPUT_DIR, file)

        try:
            ds = pydicom.dcmread(dicom_path)
            img = ds.pixel_array
        except Exception as e:
            print(f"Skipping corrupt DICOM {dicom_path}: {e}")
            summary["skipped_corrupt"] += 1
            continue

        if img.ndim > 2:
            img = img[..., 0]

        img = _normalize_xray(img)

        filename = file.replace(".dcm", ".png")
        out_path = os.path.join(PNG_DIR, filename)

        cv2.imwrite(out_path, img)
        summary["converted"] += 1

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    summary_path = os.path.join(ARTIFACT_DIR, "phase1_conversion_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("DICOM to PNG conversion finished")
    print(f"Phase 1 summary saved to {summary_path}")
