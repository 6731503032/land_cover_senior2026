"""Turn the paths in the yaml into real folders."""
from pathlib import Path


def resolve_paths(cfg):
    p = cfg["paths"]
    root = Path(p["data_root"])

    def full(x):
        x = Path(x)
        return x if x.is_absolute() else root / x

    out = {k: full(p[k]) for k in ["own_images", "own_masks", "oem_images", "oem_masks"]}
    out["weights_dir"] = Path(p["weights_dir"])
    out["results_dir"] = Path(p["results_dir"])
    out["weights_dir"].mkdir(parents=True, exist_ok=True)
    out["results_dir"].mkdir(parents=True, exist_ok=True)
    for k in ["own_images", "own_masks", "oem_images", "oem_masks"]:
        assert out[k].exists(), f"Folder not found: {out[k]}"
    return out
