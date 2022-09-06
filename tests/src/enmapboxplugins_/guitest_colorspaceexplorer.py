from qgis.core import QgsRasterLayer

from enmapbox.exampledata import enmap
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxplugins.colorspaceexplorer import ColorSpaceExplorerWidget
from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app


layer = QgsRasterLayer(enmap, 'enmap_berlin.bsq')
reader = RasterReader(layer)

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
mapDock = enmapBox._dropObject(layer)
w = ColorSpaceExplorerWidget(layer, mapDock.mapCanvas())
w.show()

qgsApp.exec_()
