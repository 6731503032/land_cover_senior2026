# data/

Nothing in here goes on GitHub (files are too big). Each teammate downloads it themselves.

| Folder | What to put there | Where from |
|---|---|---|
| raw/oem | OpenEarthMap | https://open-earth-map.org |
| raw/irsamap | IRSAMap | https://github.com/ucas-dlg/IRSAMap |
| raw/gee_chips | the 120 GeoTIFFs from gee/maesuai_gee_export.js | your Google Drive folder MaeSuai_chips |
| processed/ | tiles, masks and splits.json made by scripts/ | generated, do not edit by hand |

Expected layout for training: processed/<dataset>/<split>/images/*.png and masks/*.png
(same file names; masks hold one class number per pixel).
