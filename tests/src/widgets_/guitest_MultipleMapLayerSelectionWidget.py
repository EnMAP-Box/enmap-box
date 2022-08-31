from enmapbox import EnMAPBox, initAll
from enmapbox.gui.widgets.multiplemaplayerselectionwidget import MultipleMapLayerSelectionWidget
from enmapbox.testing import start_app, TestCase

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
enmapBox.loadExampleData()
widget = MultipleMapLayerSelectionWidget()
widget.show()
if not TestCase.runsInCI():
    qgsApp.exec_()
