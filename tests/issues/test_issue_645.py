from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog
from enmapbox.testing import TestObjects
from enmapboxprocessing.testcase import TestCase
from tests.enmapboxtestdata import library_berlin
from qgis.core import QgsVectorLayer


class Issue645Tests(TestCase):

    def test_issue647(self):
        initAll()
        n_bands = [256]
        n_features = 20
        speclib = TestObjects.createSpectralLibrary(n=n_features, n_bands=n_bands)
        speclib: QgsVectorLayer
        speclib.startEditing()
        procw = SpectralProcessingDialog(speclib=speclib)
        procw.setAlgorithm('enmapbox:SpectralResamplingToWavelength')
        self.showGui(procw)

    def test_issue_645(self):

        initAll()
        sl = QgsVectorLayer(library_berlin)
        sl.startEditing()
        d = SpectralProcessingDialog(speclib=sl)
        d.setAlgorithm('enmapbox:TranslateRasterLayer')
        self.showGui(d)
