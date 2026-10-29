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

### Method 2: Excel report for many images + color PNGs (Python Console)

Creates `class_percent.xlsx` with **one row per image and one column per class**, plus a color PNG of every mask.

| image | file | Unlabeled (%) | Bareland (%) | Rangeland (%) | Developed space (%) | Road (%) | Tree (%) | Water (%) | Agriculture (%) | Building (%) |
|---|---|---|---|---|---|---|---|---|---|---|
| 51 | mask_2019_51 | 0 | 33.17 | 0 | 0 | 0 | 33.28 | 0 | 33.55 | 0 |
| 52 | mask_2019_52 | 33.28 | 0 | 0 | 0 | 0 | 0 | 33.55 | 33.17 | 0 |

- `image` = chip number taken from the end of the file name (`mask_2019_51` → 51); `file` = full file name
- Values are plain numbers 0–100 (each row sums to 100). **Do not apply Excel's % format** to these columns — Excel multiplies by 100 again (23.32 → 2332%)
- Header is bold and frozen, with filters on every column

How to run:

1. **Plugins → Python Console** → click **Show Editor**
2. Paste the code below
3. Edit `INPUT` (a folder of mask .tif files, or one .tif file) and `OUTDIR` (output folder; created if missing)
4. Click **Run** in the editor → the console prints a summary per image and ends with `done`

Output in `OUTDIR`: `class_percent.xlsx` + one `<file name>.png` per mask.
The script uses `openpyxl` if available; otherwise it falls back to GDAL's built-in XLSX writer (same data, no bold header/filters).

```python
# QGIS Python Console: class % per mask image -> Excel (.xlsx), plus a color PNG of each image
# Plugins > Python Console > Show Editor > paste > edit the 2 paths > Run
import os, glob
import numpy as np
from osgeo import gdal

INPUT  = r'C:\path\to\masks'          # a folder of mask .tif files, OR a single .tif file
OUTDIR = r'C:\path\to\mask_report'    # class_percent.xlsx + PNG pictures are written here

N = {0: 'Unlabeled', 1: 'Bareland', 2: 'Rangeland', 3: 'Developed space', 4: 'Road',
     5: 'Tree', 6: 'Water', 7: 'Agriculture', 8: 'Building'}
COL = {0: (0, 0, 0), 1: (128, 0, 0), 2: (0, 255, 36), 3: (148, 148, 148), 4: (255, 255, 255),
       5: (34, 97, 38), 6: (0, 69, 255), 7: (75, 181, 73), 8: (222, 31, 7)}
LUT = np.zeros((256, 3), np.uint8)
for k, c in COL.items(): LUT[k] = c

files = [INPUT] if INPUT.lower().endswith(('.tif', '.tiff')) else sorted(glob.glob(os.path.join(INPUT, '*.tif')))
os.makedirs(OUTDIR, exist_ok=True)
import re
CLASSES = [k for k in range(9)]
HEADER = ['image', 'file'] + [f'{N[k]} (%)' for k in CLASSES]
rows = []
for p in files:
    ds = gdal.Open(p)
    a = ds.ReadAsArray()
    name = os.path.splitext(os.path.basename(p))[0]
    m = re.search(r'(\d+)$', name)
    img = int(m.group(1)) if m else name                     # e.g. mask_2019_51 -> 51
    n = np.bincount(a.ravel(), minlength=9)[:9]
    rows.append([img, name] + [round(100 * n[k] / a.size, 2) for k in CLASSES])

    # color picture (PNG) of the same image
    rgb = LUT[np.clip(a, 0, 255)]
    mem = gdal.GetDriverByName('MEM').Create('', a.shape[1], a.shape[0], 3, gdal.GDT_Byte)
    for i in range(3): mem.GetRasterBand(i + 1).WriteArray(rgb[:, :, i])
    gdal.GetDriverByName('PNG').CreateCopy(os.path.join(OUTDIR, name + '.png'), mem)
    mem = None; ds = None
    print(name, ' | '.join(f'{N[k]} {100*n[k]/a.size:.1f}%' for k in CLASSES if n[k]))

xlsx_path = os.path.join(OUTDIR, 'class_percent.xlsx')
if os.path.exists(xlsx_path): os.remove(xlsx_path)
try:                                   # nicer file with openpyxl (if installed)
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    wb = Workbook(); ws = wb.active; ws.title = 'class_percent'
    ws.append(HEADER)
    for c in ws[1]: c.font = Font(bold=True); c.alignment = Alignment(wrap_text=True)
    for r in rows: ws.append(r)
    for row in ws.iter_rows(min_row=2, min_col=3):
        for c in row: c.number_format = '0.00'                # plain number 0-100, not Excel % format
    ws.freeze_panes = 'C2'; ws.auto_filter.ref = ws.dimensions
    ws.column_dimensions['A'].width = 8; ws.column_dimensions['B'].width = 20
    wb.save(xlsx_path)
except ImportError:                    # fallback: GDAL's built-in XLSX writer
    from osgeo import ogr
    out = ogr.GetDriverByName('XLSX').CreateDataSource(xlsx_path)
    lyr = out.CreateLayer('class_percent', geom_type=ogr.wkbNone)
    lyr.CreateField(ogr.FieldDefn('image', ogr.OFTString)); lyr.CreateField(ogr.FieldDefn('file', ogr.OFTString))
    for h in HEADER[2:]: lyr.CreateField(ogr.FieldDefn(h, ogr.OFTReal))
    for r in rows:
        f = ogr.Feature(lyr.GetLayerDefn())
        for i, v in enumerate(r): f.SetField(i, str(v) if i < 2 else v)
        lyr.CreateFeature(f); f = None
    out = None

print('done ->', OUTDIR, '|', len(files), 'images')
```

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
| `class_percent.xlsx` | Class % per image (Method 2) |
| `mask_8class_oem_raster.qml` | Color style for opening masks in QGIS |
