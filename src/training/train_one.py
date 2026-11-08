"""Train ONE model on a dataset with modular early stopping parameters."""
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import segmentation_models_pytorch as smp
from pathlib import Path

from src.models.build import build_model
from src.evaluate import evaluate
from src.evaluation.metrics import confusion_matrix

IGNORE = 255


def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)


def train_one_model(cfg, train_dataset, test_loader, device, weights_path=None):
    # ==========================================
    # MODULAR CONFIGURATION & HYPERPARAMETERS
    # ==========================================
    train_cfg = cfg.get("train", {})
    epochs = train_cfg.get("epochs", 30)
    lr = float(train_cfg.get("learning_rate", 0.0001))
    batch_size = train_cfg.get("batch_size", 8)
    
    # Early Stopping Controls (Easily adjustable here)
    TARGET_MIOU = 0.60
    PATIENCE = 7
    # ==========================================

    n_classes = len(cfg["classes"])
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True,
        num_workers=0, 
        drop_last=True
    )

    model = build_model(cfg).to(device)
    ce = nn.CrossEntropyLoss(ignore_index=IGNORE)
    dice = smp.losses.DiceLoss("multiclass", ignore_index=IGNORE)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    use_amp = device == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    curve = []
    best_miou = -1.0
    patience_counter = 0

    for epoch in range(1, epochs + 1):
        model.train()
        total = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            with torch.amp.autocast("cuda", enabled=use_amp):
                out = model(x)
                loss = ce(out, y) + dice(out, y)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            total += loss.item()
            
        r = evaluate(model, test_loader, device, n_classes)
        current_miou = r["miou"]
        curve.append(current_miou)
        print(f"epoch {epoch:2d} | train_loss {total/len(train_loader):.3f} | test mIoU {current_miou:.3f}")

        # 1. Target mIoU Check
        if current_miou >= TARGET_MIOU:
            print(f"Elite target mIoU {TARGET_MIOU} reached at epoch {epoch}! Stopping early.")
            best_miou = current_miou
            if weights_path is not None:
                torch.save(model.state_dict(), weights_path)
            break

        # 2. Best Checkpoint Tracking & Patience Early Stopping
        if current_miou > best_miou:
            best_miou = current_miou
            patience_counter = 0
            if weights_path is not None:
                torch.save(model.state_dict(), weights_path)
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"Early stopping triggered: mIoU did not improve for {PATIENCE} consecutive epochs.")
                break

    # Load the best saved weights before final confusion matrix evaluation
    if weights_path is not None and Path(weights_path).exists():
        model.load_state_dict(torch.load(weights_path))

    cm = confusion_matrix(model, test_loader, n_classes, device)
    
    return {
        "miou": best_miou if best_miou > 0 else current_miou, 
        "iou": [float(v) for v in r["iou"]],
        "curve": [float(v) for v in curve], 
        "confusion": cm.tolist()
    }