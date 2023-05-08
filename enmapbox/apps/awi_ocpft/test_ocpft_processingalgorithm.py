from typing import Tuple
import sys
# from enmapboxprocessing.test.algorithm.testcase import TestCase
from awi_ocpft.processingalgorithm import OCPFTProcessingAlgorithm
from enmapboxprocessing.testcase import TestCase
from qgis.core import QgsProcessingContext, QgsProcessingFeedback


class TestOCPFTProcessingAlgorithm(TestCase):
    def createProcessingContextFeedback(self) -> Tuple[QgsProcessingContext, QgsProcessingFeedback]:
        """
        Create a QgsProcessingContext with connected QgsProcessingFeedback
        """

        def onProgress(progress: float):
            sys.stdout.write('\r{:0.2f} %'.format(progress))
            sys.stdout.flush()

            if progress == 100:
                print('')

        feedback = QgsProcessingFeedback()
        feedback.progressChanged.connect(onProgress)

        context = QgsProcessingContext()
        context.setFeedback(feedback)

        return context, feedback

    def test_OCPFTGlobalAlgorithm(self):
        alg = OCPFTProcessingAlgorithm()
        alg.initAlgorithm()
        parameters = {

            alg.P_FILE: '/home/alvarado/projects/typsynsat/data/sentinel3/bodensee/2020/08/16/S3A_OL_1_EFR____20200816T095809_20200816T100109_20200816T120938_0179_061_350_2160_MAR_O_NR_002.SEN3.nc',
            alg.P_SENSOR: 'OLCI',
            alg.P_MODEL: 'LAKE CONSTANCE',
            alg.P_AC: 'ENPT ACWATER',
            alg.P_OSIZE: 'Standard output',
            alg.P_OUTPUT_FOLDER: '/home/alvarado/projects/typsynsat/data/outputs/enmapbox/'

        }
        context, feedback = self.createProcessingContextFeedback()
        results = alg.processAlgorithm(parameters, context, feedback)
        self.assertTrue(len(results) > 0)
        s = []

        # self.runalg(alg, parameters)
