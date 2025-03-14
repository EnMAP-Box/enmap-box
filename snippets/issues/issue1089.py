from osgeo import gdal
from enmapbox.exampledata import enmap
from enmapbox.testing import start_app
from enmapboxprocessing.rasterwriter import RasterWriter
from qgis.core import QgsRasterLayer

qgsApp = start_app()

# create raster with a bad band
filename = 'enmap.vrt'
ds = gdal.Translate(filename, enmap)
writer = RasterWriter(ds)
for bandNo in range(1, 101):
    writer.setBadBandMultiplier(0, bandNo)
    writer.setFwhm(42, bandNo)
writer.close()
del writer, ds
layer = QgsRasterLayer(filename, 'enmap.vrt')


if True:
    from enmapbox.qgispluginsupport.qps.layerproperties import showLayerPropertiesDialog
    showLayerPropertiesDialog(layer)
else:
    from enmapbox.gui.enmapboxgui import EnMAPBox
    enmapBox = EnMAPBox(load_other_apps=False)
    enmapBox.onDataDropped([layer])
qgsApp.exec_()
