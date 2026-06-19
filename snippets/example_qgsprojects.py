from qgis.PyQt.QtWidgets import QApplication

from enmapbox.testing import TestObjects, start_app
from qgis.gui import QgsMapCanvas
from qgis.core import QgsProject

app = start_app()
lyr = TestObjects.createRasterLayer()


def onWillBeDeleted():
    print('Warning: Will be deleted')


lyr.willBeDeleted.connect(onWillBeDeleted)

A = QgsProject()
A.setTitle('P1')

B = QgsProject()
B.setTitle('P2')

c = QgsMapCanvas()
c.setLayers([lyr])
c.zoomToFullExtent()

assert lyr.project() is None  # nosec
A.addMapLayer(lyr, False)
assert lyr.project() == A  # nosec
assert lyr in A.layerStore().mapLayers().values()  # nosec
assert lyr not in B.layerStore().mapLayers().values()  # nosec

B.layerStore().addMapLayer(lyr)
lyr.setParent(A.layerStore())

assert lyr in B.layerStore().mapLayers().values()  # nosec
assert lyr in B.mapLayers().values()  # nosec
assert lyr.project() == A  # nosec
B.takeMapLayer(lyr)
s = ""

if True:
    A.removeAllMapLayers()

    print(lyr in A.mapLayers().values())
    print(lyr in B.mapLayers().values())
    del A
else:
    del A, B
QApplication.processEvents()
c.show()
QApplication.processEvents()
app.exec_()
print('Done')
