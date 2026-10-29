# How to Export Label Masks and Compute Class Percentages (QGIS 3.44)

For **OEM 8-class** labels (values 0–8) on Sentinel-2 imagery at 10 m resolution. 1 chip = 256 × 256 pixels.

| Value | Class | Color (HEX) |
|---|---|---|
| 0 | Unlabeled (not drawn yet / ignored) | 000000 |
| 1 | Bareland | 800000 |
| 2 | Rangeland | 00FF24 |
| 3 | Developed space | 949494 |
| 4 | Road | FFFFFF |
| 5 | Tree | 226126 |
| 6 | Water | 0045FF |
| 7 | Agriculture land | 4BB549 |
| 8 | Building | DE1F07 |

---

## Part 1: Export labels as a mask file (.tif)

### Step 1: Convert the label polygons into a mask for the whole area

1. **Processing Toolbox** → search **Rasterize (vector to raster)** → double-click
2. Settings:
   - **Input layer:** `labels_2019`
   - **Field to use for a burn-in value:** `class_id`
   - **Output raster size units:** `Georeferenced units`
   - **Width/Horizontal resolution:** `10`
   - **Height/Vertical resolution:** `10`
     (clear the old value in the box before typing; if it accidentally becomes 10000000 you get the error `0x256 dataset is illegal`)
   - **Output extent:** ▼ → **Calculate from Layer** → pick that year's mosaic, e.g. `2019_all_RGB`
   - **Assign a specified NoData value:** leave empty
   - **Advanced Parameters:**
     - Pre-initialize the output image with value = `0`
     - Output data type = `Byte`
   - **Rasterized:** click `...` → **Save to File** → e.g. `mask_2019.tif`
     (do not leave it as a temporary file — it disappears when QGIS closes)
3. Click **Run**
4. Check: right-click the layer → Properties → **Information** should show **2560 × 1280** (10 × 5 chips) and CRS `EPSG:32647`

### Step 2: Cut out a single image (1 chip)

1. Click the `chip_index` layer → **Select Features** tool → click **one** chip frame
   (if other frames are still selected/yellow, press `Ctrl+Alt+A` first to clear the selection)
2. **Raster → Extraction → Clip Raster by Mask Layer**
   - **Input layer:** `mask_2019`
   - **Mask layer:** `chip_index` + tick **Selected features only**
   - **Assign a specified NoData value:** leave empty
   - Tick **Match the extent of the clipped raster to the extent of the mask layer**
   - Tick **Keep resolution of input raster**
   - **Clipped (mask):** e.g. `mask_2019_51.tif`
3. Click **Run** → check that the result is **256 × 256**

### Step 3 (optional): Make the file open in color

**Why it opens in black and white:** the mask file stores only **class numbers (0–8)**, not colors. The colors you see in QGIS come from a style, not from the file. Other programs therefore show the numbers as brightness (Windows Photos looks almost black; some web viewers show shades of grey). **The file is not broken — this is exactly the format used to train the model.**

**Option A — Embed a color table in the same file (still usable for training)**

1. Remove the layer from QGIS first (right-click → Remove Layer), otherwise the file is locked
2. **Plugins → Python Console** → paste the code, edit `path`, press Enter

```python
from osgeo import gdal
path = r'C:\path\to\mask_2019_51.tif'   # <- change to the real file location
C = {0:(0,0,0),1:(128,0,0),2:(0,255,36),3:(148,148,148),4:(255,255,255),
     5:(34,97,38),6:(0,69,255),7:(75,181,73),8:(222,31,7)}
ds = gdal.Open(path, gdal.GA_Update); b = ds.GetRasterBand(1)
ct = gdal.ColorTable()
for k, (r, g, bl) in C.items(): ct.SetColorEntry(k, (r, g, bl, 255))
b.SetRasterColorTable(ct); b.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)
ds = None; print('done')
```

The values inside do not change (still 0–8), but Photos / QGIS will now show colors.
(Some web TIFF viewers do not support color tables and may still show grey.)

**Option B — Export a color picture for viewing or reports (do NOT use for training)**

1. Make the layer display in color first: Properties → Style → **Load Style** → `mask_8class_oem_raster.qml`
   (or Symbology → **Paletted/Unique values** → **Classify**)
2. Right-click the layer → **Export → Save As...**
   - **Output mode:** `Rendered image`  ← important; with Raw data the colors are lost
   - **Format:** `PNG`
   - **Resolution:** `10` / `10`
3. Save

### Why the mask edges look like stair steps

The mask has 256 × 256 pixels, the same as the satellite image (1 pixel = 10 m). Each pixel can hold only one class, so edges follow the pixel grid — **this is correct**, because the mask must line up with the image pixel by pixel.
For a smooth picture in a report, use **Project → Import/Export → Export Map to Image** from the polygon layer (`labels_2019`) at 300 dpi.

---

## Part 2: Compute the percentage of each class in an image

1 pixel = 10 × 10 m = 100 m²; 1 chip = 65,536 pixels (≈ 655 ha)

### Method 1: QGIS tool

1. **Processing Toolbox** → search **Raster layer unique values report** → double-click
2. **Input layer:** the mask file, e.g. `mask_2019_51`
3. **Run** → click the HTML file link in the results
4. You get a table of value / pixel count / area (m²)
   - % = pixel count ÷ total pixels × 100 (1 chip = 65,536)

### Method 2: Python Console (gives % with class names)

**Plugins → Python Console** → paste the code, edit `path` → Enter

```python
from osgeo import gdal; import numpy as np
path = r'C:\path\to\mask_2019_51.tif'   # <- change to the real file location
N = {0:'Unlabeled',1:'Bareland',2:'Rangeland',3:'Developed space',4:'Road',
     5:'Tree',6:'Water',7:'Agriculture',8:'Building'}
a = gdal.Open(path).ReadAsArray(); n = np.bincount(a.ravel(), minlength=9)
for k in range(9):
    if n[k]: print(f'{k} {N[k]:16s} {100*n[k]/a.size:6.2f}%  ({n[k]*100/1e4:.1f} ha)')
```

Example output:

```
1 Bareland           38.20%  (25.0 ha)
5 Tree               35.10%  (23.0 ha)
6 Water               0.40%  (0.3 ha)
```

Works for both a single chip (256 × 256) and the whole area (2560 × 1280).

### Cautions

- If the result contains **0 Unlabeled**, the chip is not fully labeled yet and the other classes' % will be too low → finish labeling before reporting numbers
- To compare years, use the same chip and the same grid for all 3 years (2019 / 2022 / 2025)

---

## File summary

| File | Purpose |
|---|---|
| `mask_2019.tif` (black & white, values 0–8) | Model training / computing % |
| `mask_2019_51.tif` (1 chip, 256 × 256) | Per-chip training |
| Same file + embedded color table | Still trainable, and opens in color |
| `*.png` (Rendered image) | Viewing or reports only |
| `mask_8class_oem_raster.qml` | Color style for opening masks in QGIS |
