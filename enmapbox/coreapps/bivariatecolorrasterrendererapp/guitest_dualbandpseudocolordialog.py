from qgis.PyQt.QtGui import QColor

from bivariatecolorrasterrendererapp.bivariatecolorrasterrendererdialog import BivariateColorRasterRendererDialog
from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from qgis.core import QgsRasterLayer

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)

case = 1

if case == 1:  # NDFI map from Katja Kowalski
    layer = QgsRasterLayer(r'D:\data\katja_kowalski\NDFI.vrt', 'NDFI')
    mapDock = enmapBox.onDataDropped([layer])

    widget = BivariateColorRasterRendererDialog()
    widget.show()
    widget.mLayer.setLayer(layer)
    widget.mBand1.setBand(1)
    widget.mBand2.setBand(2)
elif case == 2:  # Tree and Water fractions
    layer = QgsRasterLayer(r'D:\source\QGISPlugIns\enmap-box\tests\testdata\raster\fraction_map_l3.tif',
                           'fraction_map_l3')
    mapDock = enmapBox.onDataDropped([layer])
    widget = BivariateColorRasterRendererDialog()
    widget.mBand1.setBand(4)
    widget.mBand2.setBand(6)
    widget.mColor3.setColor(QColor(0, 0, 0))
    widget.mColor1.setColor(QColor(0, 0, 255))
    widget.mColor4.setColor(QColor(0, 255, 0))
    widget.mColor2.setColor(QColor(255, 0, 0))
    widget.show()
    widget.mLayer.setLayer(layer)
else:
    raise ValueError()

qgsApp.exec_()
