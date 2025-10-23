import os
import unittest

from enmapbox import initAll
from enmapbox.testing import EnMAPBoxTestCase, TestObjects, start_app
from enmapboxprocessing.algorithm.savelibraryasgeojsonalgorithm import SaveLibraryAsGeoJsonAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProject

start_app()
initAll()

class TestIssue1089(EnMAPBoxTestCase):

    def test_memoryConversion(self):
        slib = TestObjects.createSpectralLibrary()
        QgsProject.instance().addMapLayer(slib)
        context = QgsProcessingContext()
        context.setProject(QgsProject.instance())
        feedback = QgsProcessingFeedback()
        context.setFeedback(feedback)

        alg = EnMAPProcessingAlgorithm()
        alg.addParameterVectorLayer('memory', '')
        params = {'memory': slib}

        slib2 = alg.parameterAsVectorLayer(params, 'memory', context)

        for field in slib.fields():
            field2 = slib2.fields().field(field.name())
            self.assertEqual(field.type(), field2.type())
            self.assertEqual(field.editorWidgetSetup().type(), field2.editorWidgetSetup().type())

        # cleanup
        QgsProject.instance().removeAllMapLayers()

    def test_issue1089(self):
        slib = TestObjects.createSpectralLibrary()
        QgsProject.instance().addMapLayer(slib)
        context = QgsProcessingContext()
        context.setProject(QgsProject.instance())
        feedback = QgsProcessingFeedback()
        context.setFeedback(feedback)

        alg = SaveLibraryAsGeoJsonAlgorithm()
        alg.initAlgorithm({})

        DIR = self.createTestOutputDirectory() / 'issue1089'
        os.makedirs(DIR, exist_ok=True)
        path = DIR / 'test.geojson'
        params = {alg.P_LIBRARY: slib.id(),
                  alg.P_OUTPUT_FILE: path.as_posix(),
                  }

        results = alg.processAlgorithm(params, context, feedback)

        # cleanup
        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
