import time
from typing import Dict, Any

import processing
from enmapbox.qgispluginsupport.qps.testing import ExampleAlgorithmProvider
from enmapbox.testing import start_app, TestCase, TestObjects
from qgis.core import QgsProject, QgsProcessingAlgorithm, QgsProcessingRegistry, QgsApplication, \
    QgsProcessingParameterRasterLayer, \
    QgsProcessingContext, \
    QgsProcessingFeedback, QgsProcessingOutputFolder

start_app()


class MyExampleAlgorithm(QgsProcessingAlgorithm):

    INPUT_PATH = 'pathInput'

    def __init__(self):
        super().__init__()

    def createInstance(self):
        return MyExampleAlgorithm()

    def name(self):
        return 'examplealg'

    def displayName(self):
        return 'Example Algorithm'

    def initAlgorithm(self, configuration=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_PATH, 'The Input Dataset'))
        self.addOutput(QgsProcessingOutputFolder('outputFolder', 'The written folder'))

    def prepareAlgorithm(self,
                         parameters: Dict,
                         context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback) -> bool:
        # check the input parameters

        return True

    def processAlgorithm(self,
                         parameters: Dict,
                         context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback) -> Dict[str, Any]:
        # do the processing. This can be done in a parallel process
        assert isinstance(parameters, dict)
        assert isinstance(context, QgsProcessingContext)
        assert isinstance(feedback, QgsProcessingFeedback)

        feedback.setProgressText(f'Started {self.name()} processing')

        n = 42

        for i in range(n):
            # do something
            time.sleep(0.1)
            feedback.setProgress(i / n * 100)

        outputs = {'outputFolder': 'myoutputfolderpath'}

        return outputs


class MyTestCases(TestCase):

    def test_MyProcessingAlgorithm(self):
        provider = ExampleAlgorithmProvider()

        reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
        reg.addProvider(provider)

        self.assertTrue(provider.addAlgorithm(MyExampleAlgorithm()))

        a = reg.algorithmById('testalgorithmprovider:examplealg')
        self.assertIsInstance(a, MyExampleAlgorithm)
        a2 = a.createInstance()
        self.assertIsInstance(a2, MyExampleAlgorithm)
        self.assertTrue(id(a2) != id(a))

        # run the algorithm (helpful for debugging)

        lyr = TestObjects.createRasterLayer()

        # create a processing context and feedback object.
        # for testing, the feedback is printed to stdout
        context, feedback = self.createProcessingContextFeedback()

        params = {'pathInput': lyr}
        results, success = a2.run(params, context=context, feedback=feedback)

        self.assertTrue(success)
        self.assertIsInstance(results, dict)

        # run using the runner from the
        results = processing.run('testalgorithmprovider:examplealg',
                                 parameters=params, context=context, feedback=feedback)

        self.assertIsInstance(results, dict)

    def test_AlgorithmInDialog(self):
        provider = ExampleAlgorithmProvider()

        reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
        reg.addProvider(provider)
        self.assertTrue(provider.addAlgorithm(MyExampleAlgorithm()))

        lyr = TestObjects.createRasterLayer()
        QgsProject.instance().addMapLayer(lyr)

        context, feedback = self.createProcessingContextFeedback()

        dialog = processing.createAlgorithmDialog('testalgorithmprovider:examplealg')

        # the next line is equivalent to:
        # import os
        # if not os.environ['CI'].lower() in ['true',1]:
        #     dialog.exec_()

        self.showGui(dialog)

        # Don't forget to cleanup layer references
        QgsProject.instance().removeAllMapLayers()
