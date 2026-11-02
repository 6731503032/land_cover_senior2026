# How to Export Label Masks and Count Class Percentages

For QGIS 3.44. Sentinel-2 images, 10 m per pixel. One chip = 256 × 256 pixels.

## The 8 classes

| Value | Class | Colour |
|---|---|---|
| 1 | Bareland | `800000` |
| 2 | Rangeland | `00FF24` |
| 3 | Developed space | `949494` |
| 4 | Road | `FFFFFF` |
| 5 | Tree | `226126` |
| 6 | Water | `0045FF` |
| 7 | Agriculture land | `4BB549` |
| 8 | Building | `DE1F07` |

Every pixel must belong to one of these 8 classes. Before exporting, make sure the whole chip is covered by polygons, with no empty gaps.

---

## Part 1: Save the labels as a mask (.tif)

A mask is a picture where each pixel holds the class number (1 to 8) instead of a colour.

### Step 1: Turn all polygons into one mask

1. Open the **Processing Toolbox**, search **Rasterize (vector to raster)**, and double-click it.
2. Fill in:
   - **Input layer:** `labels_2019`
   - **Field to use for a burn-in value:** `class_id`
   - **Output raster size units:** Georeferenced units
   - **Width / Height:** `10` and `10`. Delete the old number in each box before typing. If a box becomes `10000000`, you get the error "dataset is illegal".
   - **Output extent:** click ▼ > **Calculate from Layer** > pick that year's image, for example `2019_all_RGB`
   - **NoData value:** leave empty
3. Open **Advanced Parameters** and set:
   - **Pre-initialize the output image with value:** `0`
   - **Output data type:** `Byte`
4. Next to **Rasterized**, click `...` > **Save to File** and name it, for example `mask_2019.tif`. Don't leave it as a temporary file, because it disappears when QGIS closes.
5. Click **Run**.
6. Check: right-click the new layer > **Properties** > **Information**. It should say 2560 × 1280 (10 × 5 chips) and EPSG:32647.

### Step 2: Cut out one chip

1. Click the `chip_index` layer and choose **Select Features**. Click one chip frame. If other frames are already yellow, press **Ctrl+Alt+A** first to clear them.
2. Go to **Raster > Extraction > Clip Raster by Mask Layer**.
3. Fill in:
   - **Input layer:** `mask_2019`
   - **Mask layer:** `chip_index`, and tick **Selected features only**
   - **NoData value:** leave empty
   - Tick **Match the extent of the clipped raster to the extent of the mask layer**
   - Tick **Keep resolution of input raster**
   - **Clipped (mask):** save as, for example, `mask_2019_51.tif`
4. Click **Run**. The result should be 256 × 256.

### Step 3 (optional): Make the mask open in colour

**Why is it black and white?** The file stores only the numbers 1 to 8, not colours. QGIS shows colours because of a style you applied. Other programs show the numbers as shades of grey, and Windows Photos looks almost black. The file is fine, and this is the right format for training a model.

**Option A: Add colours inside the file** (still works for training)

1. In QGIS, right-click the mask layer > **Remove Layer**. Otherwise the file is locked.
2. Open **Plugins > Python Console**, paste the code below, change the path, and press Enter.

```python
from osgeo import gdal

path = r'C:\path\to\mask_2019_51.tif'   # change to your file

COLORS = {1:(128,0,0), 2:(0,255,36), 3:(148,148,148), 4:(255,255,255),
          5:(34,97,38), 6:(0,69,255), 7:(75,181,73), 8:(222,31,7)}

ds = gdal.Open(path, gdal.GA_Update)
band = ds.GetRasterBand(1)
table = gdal.ColorTable()
for value, (r, g, b) in COLORS.items():
    table.SetColorEntry(value, (r, g, b, 255))
band.SetRasterColorTable(table)
band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)
ds = None
print('done')
```

### Why the edges look like stairs

The mask has the same 256 × 256 pixels as the satellite image, and each pixel can hold only one class. Edges therefore follow the pixel grid. This is correct, because the mask must line up with the image pixel by pixel. For a smooth picture in a report, use **Project > Import/Export > Export Map to Image** from the polygon layer `labels_2019` at 300 dpi.

---

## Part 2: Find the percentage of each class in an image

One pixel = 10 × 10 m = 100 m². One chip = 65,536 pixels (about 655 hectares).

### Method 1: One image, in QGIS

1. Open the **Processing Toolbox**, search **Raster layer unique values report**, and double-click it.
2. Set **Input layer** to the mask, for example `mask_2019_51`, and click **Run**.
3. Click the HTML link in the results. You get a table with each value, its pixel count and its area in m².
4. Percentage = pixel count ÷ 65,536 × 100.

