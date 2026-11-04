"""Load image + mask chips, turn masks into 0/1/2 (+255 = ignore), crop and flip."""
import random
from pathlib import Path

import numpy as np
import rasterio
import torch
from torch.utils.data import DataLoader, Dataset

# Standard numbers that pre-trained ResNet expects
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)[:, None, None]
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)[:, None, None]


IGNORE = 255   # pixels with this value are skipped by the loss and the metrics


def make_lookup(tree_ids, water_ids, ignore_ids=()):
    """Table: old mask value -> new value (0 other, 1 tree, 2 water, 255 ignore)."""
    lut = np.zeros(256, dtype=np.int64)
    for i in tree_ids:
        lut[i] = 1
    for i in water_ids:
        lut[i] = 2
    for i in ignore_ids:
        lut[i] = IGNORE
    return lut


def detect_oem_numbering(mask_paths, n=60, seed=0):
    """Original OEM labels use 1-8 (tree 5, water 6). The old 7-class remap has no 8 (tree 4, water 5)."""
    vals = set()
    for p in random.Random(seed).sample(list(mask_paths), min(n, len(mask_paths))):
        with rasterio.open(p) as src:
            vals |= set(np.unique(src.read(1)).tolist())
    if 8 in vals:
        return {"tree": [5], "water": [6], "ignore": [0]}
    print("  OEM labels have no value 8 -> old 7-class remap (tree 4, water 5)")
    return {"tree": [4], "water": [5], "ignore": [0]}


def find_pairs(image_dir, mask_dir):
    """Match images and masks by file name."""
    pairs = []
    for img in sorted(Path(image_dir).glob("*.tif")):
        mask = Path(mask_dir) / img.name
        if mask.exists():
            pairs.append((str(img), str(mask)))
        else:
            print("No mask for", img.name, "- skipped")
    return pairs


def split_pairs(pairs, val_fraction, seed):
    """Random train/val split (same seed = same split every time)."""
    pairs = list(pairs)
    random.Random(seed).shuffle(pairs)
    n_val = max(1, int(len(pairs) * val_fraction)) if pairs else 0
    return pairs[n_val:], pairs[:n_val]


class SegDataset(Dataset):
    def __init__(self, pairs, lut, crop_size=256, image_max=255, train=True, repeat=1):
        self.pairs = pairs
        self.lut = lut
        self.crop = crop_size
        self.image_max = image_max
        self.train = train
        self.repeat = repeat

    def __len__(self):
        return len(self.pairs) * self.repeat

    def __getitem__(self, idx):
        img_path, mask_path = self.pairs[idx % len(self.pairs)]

        with rasterio.open(img_path) as src:
            image = src.read([1, 2, 3]).astype(np.float32)   # first 3 bands = R,G,B
        with rasterio.open(mask_path) as src:
            mask = src.read(1)

        image = np.clip(image / self.image_max, 0, 1)
        mask = self.lut[np.clip(mask, 0, 255).astype(np.int64)]

        image, mask = self._pad(image, mask)
        image, mask = self._crop(image, mask)
        if self.train:
            image, mask = self._augment(image, mask)

        image = (image - MEAN) / STD
        return torch.from_numpy(image.copy()), torch.from_numpy(mask.copy()).long()

    def _pad(self, image, mask):
        _, h, w = image.shape
        ph, pw = max(0, self.crop - h), max(0, self.crop - w)
        if ph or pw:
            image = np.pad(image, ((0, 0), (0, ph), (0, pw)))
            mask = np.pad(mask, ((0, ph), (0, pw)), constant_values=IGNORE)
        return image, mask

    def _crop(self, image, mask):
        _, h, w = image.shape
        c = self.crop
        if self.train:   # random crop (OEM images are big, ours are already 256)
            top, left = random.randint(0, h - c), random.randint(0, w - c)
        else:            # centre crop so validation is always the same
            top, left = (h - c) // 2, (w - c) // 2
        return image[:, top:top + c, left:left + c], mask[top:top + c, left:left + c]

    def _augment(self, image, mask):
        if random.random() < 0.5:
            image, mask = image[:, :, ::-1], mask[:, ::-1]
        if random.random() < 0.5:
            image, mask = image[:, ::-1, :], mask[::-1, :]
        k = random.randint(0, 3)
        return np.rot90(image, k, axes=(1, 2)), np.rot90(mask, k, axes=(0, 1))


def build_loaders(cfg):
    """Returns: train_loader, {"own": val_loader, "oem": val_loader}, {"own": ds, ...}"""
    p, d, t = cfg["paths"], cfg["data"], cfg["train"]
    root = Path(p["data_root"])
    train_sets, val_sets = [], {}

    for name, img_key, mask_key in [("own", "own_images", "own_masks"),
                                    ("oem", "oem_images", "oem_masks")]:
        img_dir, mask_dir = root / p[img_key], root / p[mask_key]
        if not img_dir.exists():
            print(f"Folder not found, skipping {name}: {img_dir}")
            continue
        pairs = find_pairs(img_dir, mask_dir)
        tr, va = split_pairs(pairs, d["val_fraction"], t["seed"])
        ids = dict(cfg["mask_ids"][name])
        if ids.get("auto"):
            ids.update(detect_oem_numbering([m for _, m in pairs]))
        print(f"{name}: tree={ids['tree']} water={ids['water']} ignore={ids.get('ignore', [])}")
        lut = make_lookup(ids["tree"], ids["water"], ids.get("ignore", []))
        repeat = d["own_repeat"] if name == "own" else 1
        print(f"{name}: {len(tr)} train, {len(va)} val")
        train_sets.append(SegDataset(tr, lut, d["crop_size"], cfg["image_max"][name], True, repeat))
        val_sets[name] = SegDataset(va, lut, d["crop_size"], cfg["image_max"][name], False)

    train_ds = torch.utils.data.ConcatDataset(train_sets)
    train_loader = DataLoader(train_ds, batch_size=t["batch_size"], shuffle=True,
                              num_workers=d["num_workers"], drop_last=True)
    val_loaders = {k: DataLoader(v, batch_size=t["batch_size"], shuffle=False,
                                 num_workers=d["num_workers"]) for k, v in val_sets.items()}
    return train_loader, val_loaders, val_sets
