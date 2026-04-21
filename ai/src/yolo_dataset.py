import os
import json
import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.model_selection import train_test_split
import albumentations as A

from src.config import ARTIFACT_DIR, PNG_DIR, YOLO_DATASET_DIR, IMG_SIZE


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

    OUTPUT_DIR = YOLO_DATASET_DIR

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for split in ["train","val","test"]:
        os.makedirs(os.path.join(OUTPUT_DIR,split,"images"),exist_ok=True)
        os.makedirs(os.path.join(OUTPUT_DIR,split,"labels"),exist_ok=True)

    # patients that have png images
    png_files = os.listdir(PNG_DIR)
    png_patient_ids = [f.replace(".png","") for f in png_files]

    patients = df["patientId"].unique()
    patients = [p for p in patients if p in png_patient_ids]

    if len(patients)==0:
        raise ValueError("No PNG images found")

    df = df[df["patientId"].isin(patients)]

    # patient-wise split
    train_ids,temp_ids = train_test_split(patients,test_size=0.4,random_state=42)
    val_ids,test_ids = train_test_split(temp_ids,test_size=0.5,random_state=42)

    splits={
        "train":train_ids,
        "val":val_ids,
        "test":test_ids
    }
    summary = {
        "output_dir": OUTPUT_DIR,
        "total_patients_with_png": len(patients),
        "splits": {
            "train": {"total_ids": len(train_ids), "saved_images": 0, "positive_labels": 0, "negative_labels": 0},
            "val": {"total_ids": len(val_ids), "saved_images": 0, "positive_labels": 0, "negative_labels": 0},
            "test": {"total_ids": len(test_ids), "saved_images": 0, "positive_labels": 0, "negative_labels": 0},
        },
    }

    augmenter = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.Rotate(limit=15,p=0.5),
        A.CLAHE(clip_limit=2.0,p=1.0),
        A.RandomBrightnessContrast(0.2,0.2,p=0.5),
        A.RandomScale(0.1,p=0.5)
    ],bbox_params=A.BboxParams(format="pascal_voc",label_fields=["class_labels"]))

    for split,ids in splits.items():

        split_df=df[df["patientId"].isin(ids)]

        for patient_id in tqdm(ids,desc=f"Processing {split}"):

            img_path=os.path.join(PNG_DIR,f"{patient_id}.png")

            if not os.path.exists(img_path):
                continue

            img=cv2.imread(img_path)
            if img is None:
                continue

            if img.ndim == 2:
                h, w = img.shape
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                h, w, _ = img.shape

            boxes_df=split_df[split_df["patientId"]==patient_id]

            bboxes=[]
            labels=[]

            for _,row in boxes_df.iterrows():
                if row["Target"]==1:
                    x1=row["x"]
                    y1=row["y"]
                    x2=x1+row["width"]
                    y2=y1+row["height"]

                    # clip to image bounds
                    x1 = max(0, min(x1, w - 1))
                    x2 = max(0, min(x2, w - 1))
                    y1 = max(0, min(y1, h - 1))
                    y2 = max(0, min(y2, h - 1))

                    if x2 <= x1 or y2 <= y1:
                        continue

                    bboxes.append([x1,y1,x2,y2])
                    labels.append(0)  # single class 0 for pneumonia in YOLO format

            if not bboxes:
                # negative example: save image and empty label file
                img_resized = cv2.resize(img,(IMG_SIZE,IMG_SIZE))
                out_img=os.path.join(OUTPUT_DIR,split,"images",f"{patient_id}.png")
                cv2.imwrite(out_img,img_resized)

                out_label=os.path.join(OUTPUT_DIR,split,"labels",f"{patient_id}.txt")
                open(out_label,"w").close()
                summary["splits"][split]["saved_images"] += 1
                summary["splits"][split]["negative_labels"] += 1
                continue

            augmented=augmenter(image=img,bboxes=bboxes,class_labels=labels)

            img=augmented["image"]
            bboxes=augmented["bboxes"]
            labels=augmented["class_labels"]

            img=cv2.resize(img,(IMG_SIZE,IMG_SIZE))

            scale_x=IMG_SIZE/w
            scale_y=IMG_SIZE/h

            yolo_lines=[]

            for bbox,cls in zip(bboxes,labels):

                x1,y1,x2,y2=bbox

                x1*=scale_x
                x2*=scale_x
                y1*=scale_y
                y2*=scale_y

                x_center=((x1+x2)/2)/IMG_SIZE
                y_center=((y1+y2)/2)/IMG_SIZE
                bw=(x2-x1)/IMG_SIZE
                bh=(y2-y1)/IMG_SIZE

                yolo_lines.append(f"{int(cls)} {x_center} {y_center} {bw} {bh}")

            out_img=os.path.join(OUTPUT_DIR,split,"images",f"{patient_id}.png")
            cv2.imwrite(out_img,img)

            out_label=os.path.join(OUTPUT_DIR,split,"labels",f"{patient_id}.txt")

            with open(out_label,"w") as f:
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
