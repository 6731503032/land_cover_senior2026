"""Train ONE model on a dataset and score it on a test loader (last epoch, no best-epoch picking)."""
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import segmentation_models_pytorch as smp

from src.models.build import build_model
from src.evaluate import evaluate
from src.evaluation.metrics import confusion_matrix

IGNORE = 255


def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)


def train_one_model(cfg, train_dataset, test_loader, device, weights_path=None):
    n_classes = len(cfg["classes"])
    train_loader = DataLoader(train_dataset, batch_size=cfg["train"]["batch_size"], shuffle=True,
                              num_workers=0, drop_last=True)   # 0 workers: safest on Windows + Jupyter

    model = build_model(cfg).to(device)
    ce = nn.CrossEntropyLoss(ignore_index=IGNORE)
    dice = smp.losses.DiceLoss("multiclass", ignore_index=IGNORE)
    opt = torch.optim.Adam(model.parameters(), lr=float(cfg["train"]["learning_rate"]))
    use_amp = device == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    curve = []
    for epoch in range(1, cfg["train"]["epochs"] + 1):
        model.train(); total = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            with torch.amp.autocast("cuda", enabled=use_amp):
                out = model(x)
                loss = ce(out, y) + dice(out, y)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
            total += loss.item()
        r = evaluate(model, test_loader, device, n_classes)
        curve.append(r["miou"])
        print(f"epoch {epoch:2d} | train_loss {total/len(train_loader):.3f} | test mIoU {r['miou']:.3f}")

    cm = confusion_matrix(model, test_loader, n_classes, device)
    if weights_path is not None:
        torch.save(model.state_dict(), weights_path)
    return {"miou": r["miou"], "iou": [float(v) for v in r["iou"]],
            "curve": [float(v) for v in curve], "confusion": cm.tolist()}
