"""mIoU, per-class IoU and a picture of predictions."""
import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.colors import ListedColormap

from src.data.classes import CLASS_COLORS, CLASS_NAMES
from src.data.dataset import IGNORE, MEAN, STD


def scores_from_cm(cm):
    """cm[true, predicted]. IoU = overlap / union for each class."""
    tp = np.diag(cm).astype(float)
    union = cm.sum(0) + cm.sum(1) - tp
    iou = np.where(union > 0, tp / np.maximum(union, 1), np.nan)
    return {"miou": float(np.nanmean(iou)), "iou": iou.tolist(), "cm": cm}


@torch.no_grad()
def evaluate(model, loader, device, num_classes=3):
    model.eval()
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for x, y in loader:
        pred = model(x.to(device)).argmax(1).cpu().numpy().ravel()
        true = y.numpy().ravel()
        keep = true != IGNORE                      # unlabeled pixels are not scored
        idx = true[keep] * num_classes + pred[keep]
        cm += np.bincount(idx, minlength=num_classes ** 2).reshape(num_classes, num_classes)
    return scores_from_cm(cm)


@torch.no_grad()
def show_predictions(model, dataset, device, n=4, save_path=None):
    """Show image | true mask | predicted mask."""
    model.eval()
    cmap = ListedColormap(CLASS_COLORS)
    n = min(n, len(dataset))
    fig, axes = plt.subplots(n, 3, figsize=(9, 3 * n), squeeze=False)
    for row in range(n):
        x, y = dataset[row]
        pred = model(x[None].to(device)).argmax(1)[0].cpu().numpy()
        rgb = np.clip(x.numpy() * STD + MEAN, 0, 1).transpose(1, 2, 0)
        true = np.ma.masked_equal(y.numpy(), IGNORE)   # unlabeled shown as blank, not as a class
        for ax, im, title in zip(axes[row], [rgb, true, pred],
                                 ["Image", "True mask", "Prediction"]):
            if title == "Image":
                ax.imshow(im)
            else:
                ax.imshow(im, cmap=cmap, vmin=0, vmax=len(CLASS_NAMES) - 1, interpolation="nearest")
            ax.set_title(title)
            ax.axis("off")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120)
    plt.show()
