"""Tables and plots for the fraction experiment. Class names come from the yaml."""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def lab(r):
    return f"{int(r['fraction']*100)}%" + (" (seen)" if r["test_is_seen"] else "")


def print_table(results, classes):
    print(f"{'Mae Suai in training':22s} {'test imgs':>9s} {'mIoU':>6s}  " + "  ".join(f"{c:>6s}" for c in classes))
    for r in results:
        label = f"{int(r['fraction']*100):3d}% ({r['n_own_train']} imgs)"
        print(f"{label:22s} {r['n_test']:9d} {r['miou']:6.3f}  " + "  ".join(f"{v:6.3f}" for v in r["iou"]))


def plot_miou(results, save_to=None):
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
    ax[0].bar([lab(r) for r in results], [r["miou"] for r in results])
    ax[0].set_title("Test mIoU vs share of Mae Suai in training"); ax[0].set_ylim(0, 1)
    for r in results:
        ax[1].plot(range(1, len(r["curve"]) + 1), r["curve"], label=lab(r))
    ax[1].set_title("Test mIoU per epoch"); ax[1].set_xlabel("epoch"); ax[1].legend()
    plt.tight_layout()
    if save_to: plt.savefig(save_to, dpi=120)
    plt.show()


def plot_confusions(results, classes, save_to=None):
    """One heatmap per option, % of each true class. Wraps into a grid so 8 classes stay readable."""
    n, nc = len(results), len(classes)
    ncols = min(n, 4 if nc <= 3 else 2)
    nrows = -(-n // ncols)
    size = 4.2 if nc <= 3 else 6.5
    fig, axes = plt.subplots(nrows, ncols, figsize=(size * ncols, size * nrows), squeeze=False)
    for ax in axes.ravel():
        ax.axis("off")
    for ax, r in zip(axes.ravel(), results):
        ax.axis("on")
        cm = np.array(r["confusion"], dtype=np.float64)
        pct = cm / np.maximum(cm.sum(1, keepdims=True), 1) * 100
        sns.heatmap(pct, annot=True, fmt=".1f", cmap="Blues", vmin=0, vmax=100, cbar=False,
                    xticklabels=classes, yticklabels=classes, ax=ax, annot_kws={"size": 9 if nc > 3 else 11})
        ax.set_title(f"{lab(r)} | mIoU {r['miou']:.3f}")
        ax.set_xlabel("predicted"); ax.set_ylabel("true")
    plt.suptitle("Confusion matrices (% of each true class)")
    plt.tight_layout()
    if save_to: plt.savefig(save_to, dpi=120, bbox_inches="tight")
    plt.show()


def plot_iou_heatmap(results, classes, save_to=None):
    table = np.array([r["iou"] + [r["miou"]] for r in results])
    plt.figure(figsize=(1.2 * (len(classes) + 1) + 3, 0.8 * len(results) + 2))
    sns.heatmap(table, annot=True, fmt=".3f", cmap="viridis", vmin=0, vmax=1,
                xticklabels=list(classes) + ["mIoU"], yticklabels=[lab(r) for r in results])
    plt.title("IoU per class and mIoU (higher = better)")
    plt.ylabel("Mae Suai in training")
    plt.tight_layout()
    if save_to: plt.savefig(save_to, dpi=120)
    plt.show()
