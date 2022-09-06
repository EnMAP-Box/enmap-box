import numpy as np
from qgis.core import QgsRasterLayer

from enmapbox import EnMAPBox, initAll
from enmapbox.exampledata import enmap
from enmapbox.testing import start_app
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxplugins.mapviewplugins.spectralsimilarityrenderer import SpectralSimilarityRenderer

layer = QgsRasterLayer(enmap)
reader = RasterReader(layer)
endmembers = np.array([
    # np.array(reader.array(46, 194, 1, 1)).flatten(),  # tree
    np.array(reader.array(37, 186, 1, 1)).flatten()  # water
])

renderer = SpectralSimilarityRenderer()
renderer.setEndmembers(endmembers)
renderer.setMinimumValue(0)
renderer.setMaximumValue(1000)

layer.setRenderer(renderer)

renderer.block(0, layer.extent(), width=layer.width(), height=layer.height())

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
enmapBox._dropObject(layer)

qgsApp.exec_()
