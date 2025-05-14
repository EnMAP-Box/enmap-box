from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.qgispluginsupport.qps import registerSpectralLibraryIOs
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.testing import start_app, TestCase
from enmapboxtestdata import landcover_point
from qgis.core import QgsVectorLayer

start_app()
registerSpectralLibraryIOs()


class TestCaseIssue926(TestCase):

    def test_issue926(self):
        layer = QgsVectorLayer(landcover_point)
        tmp = self.createTestOutputDirectory()
        filenameCopy = tmp / 'copy.geojson'
        SpectralLibraryUtils.writeToSource(layer, filenameCopy.as_posix())
        layerCopy = QgsVectorLayer(filenameCopy.as_posix())
        self.assertTrue(layerCopy.isValid())
