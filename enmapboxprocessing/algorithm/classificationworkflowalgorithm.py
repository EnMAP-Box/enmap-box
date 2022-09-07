from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.classifierperformancealgorithm import ClassifierPerformanceAlgorithm
from enmapboxprocessing.algorithm.fitgenericclassifieralgorithm import FitGenericClassifierAlgorithm
from enmapboxprocessing.algorithm.predictclassificationalgorithm import PredictClassificationAlgorithm
from enmapboxprocessing.algorithm.predictclassprobabilityalgorithm import PredictClassPropabilityAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class ClassificationWorkflowAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Training dataset'
    P_CLASSIFIER, _CLASSIFIER = 'classifier', 'Classifier'
    P_RASTER, _RASTER = 'raster', 'Raster layer with features'
    P_NFOLD, _NFOLD = 'nfold', 'Number of cross-validation folds'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_CLASSIFIER, _OUTPUT_CLASSIFIER = 'outputClassifier', 'Output classifier'
    P_OUTPUT_CLASSIFICATION, _OUTPUT_CLASSIFICATION = 'outputClassification', 'Output classification layer'
    P_OUTPUT_PROBABILITY, _OUTPUT_PROBABILITY = 'outputProbability', 'Output class probability layer'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outputClassifierPerformance', 'Output classifier performance report'

    def displayName(self) -> str:
        return 'Classification workflow'

    def shortDescription(self) -> str:
        return 'The classification workflow combines classifier fitting, map prediction and accuracy assessment.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Training dataset pickle file used for fitting the classifier.'),
            (self._CLASSIFIER, 'Scikit-Learn Python code specifying a classifier.'),
            (self._RASTER, 'A raster layer with bands used as features.'),
            (self._NFOLD, 'The number of folds used for assessing cross-validation performance.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_CLASSIFIER, self.PickleFileDestination),
            (self._OUTPUT_CLASSIFICATION, self.RasterFileDestination),
            (self._OUTPUT_PROBABILITY, self.RasterFileDestination),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterClassificationDataset(self.P_DATASET, self._DATASET)
        self.addParameterClassifierCode(self.P_CLASSIFIER, self._CLASSIFIER)
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterInt(self.P_NFOLD, self._NFOLD, 10, True, 2, 100)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_CLASSIFIER, self._OUTPUT_CLASSIFIER, self.PickleFileFilter)
        self.addParameterRasterDestination(self.P_OUTPUT_CLASSIFICATION, self._OUTPUT_CLASSIFICATION, None, True, True)
        self.addParameterRasterDestination(self.P_OUTPUT_PROBABILITY, self._OUTPUT_PROBABILITY, None, True, False)
        self.addParameterFileDestination(
            self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter, None, True, False
        )

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        code = self.parameterAsString(parameters, self.P_CLASSIFIER, context)
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        nfold = self.parameterAsInt(parameters, self.P_NFOLD, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)
        filenameClassifier = self.parameterAsFileOutput(parameters, self.P_OUTPUT_CLASSIFIER, context)
        filenameClassification = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_CLASSIFICATION, context)
        filenameProbability = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PROBABILITY, context)
        filenameReport = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)

        with open(filenameClassifier + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # fit classifier
            alg = FitGenericClassifierAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_DATASET: filenameDataset,
                alg.P_CLASSIFIER: code,
                alg.P_OUTPUT_CLASSIFIER: filenameClassifier
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)

            # prediction classification
            if filenameClassification is not None:
                alg = PredictClassificationAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_RASTER: raster,
                    alg.P_CLASSIFIER: filenameClassifier,
                    alg.P_OUTPUT_CLASSIFICATION: filenameClassification
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)

            # prediction probability
            if filenameProbability is not None:
                alg = PredictClassPropabilityAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_RASTER: raster,
                    alg.P_CLASSIFIER: filenameClassifier,
                    alg.P_OUTPUT_PROBABILITY: filenameProbability
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)

            # classifier performance
            if filenameReport is not None:
                alg = ClassifierPerformanceAlgorithm()
                parameters = {
                    alg.P_DATASET: filenameDataset,
                    alg.P_CLASSIFIER: filenameClassifier,
                    alg.P_NFOLD: nfold,
                    alg.P_OPEN_REPORT: openReport,
                    alg.P_OUTPUT_REPORT: filenameReport
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {
                self.P_OUTPUT_CLASSIFIER: filenameClassifier,
                self.P_OUTPUT_CLASSIFICATION: filenameClassification,
                self.P_OUTPUT_PROBABILITY: filenameProbability,
                self.P_OUTPUT_REPORT: filenameReport,
            }
            self.toc(feedback, result)

        return result
