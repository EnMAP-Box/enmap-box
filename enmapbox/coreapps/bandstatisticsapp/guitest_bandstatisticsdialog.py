from qgis.core import QgsRasterLayer

from bandstatisticsapp.bandstatisticsdialog import BandStatisticsDialog
from enmapbox import EnMAPBox, initAll
from enmapbox.exampledata import enmap
from enmapbox.testing import start_app

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
layer = QgsRasterLayer(enmap, 'enmap_berlin.bsq')
mapDock = enmapBox.onDataDropped([layer])

widget = BandStatisticsDialog()
widget.show()
widget.mLayer.setLayer(layer)
widget.mAddRendererBands.click()

qgsApp.exec_()
