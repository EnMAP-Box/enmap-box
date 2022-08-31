
"""
How to load raster and vector data into a QgsMapCanvas and make a screenshot from
"""

import os
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from enmapbox.testing import initQgisApplication


def widgetScreenshot(widget, path):
    assert isinstance(widget, QWidget)

    rect = widget.rect()
    pixmap = widget.grab(rectangle=rect)
    pixmap.save(path, quality=100)



APP = initQgisApplication()
from qgis.gui import *
from qgis.core import *
from enmapbox.exampledata import enmap, landcover_polygons

lyr1 = QgsRasterLayer(enmap)

renderer = lyr1.renderer()
assert isinstance(renderer, QgsMultiBandColorRenderer)
renderer.setRedBand(1)
renderer.setBlueBand(2)
renderer.setGreenBand(3)

renderer.redContrastEnhancement().setMinimumValue(0)
renderer.redContrastEnhancement().setMaximumValue(2000)

lyr2 = QgsVectorLayer(landcover_polygons)
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

import time
time.sleep(5)


#APP.exec_()