"""Train a model. Usage: python -m src.train configs/train_oem.yaml"""
import sys
from pathlib import Path

import torch
import yaml
from torch.utils.data import DataLoader

from src.data.classes import IGNORE_INDEX
from src.data.dataset import SegDataset
from src.models.build import build_model


def main(config_path):
    cfg = yaml.safe_load(open(config_path))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_model(cfg).to(device)
    if cfg.get("pretrained_checkpoint"):
        model.load_state_dict(torch.load(cfg["pretrained_checkpoint"], map_location=device), strict=False)

    loader = DataLoader(SegDataset(cfg["data_dir"], "train", cfg["crop_size"]),
                        batch_size=cfg["batch_size"], shuffle=True, num_workers=2)
    loss_fn = torch.nn.CrossEntropyLoss(ignore_index=IGNORE_INDEX)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"])

    for epoch in range(cfg["epochs"]):
        model.train()
        total = 0.0
        for img, mask in loader:
            img, mask = img.to(device), mask.to(device)
            loss = loss_fn(model(img), mask)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item()
        print(f"epoch {epoch + 1}/{cfg['epochs']}  loss {total / max(len(loader), 1):.4f}")

    Path("checkpoints").mkdir(exist_ok=True)
    torch.save(model.state_dict(), f"checkpoints/{cfg['name']}.pth")


if __name__ == "__main__":
    main(sys.argv[1])
