"""Tables and plots for the fraction experiment. Class names come from the yaml."""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import torch
import torch.nn.functional as F


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


def metrics_table(results, classes):
    """Precision / recall / F1 / IoU per class for every option, built from the stored confusion matrices
    (rows = true class, columns = predicted). Adds a macro-average row per option, with overall pixel
    accuracy on that row. Returns a pandas DataFrame."""
    import pandas as pd
    rows = []
    for r in results:
        cm = np.array(r["confusion"], dtype=np.float64)
        tp = np.diag(cm)
        fn = cm.sum(1) - tp
        fp = cm.sum(0) - tp

        def div(a, b):
            return np.where(b > 0, a / np.maximum(b, 1e-12), 0.0)

        prec, rec = div(tp, tp + fp), div(tp, tp + fn)
        f1 = div(2 * prec * rec, prec + rec)
        iou = div(tp, tp + fp + fn)
        support = cm.sum(1)
        for i, c in enumerate(classes):
            rows.append({"Mae Suai in training": lab(r), "class": c, "precision": prec[i],
                         "recall": rec[i], "F1": f1[i], "IoU": iou[i],
                         "pixels": int(support[i]), "accuracy": np.nan})
        rows.append({"Mae Suai in training": lab(r), "class": "macro avg", "precision": prec.mean(),
                     "recall": rec.mean(), "F1": f1.mean(), "IoU": iou.mean(),
                     "pixels": int(cm.sum()), "accuracy": tp.sum() / max(cm.sum(), 1)})
    return pd.DataFrame(rows)


