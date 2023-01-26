from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.widgets.multiplemaplayerselectionwidget.multiplemaplayerselectionwidget import \
    MultipleMapLayerSelectionWidget
from enmapbox.testing import start_app

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
enmapBox.loadExampleData()
widget = MultipleMapLayerSelectionWidget()
widget.show()

qgsApp.exec_()
