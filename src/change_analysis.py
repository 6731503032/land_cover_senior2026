"""Change analysis between two classified maps (e.g. 2019 vs 2025)."""
import numpy as np


def transition_matrix(map_a, map_b, num_classes, pixel_area_ha=0.01):
    """Area (hectares) that moved from each class (rows, earlier year)
    to each class (columns, later year). 10 m pixel = 0.01 ha."""
    idx = map_a.astype(int).ravel() * num_classes + map_b.astype(int).ravel()
    counts = np.bincount(idx, minlength=num_classes ** 2).reshape(num_classes, num_classes)
    return counts * pixel_area_ha


def class_summary(tm, years_between):
    """Per-class area, net change, % change and annual rate from a transition matrix."""
    a = tm.sum(1)   # area in the earlier year
    b = tm.sum(0)   # area in the later year
    net = b - a
    with np.errstate(divide="ignore", invalid="ignore"):
        pct = net / a * 100
        annual = ((b / a) ** (1 / years_between) - 1) * 100
    persistence = np.diag(tm)
    return {"area_start": a, "area_end": b, "net_change": net,
            "pct_change": pct, "annual_rate_pct": annual, "unchanged": persistence}
