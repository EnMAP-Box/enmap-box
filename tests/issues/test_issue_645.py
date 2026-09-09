from qgis.core import QgsVectorLayer

from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingwidget import SpectralProcessingWidget
from enmapbox.testing import TestObjects
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import library_berlin

initAll()


class Issue645Tests(TestCase):

    def test_issue647(self):
        n_bands = [256]
        n_features = 20
        speclib = TestObjects.createSpectralLibrary(n=n_features, n_bands=n_bands)
        speclib: QgsVectorLayer
        speclib.startEditing()
        procw = SpectralProcessingWidget(speclib=speclib)
        procw.setAlgorithm('enmapbox:SpectralResamplingToWavelength'.lower())
        self.showGui(procw)

    def test_issue_645(self):
        sl = QgsVectorLayer(library_berlin)
        sl.startEditing()
        d = SpectralProcessingWidget(speclib=sl)
        d.setAlgorithm('enmapbox:TranslateRasterLayer'.lower())
        self.showGui(d)
