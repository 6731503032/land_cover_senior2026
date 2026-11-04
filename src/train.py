"""Training loop: train, check on val images, keep the best model."""
import json
import random
from pathlib import Path

import numpy as np
import segmentation_models_pytorch as smp
import torch
import torch.nn as nn
import yaml

from src.data.classes import CLASS_NAMES
from src.data.dataset import IGNORE, build_loaders
from src.evaluate import evaluate
from src.models.build import build_model


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def train(cfg, run_name="water_tree_unet_resnet34"):
    t = cfg["train"]
    set_seed(t["seed"])
    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_amp = device == "cuda"
    print("Device:", device)

    train_loader, val_loaders, val_sets = build_loaders(cfg)
    model = build_model(cfg).to(device)

    ce = nn.CrossEntropyLoss(ignore_index=IGNORE)                 # unlabeled pixels (255) are skipped
    dice = smp.losses.DiceLoss("multiclass", ignore_index=IGNORE)
    optimizer = torch.optim.Adam(model.parameters(), lr=t["learning_rate"])
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    weights_dir = Path(cfg["paths"]["weights_dir"])
    results_dir = Path(cfg["paths"]["results_dir"])
    weights_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    best_path = weights_dir / f"{run_name}_best.pth"

    # The best model is chosen using OUR images (the real target), if we have them.
    key = "own" if "own" in val_loaders else list(val_loaders)[0]
    best_miou, history = -1.0, []

    for epoch in range(1, t["epochs"] + 1):
        model.train()
        total = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            with torch.amp.autocast("cuda", enabled=use_amp):
                out = model(x)
                loss = ce(out, y) + dice(out, y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total += loss.item()
        train_loss = total / len(train_loader)

        row = {"epoch": epoch, "train_loss": train_loss}
        for name, loader in val_loaders.items():
            row[f"val_miou_{name}"] = evaluate(model, loader, device, len(CLASS_NAMES))["miou"]
        history.append(row)

        msg = " | ".join(f"{k} {v:.3f}" if k != "epoch" else f"epoch {v}" for k, v in row.items())
        if row[f"val_miou_{key}"] > best_miou:
            best_miou = row[f"val_miou_{key}"]
            torch.save(model.state_dict(), best_path)
            msg += "  <- best, saved"
        print(msg)

    with open(results_dir / f"{run_name}_history.json", "w") as f:
        json.dump(history, f, indent=2)

    model.load_state_dict(torch.load(best_path, map_location=device))   # go back to best epoch
    print(f"\nBest val mIoU ({key}): {best_miou:.3f}   saved to {best_path}")
    return model, history, val_loaders, val_sets, device
