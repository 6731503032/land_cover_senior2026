# Land cover mapping and change analysis: Chiang Rai (Mae Suai)

Deep-learning land cover maps of Mae Suai for three years, and the change between them.

## Quick start
```bash
pip install -r requirements.txt
python -m pytest tests            # checks the metric and change code
python -m src.train configs/train_oem.yaml
```

## Workflow
1. `gee/` : export Mae Suai chips from Google Earth Engine.
2. `data/` : download OEM and IRSAMap, prepare tiles and masks.
3. `src/train.py` : train on OEM/IRSAMap, then fine-tune on our labels.
4. `src/predict.py` + `src/evaluate.py` : map Mae Suai, measure mIoU.
5. `src/change_analysis.py` : area change and transition matrix between years.

See STRUCTURE.md for what every file is.
