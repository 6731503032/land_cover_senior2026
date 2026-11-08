#Handles finding, matching, and pairing matching image and mask file paths across OpenEarthMap and Mae Suai regions, 
# and manages dataset splitting via split_for 

"""Match images with masks by file name, and split Mae Suai into seen / unseen."""
import random
from pathlib import Path

EXTS = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}


def pair_folder(img_dir, mask_dir):
    """[(image_path, mask_path), ...] for files with the same name (without extension)."""
    masks = {p.stem: p for p in Path(mask_dir).iterdir() if p.suffix.lower() in EXTS}
    return [(p, masks[p.stem]) for p in sorted(Path(img_dir).iterdir())
            if p.suffix.lower() in EXTS and p.stem in masks]


def pair_images_and_labels(root_dir):
    """
    Scans a dataset root directory where images and labels 
    are kept in separate subfolders per region (OpenEarthMap structure).
    Expected structure:
        root_dir / <region_name> / images / *.tif
        root_dir / <region_name> / labels / *.tif (or masks)
    """
    root_path = Path(root_dir)
    paired_list = []

    if not root_path.exists():
        print(f"Warning: OEM root directory not found at {root_path}")
        return paired_list

    # Loop through each region folder (Colorado, Kumamoto, etc.)
    for region_dir in sorted(root_path.iterdir()):
        if region_dir.is_dir():
            img_dir = region_dir / "images"
            label_dir = region_dir / "labels"
            
            # Fallback to 'masks' if 'labels' doesn't exist
            if not label_dir.exists():
                label_dir = region_dir / "masks"

            if img_dir.exists() and label_dir.exists():
                # Efficient dictionary mapping for filename stem matching
                masks = {p.stem: p for p in Path(label_dir).iterdir() if p.suffix.lower() in EXTS}
                region_pairs = [(p, masks[p.stem]) for p in sorted(Path(img_dir).iterdir())
                                if p.suffix.lower() in EXTS and p.stem in masks]
                paired_list.extend(region_pairs)

    print(f"Successfully paired {len(paired_list)} images with their matching labels across all OEM regions.")
    return paired_list


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