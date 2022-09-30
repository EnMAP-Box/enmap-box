import numpy as np

from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from enmapboxprocessing.driver import Driver
from qgis.core import QgsRasterLayer
from scatterplotapp.scatterplotdialog import ScatterPlotDialog

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)

layer = QgsRasterLayer(
    r'D:\data\sensors\landsat\C2L2\LC08_L2SP_192023_20210724_20210730_02_T1\LC08_L2SP_192023_20210724_20210730_02_T1_SR.vrt',
    'LC08_L2SP_192023_20210724_20210730_02_T1_SR.vrt'
)

# issue #1407
filename = r'D:\source\QGISPlugIns\enmap-box\test-outputs\test3.tif'
Driver(filename).createFromArray(
    np.array([[[1, 2, 3, 4, 5], [11, 12, 13, 14, 15], [21, 22, 23, 24, 25], [31, 32, 33, 34, 35]]])
)
layer = QgsRasterLayer(filename)

mapDock = enmapBox.onDataDropped([layer])

widget = ScatterPlotDialog(enmapBox.ui)
widget.show()
widget.mLayerX.setLayer(layer)
widget.mLayerY.setLayer(layer)
widget.mBandX.setBand(1)
widget.mBandY.setBand(1)

qgsApp.exec_()