def print_metrics_table(results, classes, save_to=None):
    """Print the precision/recall/F1/IoU table (and optionally save it as CSV). Returns the DataFrame."""
    df = metrics_table(results, classes)
    show = df.copy()
    show["accuracy"] = show["accuracy"].map(lambda v: "" if v != v else f"{v:.3f}")
    show["Mae Suai in training"] = show["Mae Suai in training"].where(
        show["Mae Suai in training"] != show["Mae Suai in training"].shift(), "")
    print(show.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    if save_to:
        df.to_csv(save_to, index=False)
    return df


# ---------------------------------------------------------------------------
# NEW: real images -> raw | ground truth | prediction(s)
# ---------------------------------------------------------------------------
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def make_palette(n_classes, cmap="tab10"):
    """(n_classes, 3) uint8 colours. Class 0 is NOT forced to black; edit if you want that."""
    cm = plt.get_cmap(cmap, max(n_classes, 2))
    return (np.array([cm(i)[:3] for i in range(n_classes)]) * 255).astype(np.uint8)


# Label colours (OpenEarthMap labelling scheme: tree = id 5, water = id 6).
# Edit these if your labelling tool used other colours; "other" is light grey so it
# stays distinguishable from ignored pixels, which are drawn white.
LABEL_COLORS = {
    "other": (200, 200, 200),
    "tree":  (34, 97, 38),       # #226126
    "water": (0, 69, 255),       # #0045FF
}


def default_palette(classes):
    """Colours from the labelling scheme by class name; unknown names fall back to tab10."""
    fallback = make_palette(len(classes))
    return np.array([LABEL_COLORS.get(str(c).lower(), fallback[i]) for i, c in enumerate(classes)],
                    dtype=np.uint8)


def to_rgb_image(img, mean=IMAGENET_MEAN, std=IMAGENET_STD):
    """Tensor (C,H,W) or array -> uint8 (H,W,3) with NO labels, i.e. the raw image.
    Pass mean=None to skip de-normalisation if your dataset returns raw 0-1 / 0-255 data."""
    if torch.is_tensor(img):
        img = img.detach().cpu().float().numpy()
    img = np.asarray(img)
    if img.ndim == 3 and img.shape[0] in (1, 3, 4) and img.shape[-1] not in (1, 3, 4):
        img = np.transpose(img, (1, 2, 0))          # CHW -> HWC
    img = img[..., :3] if img.shape[-1] >= 3 else np.repeat(img[..., :1], 3, axis=-1)
    if mean is not None:
        img = img * np.array(std) + np.array(mean)
        if img.max() > 1.5:                          # already 0-255
            img = img / 255.0
    else:                                            # display-only contrast stretch (2-98 percentile)
        lo, hi = np.percentile(img, (2, 98))
        img = (img - lo) / (hi - lo) if hi > lo else np.zeros_like(img)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def colorize(mask, palette, ignore_index=255):
    """Class-id mask (H,W) -> RGB (H,W,3). Ignored pixels are drawn white."""
    mask = np.asarray(mask)
    out = np.full(mask.shape + (3,), 255, dtype=np.uint8)
    valid = (mask != ignore_index) & (mask >= 0) & (mask < len(palette))
    out[valid] = palette[mask[valid]]
    return out


def overlay(rgb, color_mask, alpha=0.5):
    return (rgb * (1 - alpha) + color_mask * alpha).astype(np.uint8)


@torch.no_grad()
def predict_mask(model, img_tensor, device, out_size=None):
    """Run one image through the model and return the argmax class map (H,W) as numpy.
    Handles plain tensors, torchvision dicts ({'out': ...}) and HuggingFace outputs (.logits)."""
    model.eval()
    out = model(img_tensor.unsqueeze(0).to(device))
    if isinstance(out, dict):
        out = out["out"]
    elif hasattr(out, "logits"):
        out = out.logits
    elif isinstance(out, (tuple, list)):
        out = out[0]
    if out_size is not None and out.shape[-2:] != tuple(out_size):
        out = F.interpolate(out, size=out_size, mode="bilinear", align_corners=False)
    return out.argmax(1)[0].cpu().numpy()


def plot_predictions(models, dataset, classes, indices=None, n=6, seed=0, device=None,
                     palette=None, mean=IMAGENET_MEAN, std=IMAGENET_STD, ignore_index=255,
                     show_overlay=True, show_error=True, alpha=0.5, save_to=None):
    """Side-by-side comparison on real test images.

    models  : dict {label: trained_model} (e.g. one per fraction) or a single model.
    dataset : indexable, returns (image_tensor, mask) -- same dataset you evaluate on.
    Columns : Raw image | Ground truth | one Prediction per model | (optional) error map of the LAST model
              Red pixels in the error map = wrong, black = correct, white = ignored.
    show_overlay: draw GT/predictions blended on top of the raw image instead of as flat colours.
    """
    if not isinstance(models, dict):
        models = {"model": models}
    device = device or next(iter(models.values())).parameters().__next__().device
    palette = palette if palette is not None else default_palette(classes)

    if indices is None:
        rng = np.random.default_rng(seed)
        indices = rng.choice(len(dataset), size=min(n, len(dataset)), replace=False)

    col_titles = ["Raw image", "Ground truth"] + [f"Pred: {k}" for k in models]
    if show_error:
        col_titles.append(f"Errors: {list(models)[-1]}")
    ncols, nrows = len(col_titles), len(indices)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.2 * ncols, 3.0 * nrows), squeeze=False)

    for row, idx in enumerate(indices):
        img_t, gt = dataset[int(idx)]
        gt = gt.numpy() if torch.is_tensor(gt) else np.asarray(gt)
        gt = gt.squeeze()
        rgb = to_rgb_image(img_t, mean, std)
        if rgb.shape[:2] != gt.shape:                # keep everything the same size
            rgb = np.array(torch.nn.functional.interpolate(
                torch.from_numpy(rgb).permute(2, 0, 1)[None].float(), size=gt.shape,
                mode="bilinear", align_corners=False)[0].permute(1, 2, 0).clamp(0, 255).byte())

        panels = [rgb]
        gt_c = colorize(gt, palette, ignore_index)
        panels.append(overlay(rgb, gt_c, alpha) if show_overlay else gt_c)

        pred = None
        for m in models.values():
            pred = predict_mask(m, img_t, device, out_size=gt.shape)
            p_c = colorize(pred, palette)
            panels.append(overlay(rgb, p_c, alpha) if show_overlay else p_c)

        if show_error:
            err = np.zeros(gt.shape + (3,), dtype=np.uint8)
            err[pred != gt] = (220, 40, 40)
            err[gt == ignore_index] = 255
            panels.append(err)

        for col, panel in enumerate(panels):
            ax = axes[row][col]
            ax.imshow(panel); ax.set_xticks([]); ax.set_yticks([])
            if row == 0:
                ax.set_title(col_titles[col], fontsize=10)
        axes[row][0].set_ylabel(f"#{int(idx)}", fontsize=9)

    handles = [mpatches.Patch(color=palette[i] / 255.0, label=c) for i, c in enumerate(classes)]
    fig.legend(handles=handles, loc="lower center", ncol=min(len(classes), 8), frameon=False)
    plt.tight_layout(rect=(0, 0.04, 1, 1))
    if save_to: plt.savefig(save_to, dpi=120, bbox_inches="tight")
    plt.show()


