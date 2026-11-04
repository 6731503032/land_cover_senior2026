"""Match images with masks by file name, and split Mae Suai into seen / unseen."""
import random
from pathlib import Path

EXTS = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}


def pair_folder(img_dir, mask_dir):
    """[(image_path, mask_path), ...] for files with the same name (without extension)."""
    masks = {p.stem: p for p in Path(mask_dir).iterdir() if p.suffix.lower() in EXTS}
    return [(p, masks[p.stem]) for p in sorted(Path(img_dir).iterdir())
            if p.suffix.lower() in EXTS and p.stem in masks]


def shuffle_pairs(pairs, seed):
    """Shuffle once. Because the order is fixed, 25% is always inside 50%, inside 100%."""
    out = list(pairs)
    random.Random(seed).shuffle(out)
    return out


def split_for(shuffled, fraction):
    """First `fraction` = seen (train). The rest = unseen (test).
    At 100% nothing is unseen, so the test set is the seen images (fit only, not generalization)."""
    k = round(fraction * len(shuffled))
    seen, unseen = shuffled[:k], shuffled[k:]
    if len(unseen) == 0:
        unseen = list(seen)
    return seen, unseen
