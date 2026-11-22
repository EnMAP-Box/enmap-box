import unittest

from qgis.core import QgsProject, edit

from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.testing import EnMAPBoxTestCase, start_app, TestObjects

start_app()
initAll()


class TestIssue764(EnMAPBoxTestCase):

    # @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'fails in CI')
    def test_SpectralProcessing_RasterMath(self):
        speclib = TestObjects.createSpectralLibrary(2)
        algorithmId = 'enmapbox:RasterMath'.lower()
        algorithmId = 'gdal:translate'
        parameters = {'code': 'my code input'}
        parameters = {}
        with edit(speclib):
            SpectralLibraryUtils.addSpectralProfileField(speclib, 'profiles2')
            slw = SpectralLibraryWidget(speclib=speclib)

            # spd = SpectralProcessingAlgorithmWidget(speclib=speclib)
            # spd.setAlgorithm(algorithmId)
            # spd.setParameters(parameters)
            spd = slw.openSpectralProcessingWidget(algorithmId=algorithmId, parameters=parameters)

            spd.runButton().animateClick()

            self.showGui([spd, slw])

        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
