from qgis.core import QgsRasterLayer

from classfractionstatisticsapp.classfractionstatisticsdialog import ClassFractionStatisticsDialog
from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from enmapboxtestdata import fraction_map_l3, landcover_map_l3

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
layer = QgsRasterLayer(fraction_map_l3, 'fraction_map_l3.tif')
layer2 = QgsRasterLayer(landcover_map_l3, 'landcover_map_l3.tif')
mapDock = enmapBox.onDataDropped([layer2, layer])

widget = ClassFractionStatisticsDialog()
widget.show()
widget.mLayer.setLayer(layer)

qgsApp.exec_()