# Example:
# models = {"0%": m0, "25%": m25, "100%": m100}          # trained models, one per fraction
# plot_predictions(models, test_dataset, classes, n=6, save_to="predictions.png")
# plot_predictions(models, test_dataset, classes, indices=[3, 17, 42], show_overlay=False)


# ---------------------------------------------------------------------------
# NEW: pick a test image by (part of) its filename
# ---------------------------------------------------------------------------
from pathlib import Path

_PATH_ATTRS = ("image_paths", "img_paths", "images", "image_files", "files",
               "paths", "pairs", "samples")


def _unwrap(dataset):
    """Return (base_dataset, index_map). Sees through torch Subset (random_split etc.)."""
    idx_map = None
    while hasattr(dataset, "dataset") and hasattr(dataset, "indices"):
        inner = list(dataset.indices)
        idx_map = inner if idx_map is None else [inner[i] for i in idx_map]
        dataset = dataset.dataset
    return dataset, idx_map


def _as_name(p):
    if isinstance(p, dict):
        p = next(iter(p.values()))
    if isinstance(p, (tuple, list)):        # (image_path, mask_path) pairs -> image path
        p = p[0]
    return Path(str(p)).name


def _dataset_names(dataset):
    base, idx_map = _unwrap(dataset)
    for attr in _PATH_ATTRS:
        items = getattr(base, attr, None)
        if items is None or isinstance(items, (str, bytes, dict)):
            continue
        try:
            items = list(items)
        except TypeError:
            continue
        if not items:
            continue
        names = [_as_name(p) for p in items]
        if idx_map is not None:
            names = [names[i] for i in idx_map]
        return names, attr
    return None, None


def find_image_index(dataset, query, names=None):
    """Return (index, filename) of the first image whose name contains `query`, else (None, None).
    Pass `names` (list of file names in dataset order) to skip the automatic attribute search."""
    if names is not None:
        names, attr = [_as_name(n) for n in names], "names"
    else:
        names, attr = _dataset_names(dataset)
    if names is None:
        base, _ = _unwrap(dataset)
        try:
            attrs = sorted(vars(base).keys())
        except TypeError:
            attrs = [a for a in dir(base) if not a.startswith("_")]
        print("Could not find a list of file names on the dataset. Attributes it has:")
        print(attrs)
        print("Tell me which one holds the image paths (or paste your SegDataset __init__).")
        return None, None
    if len(names) != len(dataset):
        print(f"Warning: {len(names)} file names but dataset length is {len(dataset)}; "
              f"indices may not line up (repeated or cropped samples?).")
    hits = [i for i, n in enumerate(names) if query and query.lower() in n.lower()]
    if not hits:
        print(f"No image matches '{query}'. First 15 available (from .{attr}):")
        for i, n in enumerate(names[:15]):
            print(f"   [{i}] {n}")
        return None, None
    if len(hits) > 1:
        print(f"{len(hits)} matches, using the first. Others: {[names[i] for i in hits[1:5]]}")
    return hits[0], names[hits[0]]


