# ============================================================
# QGIS setup for polygon labelling of ONE chip (all 3 years)
# Run in QGIS:  Plugins > Python Console > Show Editor (icon) > Open this file > Run
# Edit the SETTINGS below first (class list is already set to the 8 OpenEarthMap classes). For the next chip, change CHIP_ID and run again.
# ============================================================
import os
from qgis.core import (
    QgsProject, QgsRasterLayer, QgsVectorLayer, QgsCoordinateReferenceSystem,
    QgsMultiBandColorRenderer, QgsContrastEnhancement, QgsBilinearRasterResampler,
    QgsVectorFileWriter, QgsDefaultValue, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsFillSymbol, QgsSnappingConfig, QgsEditorWidgetSetup,
)
from qgis.utils import iface

# ---------- SETTINGS (edit these) ----------
ROOT = r"C:\Users\SE\Downloads"            # folder that contains MaeSuai_2019, MaeSuai_2022, MaeSuai_2025 (labels are saved here too)
CHIP_ID = 51                               # chip number to label now
YEARS = [2019, 2022, 2025]
# ONE-IMAGE TEST: set SINGLE_FILE to one .tif and SINGLE_YEAR to the year that image is from.
# Set SINGLE_FILE = None to use the three year folders instead.
SINGLE_FILE = r"C:\Users\SE\Downloads\51.tif"
SINGLE_YEAR = 2019                         # CHANGE to the real year of 51.tif
LABELLER = "your_name"                     # saved in the 'labeller' column
LABEL_DIR = os.path.join(ROOT, "labels")   # labels_2019.gpkg etc. are created here
STRETCH_MAX = 3000                         # same fixed contrast for every year (matches the GEE preview)
MIN_AREA_M2 = 900                          # 3 x 3 pixels at 10 m
SHOW_FALSE_COLOUR = True                   # also add NIR-Red-Green view (hidden by default)
CRS = "EPSG:32647"

# Classes and colours from the table you gave (OpenEarthMap's 8 classes, same HEX colours).
# The table has no ids, so the ids 1-8 follow the table's row order. 0 is kept free for "not labelled".
# id: (name, colour)
CLASSES = {
    1: ("Bareland", "#800000"),
    2: ("Rangeland", "#00FF24"),
    3: ("Developed space", "#949494"),
    4: ("Road", "#FFFFFF"),
    5: ("Tree", "#226126"),
    6: ("Water", "#0045FF"),
    7: ("Agriculture land", "#4BB549"),
    8: ("Building", "#DE1F07"),
}
# -------------------------------------------

project = QgsProject.instance()


def chip_path(year):
    if SINGLE_FILE:
        return SINGLE_FILE
    return os.path.join(ROOT, "MaeSuai_%d" % year, "%d.tif" % CHIP_ID)


def apply_colour(layer, r, g, b):
    """Show bands r,g,b with the same fixed 0..STRETCH_MAX stretch (comparable across years)."""
    prov = layer.dataProvider()

    def enhancement(band):
        ce = QgsContrastEnhancement(prov.dataType(band))
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
        ce.setMinimumValue(0)
        ce.setMaximumValue(STRETCH_MAX)
        return ce

    rend = QgsMultiBandColorRenderer(prov, r, g, b)
    rend.setRedContrastEnhancement(enhancement(r))
    rend.setGreenContrastEnhancement(enhancement(g))
    rend.setBlueContrastEnhancement(enhancement(b))
    layer.setRenderer(rend)
    try:  # smoother look when zoomed in (display only, data unchanged)
        layer.resampleFilter().setZoomedInResampler(QgsBilinearRasterResampler())
    except Exception as e:
        print("Bilinear resampling not set (set it by hand in Symbology > Resampling):", e)
    layer.triggerRepaint()


