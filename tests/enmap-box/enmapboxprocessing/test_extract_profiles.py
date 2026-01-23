from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.processing.algorithmdialog import AlgorithmDialog
from enmapbox.qgispluginsupport.qps.speclib.processing.extractspectralprofiles import ExtractSpectralProfiles
from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsApplication, QgsTaskManager

start_app()
initAll()


class ExtractProfilesTests(EnMAPBoxTestCase):

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
        if EnMAPBoxTestCase.runsInCI():
            d.runButton().click()
            # d.runAlgorithm()
            tm: QgsTaskManager = QgsApplication.taskManager()
            while len(tm.activeTasks()) > 0:
                QgsApplication.processEvents()
        else:
            d.exec_()

        if d.wasExecuted():
            results = d.results()
            lyr = results.get(ExtractSpectralProfiles.P_OUTPUT)
            self.assertIsInstance(lyr, QgsVectorLayer)
            self.assertTrue(lyr.featureCount() > 0)
        d.close()
