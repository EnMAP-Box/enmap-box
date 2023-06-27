from os.path import abspath

import numpy as np

from enmapbox.testing import start_app
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.utils import Utils
from qgis.core import QgsRasterLayer, QgsRectangle, QgsRasterDataProvider, QgsRasterRenderer

qgsApp = start_app()

layer = QgsRasterLayer(
    r'contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&featureCount=10&format=image/png&layers=bb_dop20cir&styles&url=https://isk.geobasis-bb.de/mapproxy/dop20cir/service/wms',
    'x', 'wms')
provider: QgsRasterDataProvider = layer.dataProvider()
renderer: QgsRasterRenderer = layer.renderer()
res = 1
size = 9000
xmin = 1448000
ymin = 6868000
extent = QgsRectangle(xmin, ymin, xmin + res * size, ymin + res * size)

block = renderer.block(1, extent, 9000, 9000)
array = Utils().qgsRasterBlockToNumpyArray(block)

a = np.bitwise_and(array >> 24, 255)
r = np.bitwise_and(array >> 16, 255)
g = np.bitwise_and(array >> 8, 255)
b = np.bitwise_and(array, 255)

Driver(abspath('test2.tif')).createFromArray(np.array([r, g, b], np.uint8), extent, layer.crs())
