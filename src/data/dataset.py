"""Loads image + mask pairs and cuts random crops for training."""
import random
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset


class SegDataset(Dataset):
    """Expects <data_dir>/<split>/images/*.png and <data_dir>/<split>/masks/*.png
    with the same file names. Masks store one class id per pixel."""

    def __init__(self, data_dir, split="train", crop_size=512):
        root = Path(data_dir) / split
        self.images = sorted((root / "images").glob("*.png"))
        self.masks_dir = root / "masks"
        self.crop = crop_size
        self.train = split == "train"

    def __len__(self):
        return len(self.images)

    def __getitem__(self, i):
        img_path = self.images[i]
        img = np.array(Image.open(img_path).convert("RGB"))
        mask = np.array(Image.open(self.masks_dir / img_path.name))
        h, w = mask.shape
        c = min(self.crop, h, w)
        y = random.randint(0, h - c) if self.train else 0
        x = random.randint(0, w - c) if self.train else 0
        img, mask = img[y:y + c, x:x + c], mask[y:y + c, x:x + c]
        img = torch.from_numpy(img.transpose(2, 0, 1)).float() / 255.0
        return img, torch.from_numpy(mask).long()
