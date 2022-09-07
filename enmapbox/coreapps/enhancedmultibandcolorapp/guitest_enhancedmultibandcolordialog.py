from enhancedmultibandcolorapp.enhancedmultibandcolordialog import EnhancedMultiBandColorDialog
from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from qgis.core import QgsRasterLayer

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
# layer = QgsRasterLayer(r'C:\Users\Andreas\Downloads\enmap_vi.tif', 'enmap_vi.tif')
layer = QgsRasterLayer(r'C:\Users\Andreas\Downloads\LMUvegetationApps\stack.vrt', 'stack.vrt')

mapDock = enmapBox.onDataDropped([layer])

widget = EnhancedMultiBandColorDialog()
widget.show()
widget.mLayer.setLayer(layer)

qgsApp.exec_()
