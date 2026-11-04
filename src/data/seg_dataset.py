"""Dataset, mask remapping and padding. Works for any number of classes (set in the yaml)."""
import random
import numpy as np
import rasterio
import torch
from torch.utils.data import Dataset

IGNORE = 255
MEAN = np.array([0.485, 0.456, 0.406], np.float32).reshape(3, 1, 1)
STD = np.array([0.229, 0.224, 0.225], np.float32).reshape(3, 1, 1)


def get_oem_ids(cfg, oem_pairs):
    """OEM mask numbers. With auto: true, look at the label files to pick the numbering."""
    m = cfg["mask_ids"]["oem"]
    if not m.get("auto", False):
        return m, None
    seen = set()
    for _, mp in oem_pairs[:100]:
        with rasterio.open(mp) as s:
            seen |= set(np.unique(s.read(1)).tolist())
    if 8 in seen:     # original OEM numbering
        return {"tree": [5], "water": [6], "ignore": [0]}, seen
    return {"tree": [4], "water": [5], "ignore": [0]}, seen   # old 7-class numbering


def remap_mask(mask, ids, classes):
    """classes[0] = everything not listed. classes[i] = raw values in ids[classes[i]]. ids['ignore'] -> IGNORE."""
    out = np.zeros(mask.shape, np.uint8)
    for idx, name in enumerate(classes):
        if idx == 0:
            continue
        out[np.isin(mask, ids.get(name, []))] = idx
    out[np.isin(mask, ids.get("ignore", []))] = IGNORE
    return out


def pad_to(img, mask, th, tw):
    c, h, w = img.shape
    if h < th or w < tw:
        ph, pw = max(th, h) - h, max(tw, w) - w
        img = np.pad(img, ((0, 0), (0, ph), (0, pw)))
        mask = np.pad(mask, ((0, ph), (0, pw)), constant_values=IGNORE)
    return img, mask


class SegDataset(Dataset):
    def __init__(self, pairs, ids, classes, image_max, crop, train, repeat=1):
        self.items = list(pairs) * repeat
        self.ids, self.classes = ids, list(classes)
        self.image_max, self.crop, self.train = float(image_max), crop, train

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        ip, mp = self.items[i]
        with rasterio.open(ip) as s:
            img = s.read([1, 2, 3]).astype(np.float32)        # R, G, B
        with rasterio.open(mp) as s:
            mask = remap_mask(s.read(1), self.ids, self.classes)
        img = np.clip(img / self.image_max, 0, 1)
        if self.train:
            crop = self.crop
            img, mask = pad_to(img, mask, crop, crop)
            _, h, w = img.shape
            y, x = random.randint(0, h - crop), random.randint(0, w - crop)
            img, mask = img[:, y:y+crop, x:x+crop], mask[y:y+crop, x:x+crop]
            if random.random() < 0.5: img, mask = img[:, :, ::-1], mask[:, ::-1]
            if random.random() < 0.5: img, mask = img[:, ::-1, :], mask[::-1, :]
            k = random.randint(0, 3)
            img, mask = np.rot90(img, k, (1, 2)), np.rot90(mask, k)
        else:   # test: whole image, padded so the size fits the network (multiple of 32)
            _, h, w = img.shape
            img, mask = pad_to(img, mask, -(-h // 32) * 32, -(-w // 32) * 32)
        img = (img - MEAN) / STD
        return (torch.from_numpy(np.ascontiguousarray(img)),
                torch.from_numpy(np.ascontiguousarray(mask).astype(np.int64)))
