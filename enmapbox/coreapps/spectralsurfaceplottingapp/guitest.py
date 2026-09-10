from qgis.core import QgsRasterLayer, QgsVectorLayer

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxtestdata import surfaceLongFormat
from spectralsurfaceplottingapp.spectralsurfaceplottingwindow import SpectralSurfacePlottingWindow

qgsApp = start_app()
initAll()
enmapBox = EnMAPBox()
filenameCollection = r'D:\data\timeseries\EnMAP_Namibia_TS\EnMAP_Namibia_X0080_Y0317.geojson'
filenameExampleRaster = r'D:\data\timeseries\EnMAP_Namibia_TS\X0080_Y0317\ENMAPL2A_20250124_SPECTRAL_IMAGE_MASKED.TIF'
enmapBox.onDataDropped(
    [
        QgsVectorLayer(surfaceLongFormat, 'surface_long_format.csv'),
        # QgsVectorLayer(surfaceLibrary, 'surface_library.geojson'),
        QgsVectorLayer(filenameCollection, 'raster_collection.geojson'),
        #        QgsRasterLayer(filenameExampleRaster, 'ENMAPL2A_20250124_SPECTRAL_IMAGE_MASKED.TIF')
    ]
)
enmapBox.onDataDropped(
    [
        QgsRasterLayer(filenameExampleRaster, 'ENMAPL2A_20250124_SPECTRAL_IMAGE_MASKED.TIF')
    ]
)

# enmapBox.ui.setFixedSize(1920 - 2, 1080 - 32)  # for recording 1080p videos with ScreenToGif

# x, y, z = getLmuWeizen()

widget = SpectralSurfacePlottingWindow()
widget.show()
widget.onLoadData()

# enmapBox.openExampleData(mapWindows=2)
# table = QgsVectorLayer(surfaceLongFormat, 'long_format.csv')
# enmapBox.onDataDropped([table])

qgsApp.exec()
