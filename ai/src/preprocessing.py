import os
import json
import cv2
import pydicom
import numpy as np
from tqdm import tqdm

from src.config import ARTIFACT_DIR, INPUT_DIR, PNG_DIR, MAX_IMAGES, SEED


# Single CLAHE instance reused for every image. Applying contrast enhancement
# uniformly to ALL images (not just pneumonia-positive ones) is what removes the
# class-conditional preprocessing leak that previously inflated classifier metrics.
_CLAHE = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))


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

    # Uniform CLAHE for every image regardless of label (no leak).
    img = _CLAHE.apply(img)
    return img


def _stratified_dicom_files(df, max_images: int, seed: int):
    """Pick a class-balanced, seeded subset of `{patientId}.dcm` files of size
    ~max_images, stratified by the patient-level pneumonia label."""
    from sklearn.model_selection import train_test_split

    patient_labels = df.groupby("patientId")["Target"].max()
    pids = patient_labels.index.to_numpy()
    y = patient_labels.to_numpy()

    if max_images is None or max_images >= len(pids):
        sampled = pids
    else:
        sampled, _ = train_test_split(
            pids, train_size=max_images, stratify=y, random_state=seed
        )

    available = set(os.listdir(INPUT_DIR))
    files = [f"{pid}.dcm" for pid in sampled if f"{pid}.dcm" in available]
    return files


def convert_dicom_to_png(df=None, max_images=MAX_IMAGES, seed: int = SEED):

    os.makedirs(PNG_DIR, exist_ok=True)

    if df is not None and max_images is not None:
        files = _stratified_dicom_files(df, max_images, seed)
    else:
        files = sorted(os.listdir(INPUT_DIR))
        if max_images is not None:
            files = files[:max_images]

    summary = {
        "input_dir": INPUT_DIR,
        "output_dir": PNG_DIR,
        "total_candidates": len(files),
        "max_images": max_images,
        "stratified": bool(df is not None and max_images is not None),
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
