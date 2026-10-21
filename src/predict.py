"""Sliding-window prediction: cuts a big image into overlapping tiles,
predicts each one, and stitches the result back together."""
import numpy as np
import torch


@torch.no_grad()
def predict_large(model, image, tile=512, overlap=64, device="cpu"):
    """image: float tensor (3, H, W) in 0-1. Returns class-id array (H, W)."""
    model.eval()
    _, h, w = image.shape
    n_classes = None
    step = tile - overlap
    scores = None
    counts = np.zeros((h, w), dtype=np.float32)
    for y in range(0, max(h - overlap, 1), step):
        for x in range(0, max(w - overlap, 1), step):
            y2, x2 = min(y + tile, h), min(x + tile, w)
            y1, x1 = max(y2 - tile, 0), max(x2 - tile, 0)
            out = model(image[:, y1:y2, x1:x2].unsqueeze(0).to(device))[0].softmax(0).cpu().numpy()
            if scores is None:
                n_classes = out.shape[0]
                scores = np.zeros((n_classes, h, w), dtype=np.float32)
            scores[:, y1:y2, x1:x2] += out
            counts[y1:y2, x1:x2] += 1
    return (scores / np.maximum(counts, 1)).argmax(0)
