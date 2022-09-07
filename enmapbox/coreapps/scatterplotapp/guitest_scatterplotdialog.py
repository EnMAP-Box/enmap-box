from qgis.core import QgsRasterLayer

from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from scatterplotapp.scatterplotdialog import ScatterPlotDialog

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)

layer = QgsRasterLayer(
    r'D:\data\sensors\landsat\C2L2\LC08_L2SP_192023_20210724_20210730_02_T1\LC08_L2SP_192023_20210724_20210730_02_T1_SR.vrt',
    'LC08_L2SP_192023_20210724_20210730_02_T1_SR.vrt'
)

mapDock = enmapBox.onDataDropped([layer])

widget = ScatterPlotDialog(enmapBox.ui)
widget.show()
widget.mLayer.setLayer(layer)
widget.mBandX.setBand(4)
widget.mBandY.setBand(5)

qgsApp.exec_()
