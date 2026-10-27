# Labelling rules: Mae Suai land cover (OpenEarthMap 8 classes)

Status: **DRAFT v0.1 for the team to agree on.**
Everything marked **[CONFIRM]** is a proposal, not a decision yet. Once the team agrees, change `[CONFIRM]` to `[AGREED]` and note the date in the change log at the bottom.

Why this file exists: if two people label the same area differently, the model cannot learn consistent classes. Everyone follows the same rules.

---

## 1. What we are labelling

| Item | Value |
|---|---|
| Imagery | Sentinel-2, 10 m per pixel, dry-season composites (Nov to Feb) for 2019, 2022, 2025 |
| Chip size | 256 x 256 pixels = 2.56 km x 2.56 km |
| File names | `MaeSuai_<year>/<chip number>.tif` (the same chip number is the same place in every year) |
| Band order in the file | 1 = Red (B4), 2 = Green (B3), 3 = Blue (B2), 4 = NIR (B8) |
| CRS | EPSG:32647 (UTM 47N) |
| Method | Polygon labelling in QGIS, turned into a pixel mask afterwards |

At 10 m a pixel covers 10 m x 10 m. A single house or a narrow path is smaller than one pixel. We can only label what is visible at this resolution.

## 2. Classes

The 8 classes, names and colours are the ones from the OpenEarthMap paper (Table 2). The IDs 1 to 8 follow the order of that table. 0 means "not labelled". **[CONFIRM]** the IDs must match `src/data/classes.py`.

The OpenEarthMap paper gives written class definitions in its supplement (Section S1, "Land Cover Classes"). The descriptions below adapt them for 10 m imagery and add our own working rules. **[CONFIRM]** them after the agreement test in section 8.

| ID | Class | Colour | Include | Do not include | How it usually looks at 10 m (check on your chip) |
|---|---|---|---|---|---|
| 1 | Bareland | `#800000` | Exposed soil and rock, dry riverbed or sand, cleared land with no crop or buildings | Fields that are in a regular parcel pattern (see Agriculture land), yards and compounds (Developed space) | Tan or brown, bright, little texture. Dull in the NIR view, not red |
| 2 | Rangeland | `#00FF24` | Natural grass, scrub and shrub, open grassy land without a field pattern | Crops, orchards in rows, dense tree cover | Light or yellow-green, smooth. Less red than trees in the NIR view |
| 3 | Developed space | `#949494` | Built-up ground that is not a road or a building: yards, compounds, parking areas, paved or packed surfaces, village area where houses cannot be told apart | Roads, clearly visible buildings | Grey or pale, mixed with small bright spots, often next to roads |
| 4 | Road | `#FFFFFF` | Paved and unpaved roads that you can follow as a continuous line | Footpaths, short lanes you cannot follow, yards | A pale thin line crossing other classes, 1 to 2 pixels wide |
| 5 | Tree | `#226126` | Forest, dense tree cover, tree groves | Open grass, field crops | Dark green, rough texture. Bright red in the NIR view |
| 6 | Water | `#0045FF` | Rivers, streams that are visible as water, ponds, reservoirs (including the Mae Suai dam reservoir) | Wet fields (Agriculture land), shadows | Very dark or black-blue, smooth. Almost no NIR |
| 7 | Agriculture land | `#4BB549` | Cultivated land: fields with regular parcel shapes, rice paddies, crop fields, fallow fields that still show field boundaries | Natural grass without boundaries (Rangeland) | Regular shapes with straight edges. Colour changes between years and seasons |
| 8 | Building | `#DE1F07` | A building or a group of buildings that you can clearly see as bright roof pixels covering at least the minimum size (section 3) | Single roof spots smaller than the minimum size, yards | Small bright or reddish blocks inside a village |

## 3. Rules for everyone

1. **Minimum size: 900 m²** (3 x 3 pixels). Smaller patches are merged into the surrounding class. Do not draw them as separate polygons.
2. **Label what you see in that year's image.** Use the other two years only to help you decide (for example, a field looks different each year, forest does not).
3. **Use the same display settings for every chip and year.** Fixed contrast, maximum `[CONFIRM]` (script setting `STRETCH_MAX`). Use the NIR view for a second look only.
4. **Draw large areas by hand, and keep the outline simple.** Click along the visible edge of an area (for example a forest patch or a lake) to draw its polygon yourself. Use only as many points as you need to follow the edge. Do not add extra points to trace details smaller than one pixel (10 m): the image cannot show them, and they only make the outline messy.
5. **Check other sources when the 10 m image is not clear enough. One pixel is 10 m, so houses, roads and field edges are often too small to see. Look at higher-resolution views, such as Google Earth Pro (use its historical imagery slider) and Esri World Imagery (use Wayback for older dates), then decide the class.
   - Use them only to help you decide. Draw and label on the Sentinel-2 chip.
   - Match the year as closely as you can. The land can change between that image's date and our 2019, 2022 or 2025 composite.
   - Do not copy or export those images into the project. Check their terms of use.
