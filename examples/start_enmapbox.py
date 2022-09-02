
from enmapbox import EnMAPBox

from enmapbox.testing import start_app

qgsApp = start_app()

enmapBox = EnMAPBox()

enmapBox.openExampleData()
qgsApp.exec_()
