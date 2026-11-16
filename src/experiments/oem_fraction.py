"""One run of the 'how much Mae Suai data do we need' experiment, plus the K-fold wrapper."""
import json
import time
from pathlib import Path

import numpy as np
from torch.utils.data import DataLoader, ConcatDataset

from src.data.own_split import take_fraction, make_own_folds
from src.data.seg_dataset import SegDataset
from src.training.train_one import set_seed, train_one_model


def run_fraction(fraction, cfg, device, oem_pairs, own_pool, own_test, oem_ids, own_ids,
                 weights_dir, fold=None):
    set_seed(cfg["train"]["seed"])
    classes = cfg["classes"]
    crop = cfg["data"]["crop_size"]
    repeat = cfg["data"]["own_repeat"]
    img_max = cfg["image_max"]

    model_name = cfg["model"]["active"]
    model_spec = cfg["models"][model_name]
    encoder = model_spec.get("encoder", "unknown")
    decoder = model_spec.get("decoder", "unknown")

    pct = int(fraction * 100)

    own_train = take_fraction(own_pool, fraction)   # first part of this fold's shuffled training pool
    k = len(own_train)

    test_loader = DataLoader(SegDataset(own_test, own_ids, classes, img_max["own"], crop, train=False),
                             batch_size=1, shuffle=False, num_workers=0)
    parts = [SegDataset(oem_pairs, oem_ids, classes, img_max["oem"], crop, train=True)]
    if k > 0:
        parts.append(SegDataset(own_train, own_ids, classes, img_max["own"], crop, train=True, repeat=repeat))
    train_dataset = ConcatDataset(parts)

    n_oem = len(oem_pairs)
    fold_txt = f" | fold {fold}" if fold is not None else ""
    print(f"\n=== {model_name} (Encoder: {encoder} | Decoder: {decoder}) | {pct}%{fold_txt} ===")
    print(f"Images trained on: {n_oem} OEM + {k} Mae Suai = {n_oem + k} unique images")
    print(f"Samples per epoch (Mae Suai x{repeat} repeat): {len(train_dataset)}")
    print(f"Test on {len(own_test)} held-out Mae Suai images")

    # Measure training time
    start_time = time.time()

    res = train_one_model(cfg, train_dataset, test_loader, device,
                          weights_path=weights_dir / f"{model_name}_fraction_{pct}_last.pth")

    elapsed_seconds = time.time() - start_time
    elapsed_minutes = elapsed_seconds / 60.0
    print(f"Training completed in {elapsed_minutes:.2f} minutes ({elapsed_seconds:.1f}s)")

    res.update({
        "model": model_name,
        "encoder": encoder,
        "decoder": decoder,
        "fraction": fraction,
        "fold": fold,
        "n_own_train": k,
        "n_test": len(own_test),
        "test_is_seen": False,
        "train_time_sec": round(elapsed_seconds, 2),
        "train_time_min": round(elapsed_minutes, 2)
    })

    return res


def run_kfold(fractions, cfg, device, oem_pairs, own_pairs, oem_ids, own_ids,
              weights_dir, results_dir, model_name, k=5, seed=42):
    """Rotate the test set: each of the K folds is the unseen test set once.
    Returns {fold_index: [result for each fraction]}."""
    weights_dir, results_dir = Path(weights_dir), Path(results_dir)
    folds = make_own_folds(own_pairs, k, seed, save_to=results_dir / "own_folds.json")
    all_results = {}

    for i, (pool, test) in enumerate(folds):
        print(f"\n##### FOLD {i + 1}/{k} | pool {len(pool)} | test {len(test)} #####")
        wdir = weights_dir / f"fold{i}"          # separate folder so weights don't overwrite
        wdir.mkdir(parents=True, exist_ok=True)

        all_results[i] = [
            run_fraction(f, cfg, device, oem_pairs, pool, test, oem_ids, own_ids, wdir, fold=i)
            for f in fractions
        ]
        # save after every fold so a crash doesn't lose finished folds
        with open(results_dir / f"own_fraction_{model_name}_kfold_results.json", "w") as fh:
            json.dump(all_results, fh, indent=2)

    return all_results


def summarize_kfold(all_results, fractions, key="miou"):
    """Mean ± std of one metric across folds, per fraction."""
    rows = []
    for idx, f in enumerate(fractions):
        scores = [all_results[k][idx][key] for k in all_results]
        rows.append({"fraction": f, "mean": float(np.mean(scores)),
                     "std": float(np.std(scores)), "folds": scores})
    return rows