6. **When you are not sure, choose the larger surrounding class**, not a small special case.
7.  **No overlaps and no gaps** between polygons, except where section 4 says so. Snapping, topological editing and avoid overlap must be on.
8. **Every polygon gets a class from the dropdown.** Never leave `class_id` empty. An empty class is not drawn on the map, and it breaks the mask.
9. **Label Water and Tree first.  They are the easiest classes to identify, so draw them first and get them right. Then label the other classes in the gaps, with snapping on so new polygons share edges with the water and tree polygons. Leave the harder classes (Rangeland, Agriculture land, Bareland, Developed space) for last, because you decide them by comparing with their neighbours.
   - Draw only the clear areas first (dark water, dense forest). Leave doubtful edges and mixed areas for the later pass.
   - Mountain shadow can look like water or tree. Use the shadow rule in section 5 and check the other two years.


## 4. Roads

A road is often narrower than one pixel, so we use one fixed rule for the whole project:

- Only label roads you can follow as a continuous line.
- **Option B:** leave roads as the gaps between polygons and fill them as the remaining class after labelling all other 7 classes.

Chosen option: ______ (write A or B here).

Optional idea, not decided: OpenStreetMap road lines can give a first draft of roads. They must be checked against the image.

## 5. Confusing pairs and how we decide **[CONFIRM]**

The OpenEarthMap paper reports these confusions, so expect them in our chips too.

| Confusion | Rule we propose |
|---|---|
| Road vs Developed space (parking lots and surfaces in rural areas look alike) | A continuous line that connects to other roads is Road. A wide flat area is Developed space |
| Rangeland vs Agriculture land vs Tree (similar colours) | Regular parcel shape or straight edges: Agriculture land. Dark and rough: Tree. Light, smooth and irregular: Rangeland. Check the other two years |
| Bareland vs Developed space (a construction site is Developed space in OpenEarthMap, but another dataset calls it Bareland) | Cleared ground with no buildings or paving: Bareland. Ground with a building under construction: Developed space. Decide and write it down |
| Bareland vs harvested Agriculture land (our images are from the dry season, so many fields may look bare) | If it has field boundaries or looks like a field in another year: Agriculture land |
| Orchards and plantations (fruit trees, tea, rubber) | Rows or parcel pattern: Agriculture land. Looks like forest: Tree. **Decide as a team** |
| Shadow in mountain areas (our area has steep terrain) | Label what the ground is, not the shadow. If you cannot tell, ask the team before using a class |

## 6. QGIS settings

YET TO BE CONFIRMED

## 7. Review

- The person who labels a chip does not review it. A second person checks every chip. (The OpenEarthMap authors also used one labeller and at least two checkers per image.)
- Checkers look for: empty classes, gaps, polygons under 900 m², roads that are broken or the wrong width, and classes that do not follow these rules.

## 8. Agreement test (do this before labelling everything)

1. Two people label the same 3 chips alone, using these rules.
2. Make a mask for each person.
3. Compare them pixel by pixel. Record the overall agreement and which classes they disagreed on.
4. Discuss every disagreement and update this file. Repeat with new chips until the team is happy with the agreement. The team decides what "good enough" is: ______ (write the number here).

| Date | Chips | Labellers | Overall agreement | Classes with most disagreement | Rule changes |
|---|---|---|---|---|---|
| | | | | | |

## 9. Change log

| Date | Change | By |
|---|---|---|
| | v0.1 draft | |

---

Sources:
- Class names, colours and annotation process: OpenEarthMap, Xia et al., WACV 2023 (Table 2, Sections 2.2, 3.2 and 6, and Supplement S1), https://openaccess.thecvf.com/content/WACV2023/papers/Xia_OpenEarthMap_A_Benchmark_Dataset_for_Global_High-Resolution_Land_Cover_Mapping_WACV_2023_paper.pdf
- The appearance notes and decision rules are our own working proposals, not from the paper.
