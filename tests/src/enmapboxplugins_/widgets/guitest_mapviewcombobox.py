from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from enmapboxplugins.widgets.mapviewcombobox import MapViewComboBox

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)

widget = MapViewComboBox()
widget.show()

qgsApp.exec_()
