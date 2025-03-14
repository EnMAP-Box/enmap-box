from enmapboxplugins.colorspaceexplorer import ColorSpaceExplorerWidget

from enmapbox import initAll
from enmapbox.exampledata import enmap
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import QgsRasterLayer

layer = QgsRasterLayer(enmap, 'enmap_berlin.bsq')
reader = RasterReader(layer)

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
mapDock = enmapBox._dropObject(layer)
w = ColorSpaceExplorerWidget(layer, mapDock.mapCanvas())
w.show()

qgsApp.exec_()
