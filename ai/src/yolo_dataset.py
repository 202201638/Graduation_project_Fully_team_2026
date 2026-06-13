import os
import json
import cv2
import pandas as pd
from tqdm import tqdm
from sklearn.model_selection import train_test_split

from src.config import ARTIFACT_DIR, PNG_DIR, YOLO_DATASET_DIR, IMG_SIZE, SEED


def _write_yolo_data_yaml(output_dir: str):
    yaml_path = os.path.join(output_dir, "data.yaml")
    lines = [
        "train: train/images",
        "val: val/images",
        "test: test/images",
        "",
        "nc: 1",
        "names:",
        "  - pneumonia",
        "",
    ]
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def build_yolo_dataset(df):
    """Build a train/val/test YOLO dataset from the converted PNGs.

    Preprocessing is identical for every image regardless of class: resize to
    IMG_SIZE and scale boxes. NO class-conditional augmentation is applied here
    (that previously leaked the label via a CLAHE contrast signature). Real,
    on-the-fly augmentation is applied to the train split during training only.
    """

    OUTPUT_DIR = YOLO_DATASET_DIR

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(OUTPUT_DIR, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(OUTPUT_DIR, split, "labels"), exist_ok=True)

    # original image dimensions (PNGs are stored already resized to IMG_SIZE; boxes
    # are scaled using these originals). Falls back to the PNG's own size if absent.
    dims = {}
    for dims_path in (os.path.join(PNG_DIR, "image_dims.json"),
                      os.path.join(ARTIFACT_DIR, "image_dims.json")):
        if os.path.exists(dims_path):
            with open(dims_path, "r", encoding="utf-8") as f:
                dims = json.load(f)
            break

    # patients that have png images
    png_files = [f for f in os.listdir(PNG_DIR) if f.endswith(".png")]
    png_patient_ids = set(f.replace(".png", "") for f in png_files)

    patients = df["patientId"].unique()
    patients = [p for p in patients if p in png_patient_ids]

    if len(patients) == 0:
        raise ValueError("No PNG images found")

    df = df[df["patientId"].isin(patients)]

    # patient-level labels for a stratified, leak-free split
    patient_labels = df.groupby("patientId")["Target"].max()
    patients = list(patient_labels.index)
    strat = patient_labels.to_numpy()

    # patient-wise split: 60% train / 20% val / 20% test, stratified by label
    train_ids, temp_ids, _, temp_strat = train_test_split(
        patients, strat, test_size=0.4, random_state=SEED, stratify=strat
    )
    val_ids, test_ids = train_test_split(
        temp_ids, test_size=0.5, random_state=SEED, stratify=temp_strat
    )

    splits = {
        "train": train_ids,
        "val": val_ids,
        "test": test_ids,
    }
    summary = {
        "output_dir": OUTPUT_DIR,
        "total_patients_with_png": len(patients),
        "splits": {
            s: {"total_ids": len(ids), "saved_images": 0, "positive_labels": 0, "negative_labels": 0}
            for s, ids in splits.items()
        },
    }

    for split, ids in splits.items():

        split_df = df[df["patientId"].isin(ids)]

        for patient_id in tqdm(ids, desc=f"Processing {split}"):

            img_path = os.path.join(PNG_DIR, f"{patient_id}.png")

            if not os.path.exists(img_path):
                continue

            img = cv2.imread(img_path)
            if img is None:
                continue

            if img.ndim == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            # original dimensions for box scaling (PNG may already be resized to IMG_SIZE)
            if patient_id in dims:
                h, w = dims[patient_id]
            else:
                h, w = img.shape[:2]

            boxes_df = split_df[split_df["patientId"] == patient_id]

            bboxes = []
            for _, row in boxes_df.iterrows():
                if row["Target"] == 1:
                    x1 = row["x"]
                    y1 = row["y"]
                    x2 = x1 + row["width"]
                    y2 = y1 + row["height"]

                    # clip to image bounds
                    x1 = max(0, min(x1, w - 1))
                    x2 = max(0, min(x2, w - 1))
                    y1 = max(0, min(y1, h - 1))
                    y2 = max(0, min(y2, h - 1))

                    if x2 <= x1 or y2 <= y1:
                        continue

                    bboxes.append([x1, y1, x2, y2])

            img_resized = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            out_img = os.path.join(OUTPUT_DIR, split, "images", f"{patient_id}.png")
            cv2.imwrite(out_img, img_resized)
            out_label = os.path.join(OUTPUT_DIR, split, "labels", f"{patient_id}.txt")

            if not bboxes:
                # negative example: image + empty label file
                open(out_label, "w").close()
                summary["splits"][split]["saved_images"] += 1
                summary["splits"][split]["negative_labels"] += 1
                continue

            scale_x = IMG_SIZE / w
            scale_y = IMG_SIZE / h

            yolo_lines = []
            for x1, y1, x2, y2 in bboxes:
                x1 *= scale_x
                x2 *= scale_x
                y1 *= scale_y
                y2 *= scale_y

                x_center = ((x1 + x2) / 2) / IMG_SIZE
                y_center = ((y1 + y2) / 2) / IMG_SIZE
                bw = (x2 - x1) / IMG_SIZE
                bh = (y2 - y1) / IMG_SIZE

                # single class 0 = pneumonia
                yolo_lines.append(f"0 {x_center} {y_center} {bw} {bh}")

            with open(out_label, "w") as f:
                f.write("\n".join(yolo_lines))
            summary["splits"][split]["saved_images"] += 1
            summary["splits"][split]["positive_labels"] += 1

    _write_yolo_data_yaml(OUTPUT_DIR)
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    summary_path = os.path.join(ARTIFACT_DIR, "phase2_yolo_dataset_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("YOLO dataset creation finished")
    print(f"Phase 2 summary saved to {summary_path}")
