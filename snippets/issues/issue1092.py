from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm
from qgis.core import QgsProject, QgsProcessingContext, QgsProcessingFeedback, QgsProcessingAlgorithm, \
    QgsProcessingParameterVectorLayer


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

    def test_memoryConversion_using_QgsProcessingAlgorithm(self):
        slib = TestObjects.createSpectralLibrary()
        QgsProject.instance().addMapLayer(slib)
        context = QgsProcessingContext()
        context.setProject(QgsProject.instance())
        feedback = QgsProcessingFeedback()
        context.setFeedback(feedback)

        class MyAlgo(QgsProcessingAlgorithm):
            pass

        alg = MyAlgo()
        alg.addParameter(QgsProcessingParameterVectorLayer('memory', ''))
        params = {'memory': slib}

        slib2 = alg.parameterAsVectorLayer(params, 'memory', context)

        for field in slib.fields():
            field2 = slib2.fields().field(field.name())
            print(field.type(), field2.type())
            print(field.editorWidgetSetup().type(), field2.editorWidgetSetup().type())
            self.assertEqual(field.type(), field2.type())
            self.assertEqual(field.editorWidgetSetup().type(), field2.editorWidgetSetup().type())
