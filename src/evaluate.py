"""Accuracy metrics: confusion matrix, per-class IoU, mIoU."""
import numpy as np


def confusion_matrix(truth, pred, num_classes, ignore_index=255):
    """Rows = true class, columns = predicted class."""
    keep = truth != ignore_index
    idx = truth[keep].astype(int) * num_classes + pred[keep].astype(int)
    return np.bincount(idx, minlength=num_classes ** 2).reshape(num_classes, num_classes)


def iou_per_class(cm):
    """IoU = TP / (TP + FP + FN) for each class."""
    tp = np.diag(cm).astype(float)
    denom = cm.sum(0) + cm.sum(1) - np.diag(cm)
    return np.divide(tp, denom, out=np.full_like(tp, np.nan), where=denom > 0)


def miou(cm):
    return float(np.nanmean(iou_per_class(cm)))
