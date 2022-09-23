"""
How to load raster and vector data into a QgsMapCanvas and make a screenshot from
"""

import os

from qgis.PyQt.QtWidgets import QWidget, QApplication
from enmapbox.exampledata import enmap, landcover_polygon
from enmapbox.testing import start_app
import time

from qgis.core import QgsRasterLayer, QgsMultiBandColorRenderer, QgsVectorLayer, QgsProject
from qgis.gui import QgsMapCanvas


def widgetScreenshot(widget, path):
    assert isinstance(widget, QWidget)

    rect = widget.rect()
    pixmap = widget.grab(rectangle=rect)
    pixmap.save(path, quality=100)


APP = start_app()

lyr1 = QgsRasterLayer(enmap)

renderer = lyr1.renderer()
assert isinstance(renderer, QgsMultiBandColorRenderer)
renderer.setRedBand(1)
renderer.setBlueBand(2)
renderer.setGreenBand(3)

renderer.redContrastEnhancement().setMinimumValue(0)
renderer.redContrastEnhancement().setMaximumValue(2000)

lyr2 = QgsVectorLayer(landcover_polygon)
assert lyr1.isValid()
assert lyr2.isValid()
layers = [lyr1, lyr2]
QgsProject.instance().addMapLayers(layers)

canvas = QgsMapCanvas()
canvas.setLayers(layers)
canvas.setExtent(canvas.fullExtent())
canvas.setDestinationCrs(lyr1.crs())
canvas.waitWhileRendering()

print('Completed')
dn = os.path.dirname(__file__)
filepath1 = os.path.join(dn, 'myimage12.png')
filepath2 = os.path.join(dn, 'myimage22.png')
QApplication.processEvents()
canvas.saveAsImage(filepath1)
widgetScreenshot(canvas, filepath2)

time.sleep(5)
