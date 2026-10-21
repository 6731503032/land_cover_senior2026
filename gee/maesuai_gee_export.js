// ============================================================
<<<<<<< HEAD
// Mae Suai (Chiang Rai) - 40 fixed chips x 3 years = 120 images
// Paste into the Google Earth Engine Code Editor and press Run.
// ============================================================

// ---------- SETTINGS ----------
var CENTER = [99.56, 19.65];      // [lon, lat] centre of the chip grid (Mae Suai area). Adjust if needed.
var COLS = 8, ROWS = 5;           // 8 x 5 = 40 chips
var CHIP_PX = 256;                // chip size in pixels
var SCALE = 10;                   // metres per pixel (Sentinel-2)
var CHIP_M = CHIP_PX * SCALE;     // 2,560 m per chip side
var YEARS = [2019, 2022, 2025];
var CS_THRESHOLD = 0.6;           // Cloud Score+ clear threshold (0-1). Higher = stricter.
var CRS = 'EPSG:32647';           // UTM zone 47N
var FOLDER = 'MaeSuai_chips';     // Google Drive folder
var BANDS = ['B2', 'B3', 'B4', 'B8'];   // Blue, Green, Red, NIR
var EXPORT = false;               // set true to create the 120 export tasks (+1 grid file)

// ---------- CHIP GRID (same 40 locations every year) ----------
var c = ee.Geometry.Point(CENTER).transform(CRS, 1).coordinates().getInfo();
var x0 = Math.round((c[0] - COLS * CHIP_M / 2) / SCALE) * SCALE;   // snap to 10 m grid
=======
// Mae Suai (Chiang Rai) - Sentinel-2
// 40 FIXED chips x 3 years = 120 images (same places every year)
// IMPROVED: Cloud Score+, dry season, gap filling, quality check
// Paste into the Google Earth Engine Code Editor and press Run.
// ============================================================

// ---------- 1. SETTINGS ----------
var CENTER = [99.56, 19.65];   // [lon, lat] centre of the grid (Mae Suai)
var COLS = 8, ROWS = 5;        // 8 x 5 = 40 chips
var CHIP_PX = 256;             // pixels per chip side
var SCALE = 10;                // metres per pixel
var CHIP_M = CHIP_PX * SCALE;  // 2,560 m per chip side
var YEARS = [2019, 2022, 2025];
var CS_THRESHOLD = 0.6;        // cloud removal strength (0-1). Higher = stricter
var MIN_VALID = 0.98;          // chips below 98% valid pixels get flagged
var CRS = 'EPSG:32647';        // UTM zone 47N
var FOLDER = 'MaeSuai_chips';  // Google Drive folder
var BANDS = ['B2', 'B3', 'B4', 'B8'];  // Blue, Green, Red, NIR
var EXPORT = false;            // set true to create the export tasks

// ---------- 2. FIXED CHIP GRID (same 40 places every year) ----------
var c = ee.Geometry.Point(CENTER).transform(CRS, 1).coordinates().getInfo();
var x0 = Math.round((c[0] - COLS * CHIP_M / 2) / SCALE) * SCALE;
>>>>>>> a9deb99190232972af47d099a594f3eb4daaa0dd
var y0 = Math.round((c[1] - ROWS * CHIP_M / 2) / SCALE) * SCALE;

var chips = [];
for (var r = 0; r < ROWS; r++) {
  for (var q = 0; q < COLS; q++) {
    var id = r * COLS + q + 1;
    var xa = x0 + q * CHIP_M, ya = y0 + r * CHIP_M;
    chips.push({
      id: id,
      rect: ee.Geometry.Rectangle([xa, ya, xa + CHIP_M, ya + CHIP_M], CRS, false)
    });
  }
}
var aoi = ee.Geometry.Rectangle(
  [x0, y0, x0 + COLS * CHIP_M, y0 + ROWS * CHIP_M], CRS, false);

var gridFc = ee.FeatureCollection(chips.map(function (ch) {
  return ee.Feature(ch.rect, {chip_id: ch.id});
}));

<<<<<<< HEAD
// ---------- CLOUD-FREE COMPOSITES ----------
=======
// ---------- 3. CLOUD-FREE COMPOSITE ----------
>>>>>>> a9deb99190232972af47d099a594f3eb4daaa0dd
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

function composite(start, end) {
  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(aoi)
    .filterDate(start, end)
    .linkCollection(csPlus, ['cs_cdf'])
    .map(function (img) {
<<<<<<< HEAD
      // keep only pixels Cloud Score+ rates as clear (removes cloud, shadow, haze)
      return img.updateMask(img.select('cs_cdf').gte(CS_THRESHOLD)).select(BANDS);
    });
  return {image: col.median().clip(aoi), count: col.size()};
}

