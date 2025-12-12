import unittest

from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.processing.algorithmdialog import AlgorithmDialog
from enmapbox.qgispluginsupport.qps.speclib.processing.extractspectralprofiles import ExtractSpectralProfiles
from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis._core import QgsProject, QgsRasterLayer, QgsVectorLayer

start_app()
initAll()


class ExtractProfilesTests(EnMAPBoxTestCase):

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'GUI Testing only')
    def test_extractProfiles(self):
        alg = ExtractSpectralProfiles()
        alg.initAlgorithm({})

        context, feedback = self.createProcessingContextFeedback()

        from enmapbox.exampledata import enmap, landcover_point
        project = QgsProject()
        lyr1 = QgsRasterLayer(enmap, 'enmap')
        lyr2 = QgsVectorLayer(landcover_point, 'landcover')

        project.addMapLayers([lyr1, lyr2])
        context.setProject(project)

        d = AlgorithmDialog(alg, context=context)

        d.exec_()

        results = d.results()
        self.assertTrue(len(results) > 0)
