import os
import random
from typing import List, Tuple, Dict

import cv2
import torch
from torch.utils.data import Dataset, DataLoader

from src.config import YOLO_DATASET_DIR, IMG_SIZE, SEED


class YoloDetectionDataset(Dataset):
    def __init__(self, split: str = "train", fraction: float = 1.0):
        self.split = split
        self.is_train = split == "train"
        self.img_dir = os.path.join(YOLO_DATASET_DIR, split, "images")
        self.label_dir = os.path.join(YOLO_DATASET_DIR, split, "labels")

        self.image_files = [
            f for f in os.listdir(self.img_dir) if f.endswith(".png")
        ]
        self.image_files.sort()

        # Deterministic subsample for fast training on part of the data
        # (e.g. the Phase-4 proxy search).
        if 0.0 < fraction < 1.0 and self.image_files:
            keep = max(1, int(len(self.image_files) * fraction))
            rng = random.Random(SEED)
            self.image_files = sorted(rng.sample(self.image_files, keep))

    def __len__(self) -> int:
        return len(self.image_files)

    def _load_labels(self, label_path: str, w: int, h: int) -> Tuple[torch.Tensor, torch.Tensor]:
        if not os.path.exists(label_path):
            return torch.zeros((0, 4), dtype=torch.float32), torch.zeros((0,), dtype=torch.int64)

        with open(label_path) as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        boxes: List[List[float]] = []
        labels: List[int] = []

        for line in lines:
            parts = line.split()
            if len(parts) != 5:
                continue
            cls, x_c, y_c, bw, bh = map(float, parts)

            x_center = x_c * w
            y_center = y_c * h
            box_w = bw * w
            box_h = bh * h

            x1 = x_center - box_w / 2.0
            y1 = y_center - box_h / 2.0
            x2 = x_center + box_w / 2.0
            y2 = y_center + box_h / 2.0

            x1 = max(0.0, min(x1, w - 1.0))
            x2 = max(0.0, min(x2, w - 1.0))
            y1 = max(0.0, min(y1, h - 1.0))
            y2 = max(0.0, min(y2, h - 1.0))

            if x2 <= x1 or y2 <= y1:
                continue

            boxes.append([x1, y1, x2, y2])
            labels.append(int(cls) + 1)  # 0 reserved for background

        if not boxes:
            return torch.zeros((0, 4), dtype=torch.float32), torch.zeros((0,), dtype=torch.int64)

        boxes_tensor = torch.tensor(boxes, dtype=torch.float32)
        labels_tensor = torch.tensor(labels, dtype=torch.int64)
        return boxes_tensor, labels_tensor

    def _augment(self, img_tensor: torch.Tensor, boxes: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # Box-aware horizontal flip
        if random.random() < 0.5:
            img_tensor = torch.flip(img_tensor, dims=[2])  # flip width
            if boxes.numel() > 0:
                w = img_tensor.shape[2]
                x1 = boxes[:, 0].clone()
                x2 = boxes[:, 2].clone()
                boxes[:, 0] = w - x2
                boxes[:, 2] = w - x1
        # Photometric jitter (does not affect boxes)
        contrast = random.uniform(0.85, 1.15)
        brightness = random.uniform(-0.1, 0.1)
        img_tensor = (img_tensor * contrast + brightness).clamp(0.0, 1.0)
        return img_tensor, boxes

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        img_file = self.image_files[idx]
        img_path = os.path.join(self.img_dir, img_file)
        label_path = os.path.join(self.label_dir, img_file.replace(".png", ".txt"))

        img = cv2.imread(img_path)
        if img is None:
            raise RuntimeError(f"Failed to read image {img_path}")

        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))

        img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0

        boxes, labels = self._load_labels(label_path, IMG_SIZE, IMG_SIZE)

        if self.is_train:
            img_tensor, boxes = self._augment(img_tensor, boxes)

        target: Dict[str, torch.Tensor] = {
            "boxes": boxes,
            "labels": labels,
            "image_id": torch.tensor([idx], dtype=torch.int64),
        }

        if boxes.numel() > 0:
            area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        else:
            area = torch.zeros((0,), dtype=torch.float32)

        target["area"] = area
        target["iscrowd"] = torch.zeros((boxes.shape[0],), dtype=torch.int64)

        return img_tensor, target


def _collate_fn(batch):
    images, targets = list(zip(*batch))
    return list(images), list(targets)


def _make_loader(split: str, batch_size: int, num_workers: int, fraction: float = 1.0) -> DataLoader:
    dataset = YoloDetectionDataset(split=split, fraction=fraction)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=(split == "train"),
        num_workers=num_workers,
        collate_fn=_collate_fn,
        pin_memory=torch.cuda.is_available(),
    )


def create_dataloaders(
    batch_size: int = 4, num_workers: int = 2, train_fraction: float = 1.0
) -> Tuple[DataLoader, DataLoader]:
    # Only the train split is subsampled; val stays full so evaluation is comparable.
    return (
        _make_loader("train", batch_size, num_workers, fraction=train_fraction),
        _make_loader("val", batch_size, num_workers),
    )


def create_detection_test_loader(batch_size: int = 4, num_workers: int = 2) -> DataLoader:
    return _make_loader("test", batch_size, num_workers)