// Dry season ending in the given year (Nov of previous year to Feb), fewer clouds
// and before the March-April burning haze. Gaps are filled from a wider window.
function yearComposite(year) {
  var primary = composite((year - 1) + '-11-01', year + '-03-01');
  var wide = composite((year - 1) + '-10-01', year + '-04-15');
  var img = primary.image.unmask(wide.image)
    .clamp(0, 10000).toUint16();
  return {image: img, count: primary.count};
}

// ---------- DISPLAY ----------
Map.centerObject(aoi, 11);
var vis = {bands: ['B4', 'B3', 'B2'], min: 0, max: 3000};
var composites = {};
=======
      // keep only pixels Cloud Score+ says are clear (no cloud, shadow, haze)
      return img.updateMask(img.select('cs_cdf').gte(CS_THRESHOLD)).select(BANDS);
    });
  return {image: col.median(), count: col.size()};
}

// Step A: dry season (Nov to Feb) = fewest clouds, before burning smoke
// Step B: wider window fills the remaining holes
// Step C: even wider window fills any last holes
function yearComposite(year) {
  var a = composite((year - 1) + '-11-01', year + '-03-01');
  var b = composite((year - 1) + '-10-01', year + '-04-15');
  var d = composite((year - 1) + '-10-01', year + '-06-01');
  var img = a.image.unmask(b.image).unmask(d.image)
    .clamp(0, 10000).toUint16().clip(aoi);
  return {image: img, rawImage: a.image, count: a.count};
}

// ---------- 4. DISPLAY ----------
Map.centerObject(aoi, 11);
var vis = {bands: ['B4', 'B3', 'B2'], min: 0, max: 3000};
var composites = {};
var qualityList = [];

>>>>>>> a9deb99190232972af47d099a594f3eb4daaa0dd
YEARS.forEach(function (y) {
  var res = yearComposite(y);
  composites[y] = res.image;
  Map.addLayer(res.image, vis, 'Mae Suai ' + y, y === YEARS[0]);
<<<<<<< HEAD
  print('Scenes used in main window, ' + y, res.count);
});
Map.addLayer(gridFc.style({color: 'yellow', fillColor: '00000000', width: 1}), {}, '40 chips');

// ---------- EXPORT: 40 chips x 3 years = 120 GeoTIFFs ----------
=======
  print('Scenes used in dry season, ' + y, res.count);

  // ---------- 5. QUALITY CHECK (share of valid pixels per chip) ----------
  var validImg = res.image.select('B4').mask().rename('valid');
  var q = validImg.reduceRegions({
    collection: gridFc,
    reducer: ee.Reducer.mean(),
    scale: SCALE,
    crs: CRS
  }).map(function (f) {
    return f.set('year', y);
  });
  qualityList.push(q);

  var bad = q.filter(ee.Filter.lt('valid', MIN_VALID));
  print('Chips below ' + (MIN_VALID * 100) + '% valid, ' + y + ' (chip ids):',
    bad.aggregate_array('chip_id'));
});

var quality = ee.FeatureCollection(qualityList).flatten();

Map.addLayer(gridFc.style({color: 'yellow', fillColor: '00000000', width: 1}),
  {}, '40 chips');

// ---------- 6. EXPORT ----------
>>>>>>> a9deb99190232972af47d099a594f3eb4daaa0dd
if (EXPORT) {
  YEARS.forEach(function (y) {
    chips.forEach(function (ch) {
      var idStr = ('0' + ch.id).slice(-2);
      Export.image.toDrive({
        image: composites[y],
        description: 'maesuai_' + y + '_chip' + idStr,
        folder: FOLDER,
        fileNamePrefix: 'maesuai_' + y + '_chip' + idStr,
        region: ch.rect,
        crs: CRS,
        scale: SCALE,
        maxPixels: 1e8,
        fileFormat: 'GeoTIFF'
      });
    });
  });
<<<<<<< HEAD
  // chip footprints, so each image can be located later
=======

  // chip locations
>>>>>>> a9deb99190232972af47d099a594f3eb4daaa0dd
  Export.table.toDrive({
    collection: gridFc,
    description: 'maesuai_chip_grid',
    folder: FOLDER,
    fileFormat: 'GeoJSON'
  });
<<<<<<< HEAD
=======

  // quality report: valid pixel share for every chip and year
  Export.table.toDrive({
    collection: quality.select(['chip_id', 'year', 'valid']),
    description: 'maesuai_chip_quality',
    folder: FOLDER,
    fileFormat: 'CSV'
  });
>>>>>>> a9deb99190232972af47d099a594f3eb4daaa0dd
}
