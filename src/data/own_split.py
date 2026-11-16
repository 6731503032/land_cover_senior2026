"""Own (Mae Suai) images: rotating K-fold test sets, then a fraction of each fold's training pool."""
import json
from src.data.pairing import shuffle_pairs


def make_own_split(own_pairs, seed, test_fraction=0.2, save_to=None):
    """(old single split, kept for reference)"""
    shuffled = shuffle_pairs(own_pairs, seed)
    n_test = max(1, round(test_fraction * len(shuffled)))
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


def make_own_folds(own_pairs, k=5, seed=42, save_to=None):
    """Rotating test set: split all images into k chunks; each chunk is the test set once.
    Returns [(pool, test), ...]. Pool keeps the shuffled order, so take_fraction()
    gives 25% ⊂ 50% ⊂ 75% ⊂ 100% inside every fold."""
    shuffled = shuffle_pairs(own_pairs, seed)       # shuffle once
    n = len(shuffled)
    assert 2 <= k <= n, "k must be between 2 and the number of images"

    sizes = [n // k + (1 if i < n % k else 0) for i in range(k)]   # 44, k=5 -> 9,9,9,9,8
    folds, start = [], 0
    for size in sizes:
        test = shuffled[start:start + size]
        pool = shuffled[:start] + shuffled[start + size:]
        folds.append((pool, test))
        start += size

    if save_to is not None:
        json.dump([{"fold": i,
                    "test": [a.stem for a, _ in test],
                    "pool_order": [a.stem for a, _ in pool]}
                   for i, (pool, test) in enumerate(folds)],
                  open(save_to, "w"), indent=2)
    return folds