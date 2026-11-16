# Land Cover Mapping & Change Analysis: Chiang Rai (Mae Suai)

Deep-learning land-cover maps of Mae Suai, Chiang Rai, from 10 m Sentinel-2 images, and how the land changed between years.

We train on **OpenEarthMap (OEM)**, add a small set of our own hand-labelled Mae Suai images, and measure how much local data the model needs.

## Setup

```bash
git clone https://github.com/6731503032/land_cover_senior2026.git
cd land_cover_senior2026
pip install -r requirements.txt
pip install matplotlib pandas
python -m pytest tests        # checks the metric and change-analysis code
```

The large data files are not on GitHub. Download them yourself, as `data/README.md` explains.

## Workflow

1. **Export images:** run `data/gee/maesuai_gee_export.js` in Google Earth Engine to export the Mae Suai chips.
2. **Label:** open each chip in QGIS with `scripts/qgis_script.py` and draw polygons. Follow the class rules in `docs/labelling_rules.md`.
3. **Prepare data:** download OEM (and IRSAMap later) into `data/raw/`. Then run `python scripts/make_splits.py data/processed/oem` so everyone uses the same split.
4. **Train:** `src/experiments/` trains on OEM plus 0–100% of the Mae Suai images, then tests on the Mae Suai images it did not see. Settings are in `configs/*.yaml`.
5. **Evaluate:** `src/evaluate.py` saves mIoU, confusion matrices and IoU heatmaps to `results/`.
6. **Change analysis:** `src/change_analysis.py` compares two yearly maps (area per class, net change, transition matrix).

## src/

| Folder / file | What it does |
|---|---|
| `data/` | Finds and pairs images with masks (`pairing.py`), makes the fixed 80/20 Mae Suai split (`own_split.py`), loads and crops chips (`seg_dataset.py`, `dataset.py`), turns yaml paths into folders (`paths.py`), and holds the class list (`classes.py`) |
| `models/` | `build.py` builds the segmentation model from the yaml (U-Net, FPN, Swin) |
| `training/` | `train_one.py` trains one model with early stopping |
| `experiments/` | `fraction.py` and `oem_fraction.py` run one step of the "how much Mae Suai data do we need" test |
| `evaluation/` | `metrics.py` computes IoU and mIoU |
| `visualization/` | `plots.py` makes the result tables and plots |
| `train.py` | Training loop: train, check on validation images, keep the best model |
| `predict.py` | Predicts a large image tile by tile and stitches the result |
| `evaluate.py` | mIoU, per-class IoU and prediction pictures |
| `change_analysis.py` | Area change and transition matrix between two years |

## Configs

| File | Used for |
|---|---|
| `configs/water_tree.yaml` | 3-class experiment |
| `configs/oem_8class.yaml` | 8-class experiment |
| `configs/train_oem.yaml` | Training on OEM only |
| `configs/finetune_maesuai.yaml` | Fine-tuning on Mae Suai labels |

Change the folder paths in `paths:` to match your computer before running.

## Classes

Bareland, Rangeland, Developed space, Road, Tree, Water, Agriculture, Building (the 8 OEM classes).

## Not finished yet

- `scripts/polygons_to_masks.py` is a starter and does not run yet.
- IRSAMap is planned for Semester 2.

See `STRUCTURE.md` for what every file does.

## Team

Group Newbie, Mae Fah Luang University: Wacharaphong Sutthiboriban, Yosnawat Onjan, Kazunori Kanazawa