# -*- coding: utf-8 -*-
"""
functions to use GEE within Qgis python script
"""
from enmapbox.utils import importEarthEngine
from qgis.core import QgsRasterLayer

eeImported, ee = importEarthEngine(False)


def addLayer(eeObject, visParams, name, mapCanvas, shown=True, opacity=1.0) -> QgsRasterLayer:
    from geetimeseriesexplorerapp.externals.ee_plugin.utils import add_or_update_ee_layer
    return add_or_update_ee_layer(eeObject, visParams, name, mapCanvas, shown, opacity)


def getBounds(asGeoJSON=False):
    from enmapbox import EnMAPBox
    enmapBox = EnMAPBox.instance()
    ex = enmapBox.currentMapCanvas().extent()
    xmax = ex.xMaximum()
    ymax = ex.yMaximum()
    xmin = ex.xMinimum()
    ymin = ex.yMinimum()

    # return as [west, south, east, north]
    if not asGeoJSON:
        return [xmin, ymin, xmax, ymax]

    # return as geometry
    # crs = iface.mapCanvas().mapSettings().destinationCrs().authid()
    crs = enmapBox.currentMapCanvas().mapSettings().destinationCrs().authid()

    return ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], crs, False)
