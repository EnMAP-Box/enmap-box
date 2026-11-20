import unittest

from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingalgorithmwidget import \
    SpectralProcessingAlgorithmWidget
from enmapbox.testing import EnMAPBoxTestCase, start_app, TestObjects
from enmapboxprocessing.algorithm.fitpcaalgorithm import FitPcaAlgorithm
from qgis.core import QgsProject, edit

start_app()
initAll()


class TestIssue764(EnMAPBoxTestCase):

    def test_SpectralProcessing_Logging(self):
        speclib = TestObjects.createSpectralLibrary(2)
        project = QgsProject()
        alg = FitPcaAlgorithm()

        algorithmId = 'enmapbox:FitPca'.lower()
        parameters = {'featureRaster': 'profile0'}

        with edit(speclib):
            slw = SpectralLibraryWidget(speclib=speclib, project=project)
            spd = SpectralProcessingAlgorithmWidget(speclib)
            spd.setAlgorithm(algorithmId)
            spd.setParameters(parameters)

            results_0 = None

            def checkOutputs(success: bool, results: dict):
                self.assertTrue(success)
                nonlocal results_0
                results_0 = results

            spd.algorithmFinished.connect(checkOutputs)
            spd.runAlgorithm(fail_fast=True)

            results = spd.results()
            for o in alg.outputDefinitions():
                self.assertTrue(o.name() in results)
                self.assertTrue(o.name() in results_0)

            logText = spd.feedback().textLog()
            self.assertTrue('Fit transformer' in logText, msg='Missing "Fit transformer" in log: {}'.format(logText))
            self.showGui([spd, slw])

        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
