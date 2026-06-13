import os
from typing import Tuple

import cv2
import torch
import torchvision.transforms as T
from torch.utils.data import Dataset, DataLoader

from src.config import YOLO_DATASET_DIR, CLS_IMG_SIZE, IMAGENET_MEAN, IMAGENET_STD


# Train-only, class-agnostic augmentation applied on-the-fly (different every epoch).
# This is real augmentation - unlike the old build-time, class-conditional transform
# that leaked the label. Val/test get normalization only.
_TRAIN_TRANSFORM = T.Compose(
    [
        T.RandomHorizontalFlip(p=0.5),
        T.RandomRotation(degrees=10),
        T.ColorJitter(brightness=0.15, contrast=0.15),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
)
_EVAL_TRANSFORM = T.Compose([T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)])


class YoloClassificationDataset(Dataset):
    """
    Binary classification dataset built on top of the YOLO dataset.
    Label = 1 if the corresponding YOLO label file has at least one box, else 0.
    """

    def __init__(self, split: str = "train"):
        self.split = split
        self.is_train = split == "train"
        self.transform = _TRAIN_TRANSFORM if self.is_train else _EVAL_TRANSFORM
        self.img_dir = os.path.join(YOLO_DATASET_DIR, split, "images")
        self.label_dir = os.path.join(YOLO_DATASET_DIR, split, "labels")

        self.image_files = [
            f for f in os.listdir(self.img_dir) if f.endswith(".png")
        ]
        self.image_files.sort()

    def __len__(self) -> int:
        return len(self.image_files)

    def get_label(self, idx: int) -> int:
        img_file = self.image_files[idx]
        label_path = os.path.join(self.label_dir, img_file.replace(".png", ".txt"))
        if os.path.exists(label_path):
            with open(label_path) as f:
                if any(line.strip() for line in f):
                    return 1
        return 0

    def get_labels(self):
        return [self.get_label(i) for i in range(len(self))]

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        img_file = self.image_files[idx]
        img_path = os.path.join(self.img_dir, img_file)

        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise RuntimeError(f"Failed to read image {img_path}")

        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        img = cv2.resize(img, (CLS_IMG_SIZE, CLS_IMG_SIZE))

        img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
        img_tensor = self.transform(img_tensor)

        label = self.get_label(idx)
        label_tensor = torch.tensor(label, dtype=torch.long)
        return img_tensor, label_tensor


def _make_loader(split: str, batch_size: int, num_workers: int) -> DataLoader:
    dataset = YoloClassificationDataset(split=split)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=(split == "train"),
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )


def create_classification_dataloaders(
    batch_size: int = 32, num_workers: int = 2
) -> Tuple[DataLoader, DataLoader]:
    return (
        _make_loader("train", batch_size, num_workers),
        _make_loader("val", batch_size, num_workers),
    )


def create_classification_test_loader(
    batch_size: int = 32, num_workers: int = 2
) -> DataLoader:
    return _make_loader("test", batch_size, num_workers)
