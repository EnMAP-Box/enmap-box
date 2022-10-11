from enmapbox import EnMAPBox, initAll
from enmapbox.gui.widgets.multiplerasterbandselectionwidget.multiplerasterbandselectionwidget import \
    MultipleRasterBandSelectionWidget
from enmapbox.testing import start_app
from enmapboxtestdata import enmap
from qgis._core import QgsRasterLayer

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
#enmapBox.loadExampleData()
widget = MultipleRasterBandSelectionWidget()
layer = QgsRasterLayer(enmap)
widget.mBand.setLayer(layer)
widget.show()

qgsApp.exec_()
