from enmapbox.gui.enmapboxgui import EnMAPBox

from enmapbox.testing import start_app

qgsApp = start_app()

enmapBox = EnMAPBox()
# enmapBox.ui.setFixedSize(1920 - 2, 1080 - 32)  # for recording 1080p videos with ScreenToGif

enmapBox.openExampleData()
qgsApp.exec_()
