import numpy as np
import torch

IGNORE = 255


@torch.no_grad()
def confusion_matrix(model, loader, n_classes, device):
    """rows = true class, columns = predicted class (ignored pixels skipped)"""
    model.eval()
    cm = np.zeros((n_classes, n_classes), np.int64)
    for x, y in loader:
        pred = model(x.to(device)).argmax(1).cpu().numpy().ravel()
        true = y.numpy().ravel()
        keep = true != IGNORE
        cm += np.bincount(true[keep] * n_classes + pred[keep],
                          minlength=n_classes ** 2).reshape(n_classes, n_classes)
    return cm
