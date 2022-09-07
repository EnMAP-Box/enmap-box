import webbrowser
from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.classificationperformancestratifiedalgorithm import \
    ClassificationPerformanceStratifiedAlgorithm
from enmapboxprocessing.algorithm.rastermathalgorithm.rastermathalgorithm import RasterMathAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsMapLayer
from typeguard import typechecked


@typechecked
class ClassificationPerformanceSimpleAlgorithm(EnMAPProcessingAlgorithm):
    P_CLASSIFICATION, _CLASSIFICATION = 'classification', 'Predicted classification layer'
    P_REFERENCE, _REFERENCE = 'reference', 'Observed categorized layer'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outClassificationPerformance', 'Output report'

    @classmethod
    def displayName(cls) -> str:
        return 'Classification layer accuracy and area report (for simple random sampling)'

    def shortDescription(self) -> str:
        return 'Estimates map accuracy and area proportions for (simple) random sampling. ' \
               'We use the formulars for the stratified random sampling described in ' \
               'Stehman (2014): https://doi.org/10.1080/01431161.2014.930207. ' \
               'Note that (simple) random sampling is a special case of stratified random sampling, ' \
               'with exactly one stratum. \n' \
               'Observed and predicted categories are matched by name.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CLASSIFICATION, 'A classification layer that is to be assessed.'),
            (self._REFERENCE, 'A categorized layer representing a (ground truth) observation sample, '
                              'that was aquired using a (simple) random sampling approach.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_CLASSIFICATION, self._CLASSIFICATION)
        self.addParameterMapLayer(self.P_REFERENCE, self._REFERENCE)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        classification = self.parameterAsRasterLayer(parameters, self.P_CLASSIFICATION, context)
        reference = self.parameterAsLayer(parameters, self.P_REFERENCE, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # create (pseudo) stratification with only one stratum
            alg = RasterMathAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_R1: classification,
                alg.P_CODE: 'R1*0 + 1',
                alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'pseudo-stratification.tif')
            }
            result = self.runAlg(alg, parameters, None, feedback2, context, True)
            stratification = QgsRasterLayer(result[alg.P_OUTPUT_RASTER])
            categories = [Category(1, 'Stratum 1', '#FF0000')]
            renderer = Utils.palettedRasterRendererFromCategories(stratification.dataProvider(), 1, categories)
            stratification.setRenderer(renderer)
            stratification.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            # run stratified version
            alg = ClassificationPerformanceStratifiedAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_CLASSIFICATION: classification,
                alg.P_REFERENCE: reference,
                alg.P_STRATIFICATION: stratification,
                alg.P_OPEN_REPORT: False,
                alg.P_OUTPUT_REPORT: filename,
            }
            result = self.runAlg(alg, parameters, None, feedback2, context, True)

            if openReport:
                webbrowser.open_new_tab(filename)

            self.toc(feedback, result)

        return result
