from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
import os

os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu-compositing"

qgsApp = start_app()

darkMode = False
if darkMode:
    qgsApp.setStyle('Fusion')
    qgsApp.setUITheme('Night Mapping')

initAll()
enmapBox = EnMAPBox()

# enmapBox.ui.setFixedSize(1920 - 2, 1080 - 32)  # for recording 1080p videos with ScreenToGif

enmapBox.openExampleData(mapWindows=2)
qgsApp.exec()
