"""
This is a template to create an EnMAP-Box test
"""
import platform
import sys
import unittest

from qgis.PyQt.QtCore import QObject, pyqtSignal

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.datasources.datasources import VectorDataSource
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapbox.testing import EnMAPBoxTestCase
from qgis.PyQt import Qt
from qgis.core import Qgis


class ExampleClass(QObject):
    sigCurrentLocationChanged = pyqtSignal([object],
                                           [object, MapCanvas])

    def __init__(self):
        super(ExampleClass, self).__init__()

        print()


class TestIssue243Examples(EnMAPBoxTestCase):

    def test_print_system_info(self):
        Qgis.QGIS_DEV_VERSION
        print(f'QGIS: {Qgis.version()}')
        print(f'Qt: {Qt.QT_VERSION_STR}')
        print(f'PyQt: {Qt.PYQT_VERSION_STR}')
        print(f'Python: {sys.version}')
        print(f'Platform: {platform.platform()}')

    def test_Issue243(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)

        # sigSpectralLibraryAdded = pyqtSignal([str], [VectorDataSource])
        print(enmapBox.sigSpectralLibraryAdded.signal)
        print(enmapBox.sigSpectralLibraryAdded[str].signal)
        print(enmapBox.sigSpectralLibraryAdded[VectorDataSource].signal)

        print(enmapBox.sigCurrentLocationChanged.signal)
        print(enmapBox.sigCurrentLocationChanged[object].signal)
        print(enmapBox.sigCurrentLocationChanged[object, MapCanvas].signal)

        enmapBox.loadExampleData()
        enmapBox.createNewMapCanvas('2nd Map')
        c1, c2 = enmapBox.mapCanvases()

        pt = SpatialPoint.fromMapCanvasCenter(c1)
        self.assertIsInstance(pt, SpatialPoint)
        enmapBox.setCurrentLocation(pt, mapCanvas=c1)
        self.showGui(enmapBox.ui)


if __name__ == '__main__':
    unittest.main(buffer=False)
