from os.path import abspath

import numpy as np

from enmapbox.testing import start_app
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.utils import Utils
from qgis.core import QgsRasterLayer, QgsRectangle, QgsRasterDataProvider, QgsRasterRenderer

qgsApp = start_app()

layer1 = QgsRasterLayer(
    r'contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&featureCount=10&format=image/png&layers=bb_dop20cir&styles&url=https://isk.geobasis-bb.de/mapproxy/dop20cir/service/wms',
    'x1', 'wms'
)
layer2 = QgsRasterLayer(
    r'contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&featureCount=10&format=image/png&layers=bebb_dop20c&styles&url=https://isk.geobasis-bb.de/mapproxy/dop20c_wmts/service',
    'x2', 'wms'
)
provider1: QgsRasterDataProvider = layer1.dataProvider()
provider2: QgsRasterDataProvider = layer2.dataProvider()
renderer1: QgsRasterRenderer = layer1.renderer()
renderer2: QgsRasterRenderer = layer2.renderer()
res = 1
size = 9000
xmin = 1448000
ymin = 6868000
extent = QgsRectangle(xmin, ymin, xmin + res * size, ymin + res * size)
array1 = Utils().qgsRasterBlockToNumpyArray(renderer1.block(1, extent, size, size))
array2 = Utils().qgsRasterBlockToNumpyArray(renderer2.block(1, extent, size, size))
a1 = np.bitwise_and(array1 >> 24, 255)
r1 = np.bitwise_and(array1 >> 16, 255)
g1 = np.bitwise_and(array1 >> 8, 255)
b1 = np.bitwise_and(array1, 255)
a2 = np.bitwise_and(array2 >> 24, 255)
r2 = np.bitwise_and(array2 >> 16, 255)
g2 = np.bitwise_and(array2 >> 8, 255)
b2 = np.bitwise_and(array2, 255)

blue, green, red, nir = b2, g2, r2, r1
Driver(abspath('test4.tif')).createFromArray(np.array([blue, green, red, nir], np.uint8), extent, layer1.crs())
