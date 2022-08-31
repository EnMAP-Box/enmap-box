

from osgeo import gdal
from qgis._gui import QgsRasterLayerProperties, QgsMapCanvas

from enmapbox import EnMAPBox, initAll
from enmapbox.exampledata import enmap
from enmapbox.qgispluginsupport.qps.qgsrasterlayerproperties import QgsRasterLayerSpectralProperties
from enmapbox.testing import start_app
from enmapboxprocessing.rasterwriter import RasterWriter
from qgis._core import QgsRasterLayer


qgsApp = start_app()
initAll()

# create raster with a bad band
filename = 'enmap.vrt'
ds = gdal.Translate(filename, enmap)
writer = RasterWriter(ds)
for bandNo in range(1, 101):
    writer.setBadBandMultiplier(0, 2)
del writer, ds
layer = QgsRasterLayer(filename)

if False:
    c = QgsMapCanvas()
    d = QgsRasterLayerProperties(layer, c)
    d.exec_()

props = QgsRasterLayerSpectralProperties.fromRasterLayer(layer)

enmapBox = EnMAPBox(load_other_apps=False)
enmapBox.onDataDropped([layer])
qgsApp.exec_()