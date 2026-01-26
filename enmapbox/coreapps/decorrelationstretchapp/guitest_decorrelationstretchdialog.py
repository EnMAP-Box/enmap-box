from decorrelationstretchapp import DecorrelationStretchDialog
from enmapbox import initAll
from enmapbox.exampledata import enmap
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from qgis.core import QgsRasterLayer

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
layer = QgsRasterLayer(enmap, 'enmap_berlin.bsq')
mapDock = enmapBox.onDataDropped([layer])

widget = DecorrelationStretchDialog()
widget.show()
widget.mLayer.setLayer(layer)

qgsApp.exec_()
