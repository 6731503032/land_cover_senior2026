# What every file is for

## Top level
| File | What it is |
|---|---|
| README.md | The front page on GitHub: what the project is and how to run it. |
| STRUCTURE.md | This file. |
| .gitignore | A list of files Git must NOT upload (imagery, model weights). Without it, big files would break your upload. |
| requirements.txt | The Python libraries to install (`pip install -r requirements.txt`). |

## configs/  (settings, one file per experiment)
| File | What it is |
|---|---|
| train_oem.yaml | Settings for training on OpenEarthMap: crop size, learning rate, epochs, model. Change numbers here, not in the code. |
| finetune_maesuai.yaml | Settings for the second step: adjusting the trained model with our own Mae Suai labels (smaller learning rate). |

## data/  (not uploaded to GitHub)
| File | What it is |
|---|---|
| README.md | Says where to download each dataset and how folders must look. |
| raw/ | Untouched downloads: OEM, IRSAMap, the 120 GEE chips. |
| processed/ | Ready-to-train tiles and masks, made by the scripts. |

## gee/
| File | What it is |
|---|---|
| maesuai_gee_export.js | The Google Earth Engine script that exports the 40 chips x 3 years. |

## src/  (the main code)
| File | What it is |
|---|---|
| data/classes.py | The class list and the mapping from OEM/IRSAMap classes to ours. Keep all class decisions here. |
| data/dataset.py | Reads image and mask pairs and cuts random crops to feed the model. |
| models/build.py | Builds the segmentation network (U-Net by default) from a config file. |
| train.py | Trains the model and saves it to checkpoints/. |
| predict.py | Predicts on a big image by cutting it into overlapping tiles and stitching them back. |
| evaluate.py | Accuracy: confusion matrix, IoU per class, mIoU. |
| change_analysis.py | Compares two years: area per class, net change, % change, yearly rate, transition matrix. |

## Other folders
| File | What it is |
|---|---|
| scripts/make_splits.py | Splits images into train, validation and test once and saves the list, so everyone uses the same split. |
| scripts/polygons_to_masks.py | Unfinished starter: turns polygons into pixel masks. |
| notebooks/ | Jupyter notebooks for exploring, numbered (01_..., 02_...). Not the main code. |
| labels/ | Our own hand-labelled Mae Suai polygons (small, so they are uploaded). |
| results/ | Final tables and figures (small files only). |
| docs/labelling_rules.md | A table for writing the rules each class follows. Fill it in as a team. |
| docs/decisions.md | A log of team decisions (years, classes, crop size) so nobody re-argues them. |
| tests/test_core.py | Automatic checks that the accuracy and change code gives correct answers. |

## Notes
- `__init__.py` and `.gitkeep` files are empty on purpose. The first lets Python import the folder; the second makes Git keep an empty folder.
- Files marked "starter" or with placeholder lists (classes, rules, decisions) need your team to fill them in.
