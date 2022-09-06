from qgis.core import QgsRasterLayer

from decorrelationstretchapp import DecorrelationStretchDialog
from enmapbox import EnMAPBox, initAll
from enmapbox.exampledata import enmap
from enmapbox.testing import start_app

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
layer = QgsRasterLayer(enmap, 'enmap_berlin.bsq')
mapDock = enmapBox.onDataDropped([layer])

widget = DecorrelationStretchDialog()
widget.show()
widget.mLayer.setLayer(layer)

qgsApp.exec_()
