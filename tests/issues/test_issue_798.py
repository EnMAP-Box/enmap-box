import unittest

from qgis.core import QgsProject, edit

from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingwidget import SpectralProcessingWidget
from enmapbox.testing import EnMAPBoxTestCase, start_app, TestObjects
from enmapboxprocessing.algorithm.fitpcaalgorithm import FitPcaAlgorithm

start_app()
initAll()


class TestIssue764(EnMAPBoxTestCase):

    def test_SpectralProcessing_Logging(self):
        speclib = TestObjects.createSpectralLibrary(2)

        alg = FitPcaAlgorithm()

        algorithmId = 'enmapbox:FitPca'.lower()
        parameters = {'featureRaster': 'profile0'}

        def checkOutputs(outputs):
            self.assertIsInstance(outputs, dict)
            for o in alg.outputDefinitions():
                self.assertTrue(o.name() in outputs)

        with edit(speclib):
            slw = SpectralLibraryWidget(speclib=speclib)
            spd = SpectralProcessingWidget(speclib=speclib, algorithmId=algorithmId, parameters=parameters)
            spd.sigOutputsCreated.connect(checkOutputs)
            spd.runAlgorithm(fail_fast=True)

            logText = spd.processingFeedback().htmlLog()
            self.assertTrue('Fit transformer' in logText)
            self.showGui([spd, slw])

        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
