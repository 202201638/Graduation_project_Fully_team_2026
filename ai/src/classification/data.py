import os
from typing import Tuple

import cv2
import torch
from torch.utils.data import Dataset, DataLoader

from src.config import YOLO_DATASET_DIR, IMG_SIZE


class YoloClassificationDataset(Dataset):
    """
    Binary classification dataset built on top of the YOLO dataset.
    Label = 1 if the corresponding YOLO label file has at least one box, else 0.
    """

    def __init__(self, split: str = "train"):
        self.split = split
        self.img_dir = os.path.join(YOLO_DATASET_DIR, split, "images")
        self.label_dir = os.path.join(YOLO_DATASET_DIR, split, "labels")

        self.image_files = [
            f for f in os.listdir(self.img_dir) if f.endswith(".png")
        ]
        self.image_files.sort()

    def __len__(self) -> int:
        return len(self.image_files)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        img_file = self.image_files[idx]
        img_path = os.path.join(self.img_dir, img_file)
        label_path = os.path.join(self.label_dir, img_file.replace(".png", ".txt"))

        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise RuntimeError(f"Failed to read image {img_path}")

        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))

        img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0

        label = 0
        if os.path.exists(label_path):
            with open(label_path) as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            if lines:
                label = 1

        label_tensor = torch.tensor(label, dtype=torch.long)
        return img_tensor, label_tensor


def create_classification_dataloaders(
    batch_size: int = 16, num_workers: int = 2
) -> Tuple[DataLoader, DataLoader]:
    train_dataset = YoloClassificationDataset(split="train")
    val_dataset = YoloClassificationDataset(split="val")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )

    return train_loader, val_loader

