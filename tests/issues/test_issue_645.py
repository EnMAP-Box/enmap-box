from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog
from enmapbox.testing import TestObjects
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import library_berlin
from qgis.core import QgsVectorLayer

initAll()


class Issue645Tests(TestCase):

    def test_issue647(self):
        n_bands = [256]
        n_features = 20
        speclib = TestObjects.createSpectralLibrary(n=n_features, n_bands=n_bands)
        speclib: QgsVectorLayer
        speclib.startEditing()
        procw = SpectralProcessingDialog(speclib=speclib)
        procw.setAlgorithm('enmapbox:SpectralResamplingToWavelength'.lower())
        self.showGui(procw)

    def test_issue_645(self):
        sl = QgsVectorLayer(library_berlin)
        sl.startEditing()
        d = SpectralProcessingDialog(speclib=sl)
        d.setAlgorithm('enmapbox:TranslateRasterLayer'.lower())
        self.showGui(d)
