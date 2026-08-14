import numpy as np
from qgis._core import QgsVectorLayer

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxtestdata import surfaceLongFormat, surfaceLibrary
from spectralsurfaceplottingapp import SpectralSurfacePlottingWindow

qgsApp = start_app()
initAll()
enmapBox = EnMAPBox()
enmapBox.onDataDropped(
    [
        QgsVectorLayer(surfaceLongFormat, 'surface_long_format.csv'),
        QgsVectorLayer(surfaceLibrary, 'surface_library.geojson')
    ]
)
# enmapBox.ui.setFixedSize(1920 - 2, 1080 - 32)  # for recording 1080p videos with ScreenToGif

#x, y, z = getLmuWeizen()

widget = SpectralSurfacePlottingWindow()
widget.show()
widget.onLoadData()

# enmapBox.openExampleData(mapWindows=2)
# table = QgsVectorLayer(surfaceLongFormat, 'long_format.csv')
# enmapBox.onDataDropped([table])

qgsApp.exec()
