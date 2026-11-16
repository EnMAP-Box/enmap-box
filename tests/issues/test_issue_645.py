from enmapboxtestdata import library_berlin
from qgis.core import QgsVectorLayer

from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingalgorithmwidget import \
    SpectralProcessingAlgorithmWidget
from enmapbox.testing import TestObjects
from enmapboxprocessing.testcase import TestCase

initAll()


class Issue645Tests(TestCase):

    def test_issue647(self):
        n_bands = [256]
        n_features = 20
        speclib = TestObjects.createSpectralLibrary(n=n_features, n_bands=n_bands)
        speclib: QgsVectorLayer
        speclib.startEditing()
        procw = SpectralProcessingAlgorithmWidget(speclib)
        procw.setAlgorithm('enmapbox:SpectralResamplingToWavelength'.lower())
        self.showGui(procw)

    def test_issue_645(self):
        sl = QgsVectorLayer(library_berlin)
        sl.startEditing()
        d = SpectralProcessingAlgorithmWidget(sl)
        d.setAlgorithm('enmapbox:TranslateRasterLayer'.lower())
        self.showGui(d)
