"""Fixed 80/20 split of our own (Mae Suai) images, then a fraction of the 80%."""
import json
from src.data.pairing import shuffle_pairs


def make_own_split(own_pairs, seed, test_fraction=0.2, save_to=None):
    """Shuffle once, then cut into a fixed test set (20%) and a training pool (80%)."""
    shuffled = shuffle_pairs(own_pairs, seed)
    n_test = max(1, round(test_fraction * len(shuffled)))   # at least 1 test image
    own_test = shuffled[:n_test]
    own_pool = shuffled[n_test:]

    if save_to is not None:
        json.dump({"test": [a.stem for a, _ in own_test],
                   "pool_order": [a.stem for a, _ in own_pool]},
                  open(save_to, "w"), indent=2)
    return own_pool, own_test


def take_fraction(own_pool, fraction):
    """First `fraction` of the pool (0.25 images are always inside the 0.5 images)."""
    k = round(fraction * len(own_pool))
    return own_pool[:k]