### Method 2: Many images at once, into Excel

This makes `class_percent.xlsx` with one row per image and one column per class. It also saves a colour PNG of each mask.

**Example result** (made-up numbers):

| image | file | Bareland (%) | Rangeland (%) | Developed space (%) | Road (%) | Tree (%) | Water (%) | Agriculture land (%) | Building (%) |
|---|---|---|---|---|---|---|---|---|---|
| 51 | mask_2019_51 | 25.40 | 10.12 | 5.30 | 2.18 | 30.05 | 1.25 | 24.10 | 1.60 |

- `image` is the chip number at the end of the file name (`mask_2019_51` gives 51).
- Each row adds up to 100.
- The values are plain numbers from 0 to 100. Don't apply Excel's % format to these columns, because Excel would multiply them by 100 again (23.32 becomes 2332%).

**How to run it**

1. Open **Plugins > Python Console** and click **Show Editor**.
2. Paste the code below.
3. Change the two paths:
   - `INPUT`: a folder of mask `.tif` files, or one `.tif` file
   - `OUTDIR`: where the results go. It is created if it doesn't exist.
4. Click **Run**. The console prints a summary for each image and ends with `done`.

```python
import os, glob, re, csv
import numpy as np
from osgeo import gdal

INPUT  = r'C:\path\to\masks'         # a folder of mask .tif files, or one .tif file
OUTDIR = r'C:\path\to\mask_report'   # results are saved here

NAMES = {1:'Bareland', 2:'Rangeland', 3:'Developed space', 4:'Road',
         5:'Tree', 6:'Water', 7:'Agriculture land', 8:'Building'}
COLORS = {1:(128,0,0), 2:(0,255,36), 3:(148,148,148), 4:(255,255,255),
          5:(34,97,38), 6:(0,69,255), 7:(75,181,73), 8:(222,31,7)}

lookup = np.zeros((256, 3), np.uint8)
for value, rgb in COLORS.items():
    lookup[value] = rgb

if INPUT.lower().endswith(('.tif', '.tiff')):
    files = [INPUT]
else:
    files = sorted(glob.glob(os.path.join(INPUT, '*.tif')))
os.makedirs(OUTDIR, exist_ok=True)

header = ['image', 'file'] + [NAMES[k] + ' (%)' for k in NAMES]
rows = []

for path in files:
    ds = gdal.Open(path)
    data = ds.ReadAsArray()
    name = os.path.splitext(os.path.basename(path))[0]
    found = re.search(r'(\d+)$', name)
    image = int(found.group(1)) if found else name

    counts = np.bincount(data.ravel(), minlength=9)
    rows.append([image, name] + [round(100 * counts[k] / data.size, 2) for k in NAMES])

    if counts[0] > 0:
        print('WARNING:', name, 'has', counts[0], 'empty pixels. Finish labelling this chip.')

    # colour picture of the mask
    rgb = lookup[np.clip(data, 0, 255)]
    mem = gdal.GetDriverByName('MEM').Create('', data.shape[1], data.shape[0], 3, gdal.GDT_Byte)
    for i in range(3):
        mem.GetRasterBand(i + 1).WriteArray(rgb[:, :, i])
    gdal.GetDriverByName('PNG').CreateCopy(os.path.join(OUTDIR, name + '.png'), mem)
    mem = None
    ds = None

    print(name, ' | '.join('%s %.1f%%' % (NAMES[k], 100 * counts[k] / data.size)
                            for k in NAMES if counts[k]))

# save the table
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = 'class_percent'
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append(row)
    ws.freeze_panes = 'C2'
    wb.save(os.path.join(OUTDIR, 'class_percent.xlsx'))
except ImportError:
    # Excel can open a .csv file too
    with open(os.path.join(OUTDIR, 'class_percent.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

print('done ->', OUTDIR, '|', len(files), 'images')
```

If the console prints a **WARNING** about empty pixels, that chip is not fully labelled yet. Its percentages will add up to less than 100, so finish it before you report any numbers.

To compare years, use the same chips and the same grid for 2019, 2022 and 2025.

---

## Which file is for what

| File | Use |
|---|---|
| `mask_2019.tif` (whole area, values 1 to 8) | Training a model, counting percentages |
| `mask_2019_51.tif` (one chip, 256 × 256) | Training with one chip at a time |
| Same file with colours added (Option A) | Still works for training, and opens in colour |
| `*.png` (Rendered image) | Viewing and reports only |
| `class_percent.xlsx` | Class percentages per image (Method 2) |
| `mask_8class_oem_raster.qml` | Colour style for opening masks in QGIS |
