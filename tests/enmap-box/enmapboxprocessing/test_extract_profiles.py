from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.reimplementation.algorithmwidget import AlgorithmWidget
from enmapbox.qgispluginsupport.qps.speclib.processing.extractspectralprofiles import ExtractSpectralProfiles
from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsApplication

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

        is_finished = False

        def onFinished(*args):
            nonlocal is_finished
            is_finished = True

        d = AlgorithmWidget(alg, processing_context=context)
        d.algorithmFinished.connect(onFinished)
        d.runAlgorithm()

        while not is_finished:
            QgsApplication.processEvents()
        results = d.results()
        lyr = results.get(ExtractSpectralProfiles.P_OUTPUT)
        self.assertIsInstance(lyr, QgsVectorLayer)
        self.assertTrue(lyr.featureCount() > 0)
        d.close()