def make_label_layer(year):
    os.makedirs(LABEL_DIR, exist_ok=True)
    gpkg = os.path.join(LABEL_DIR, "labels_%d.gpkg" % year)
    if not os.path.exists(gpkg):
        mem = QgsVectorLayer(
            "Polygon?crs=%s&field=class_id:integer&field=chip_id:integer"
            "&field=year:integer&field=labeller:string(40)" % CRS, "labels", "memory")
        try:
            opts = QgsVectorFileWriter.SaveVectorOptions()
            opts.driverName = "GPKG"
            opts.layerName = "labels"
            res = QgsVectorFileWriter.writeAsVectorFormatV3(
                mem, gpkg, project.transformContext(), opts)
        except AttributeError:  # older QGIS
            res = QgsVectorFileWriter.writeAsVectorFormat(mem, gpkg, "utf-8", mem.crs(), "GPKG")
        err = res[0] if isinstance(res, tuple) else res
        if err != 0:
            print("Could not create", gpkg, "error code", err)
    layer = QgsVectorLayer("%s|layername=labels" % gpkg, "labels_%d" % year, "ogr")
    if not layer.isValid():
        print("Label layer not valid:", gpkg)
        return None

    # auto-fill chip_id, year, labeller for every new polygon
    f = layer.fields()
    layer.setDefaultValueDefinition(f.indexOf("chip_id"), QgsDefaultValue(str(CHIP_ID)))
    layer.setDefaultValueDefinition(f.indexOf("year"), QgsDefaultValue(str(year)))
    layer.setDefaultValueDefinition(f.indexOf("labeller"), QgsDefaultValue("'%s'" % LABELLER))

    # dropdown with class names for class_id
    try:
        value_map = [{"%d %s" % (cid, name): cid} for cid, (name, _) in CLASSES.items()]
        layer.setEditorWidgetSetup(
            f.indexOf("class_id"), QgsEditorWidgetSetup("ValueMap", {"map": value_map}))
    except Exception as e:
        print("Class dropdown not set (type the class_id by hand):", e)

    # colour polygons by class, 50% transparent
    cats = []
    for cid, (name, colour) in CLASSES.items():
        sym = QgsFillSymbol.createSimple(
            {"color": colour, "outline_color": "#000000", "outline_width": "0.2"})
        sym.setOpacity(0.5)
        cats.append(QgsRendererCategory(cid, sym, "%d %s" % (cid, name)))
    layer.setRenderer(QgsCategorizedSymbolRenderer("class_id", cats))
    return layer


def setup_editing():
    project.setTopologicalEditing(True)
    try:
        project.setAvoidIntersectionsMode(
            QgsProject.AvoidIntersectionsMode.AvoidIntersectionsCurrentLayer)
    except AttributeError:
        project.setAvoidIntersectionsMode(QgsProject.AvoidIntersectionsCurrentLayer)
    except Exception as e:
        print("Set 'avoid overlap on active layer' by hand in Project > Snapping Options:", e)
    try:
        cfg = project.snappingConfig()
        cfg.setEnabled(True)
        cfg.setTypeFlag(QgsSnappingConfig.VertexFlag | QgsSnappingConfig.SegmentFlag)
        project.setSnappingConfig(cfg)
    except Exception as e:
        print("Turn on snapping by hand in Project > Snapping Options:", e)


def select_small(year):
    """Select polygons of this chip smaller than MIN_AREA_M2 (then use 'Eliminate selected polygons')."""
    layers = project.mapLayersByName("labels_%d" % year)
    if not layers:
        print("No layer labels_%d" % year)
        return
    layers[0].selectByExpression(
        'area($geometry) < %d AND "chip_id" = %d' % (MIN_AREA_M2, CHIP_ID))
    print("Selected %d small polygons in labels_%d" % (layers[0].selectedFeatureCount(), year))


def main():
    project.clear()
    project.setCrs(QgsCoordinateReferenceSystem(CRS))
    root = project.layerTreeRoot()
    first_extent = None
    years = [SINGLE_YEAR] if SINGLE_FILE else YEARS
    for i, year in enumerate(years):
        group = root.addGroup("%d  chip %d" % (year, CHIP_ID))
        path = chip_path(year)
        if not os.path.exists(path):
            print("MISSING:", path)
            continue
        views = [("RGB", (1, 2, 3))]          # file band order: B4, B3, B2, B8
        if SHOW_FALSE_COLOUR:
            views.append(("NIR", (4, 1, 2)))  # NIR, Red, Green
        for tag, (r, g, b) in views:
            rl = QgsRasterLayer(path, "%d_chip%d_%s" % (year, CHIP_ID, tag))
            if not rl.isValid() or rl.bandCount() < max(r, g, b):
                print("Problem with", path, "(bands:", rl.bandCount(), ")")
                continue
            apply_colour(rl, r, g, b)
            project.addMapLayer(rl, False)
            node = group.addLayer(rl)
            node.setItemVisibilityChecked(tag == "RGB")
            if first_extent is None:
                first_extent = rl.extent()
        ll = make_label_layer(year)
        if ll is not None:
            project.addMapLayer(ll, False)
            group.insertLayer(0, ll)           # labels on top of the imagery
        group.setItemVisibilityChecked(i == 0)  # only the first year visible; tick others to switch
        group.setExpanded(i == 0)
    setup_editing()
    if first_extent is not None:
        iface.mapCanvas().setExtent(first_extent)
        iface.mapCanvas().refresh()
    out = os.path.join(ROOT, "chip%d.qgz" % CHIP_ID)
    project.write(out)
    print("Done. Project saved to", out)
    print("Next: select labels_<year> in the Layers panel > Toggle Editing > Add Polygon Feature.")


main()