def plot_prediction_by_filename(model, test_loader, classes, device=None, filename_query="",
                                show_overlay=False, show_error=False, names=None, **kwargs):
    """Find a test image by filename (or part of it) and plot raw | ground truth | prediction.

    model       : one trained model, or a dict {label: model} to compare several side by side.
    test_loader : a DataLoader or a Dataset.
    extra kwargs go to plot_predictions (mean, std, ignore_index, palette, alpha, save_to).
    Returns the dataset index that was plotted (or None if nothing matched).
    """
    dataset = getattr(test_loader, "dataset", test_loader)
    idx, name = find_image_index(dataset, filename_query, names=names)
    if idx is None:
        return None
    print(f"Showing: {name}  (dataset index {idx})")
    _x, _ = dataset[idx]
    _x = _x.float() if torch.is_tensor(_x) else torch.as_tensor(_x).float()
    print(f"Model input tensor: shape {tuple(_x.shape)} | min {_x.min():.4f} | max {_x.max():.4f} | mean {_x.mean():.4f}")
    plot_predictions(model, dataset, classes, indices=[idx], device=device,
                     show_overlay=show_overlay, show_error=show_error, **kwargs)
    return idx


def setup_viewer(cfg, own_shuffled, own_ids, paths, device, test_fraction=0.75,
                 fractions=(0, 25, 50, 75, 100), **plot_kwargs):
    """Build the test loader (same way run_fraction does) and load one trained model per fraction.
    Returns a `show` function:  show("85.tif")  |  show(["85.tif", "57.tif"])  |  show("all")
    `show.names`, `show.models` and `show.test_loader` are also available."""
    from torch.utils.data import DataLoader
    import segmentation_models_pytorch as smp
    from src.data.pairing import split_for
    from src.data.seg_dataset import SegDataset

    classes = cfg["classes"]
    model_name = cfg["model"]["active"]
    spec = cfg["models"][model_name]
    archs = {"unet": smp.Unet, "fpn": smp.FPN, "deeplabv3plus": smp.DeepLabV3Plus}
    Arch = archs.get(spec["decoder"], smp.Unet)

    # test set
    _, own_test = split_for(own_shuffled, test_fraction)
    test_loader = DataLoader(
        SegDataset(own_test, own_ids, classes, cfg["image_max"]["own"],
                   cfg["data"]["crop_size"], train=False),
        batch_size=1, shuffle=False, num_workers=0)
    names = [Path(a).name for a, _ in own_test]
    print(f"test images ({len(names)}, from the {int(round((1 - test_fraction) * 100))}% never used "
          f"by models trained on <= {int(test_fraction * 100)}%):")
    print("  " + "  ".join(f"[{i}] {n}" for i, n in enumerate(names)))

    # models
    weights_dir = Path(paths["weights_dir"])
    models = {}
    for p in fractions:
        m = Arch(encoder_name=spec["encoder"], encoder_weights=None,
                 in_channels=cfg["in_channels"], classes=len(classes))
        ckpt = torch.load(weights_dir / f"{model_name}_fraction_{p}_last.pth", map_location=device)
        if isinstance(ckpt, dict) and "state_dict" in ckpt:
            ckpt = ckpt["state_dict"]
        elif isinstance(ckpt, dict) and "model" in ckpt:
            ckpt = ckpt["model"]
        m.load_state_dict(ckpt)
        models[f"{p}%"] = m.to(device).eval()
    print("models loaded:", list(models))

    kw = dict(mean=None, std=None)
    kw.update(plot_kwargs)

    def show(query="", **extra):
        if query == "all":
            query = names
        if isinstance(query, (list, tuple)):
            for q in query:
                show(q, **extra)
            return
        return plot_prediction_by_filename(models, test_loader, classes, device,
                                           filename_query=query or names[0], names=names,
                                           **{**kw, **extra})

    show.names, show.models, show.test_loader = names, models, test_loader
    return show


# Example:
# show = setup_viewer(cfg, own_shuffled, OWN_IDS, P, device)
# show("85.tif")