from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.fitgenericregressoralgorithm import FitGenericRegressorAlgorithm
from enmapboxprocessing.algorithm.predictregressionalgorithm import PredictRegressionAlgorithm
from enmapboxprocessing.algorithm.regressorperformancealgorithm import RegressorPerformanceAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class RegressionWorkflowAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Training dataset'
    P_REGRESSOR, _REGRESSOR = 'regressor', 'Regressor'
    P_RASTER, _RASTER = 'raster', 'Raster layer with features'
    P_NFOLD, _NFOLD = 'nfold', 'Number of cross-validation folds'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output cross-validation regressor performance report in ' \
                                                'webbrowser after running algorithm'
    P_OUTPUT_REGRESSOR, _OUTPUT_REGRESSOR = 'outputRegressor', 'Output regressor'
    P_OUTPUT_REGRESSION, _OUTPUT_REGRESSION = 'outputRegression', 'Output regression layer'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outputRegressorPerformance', 'Output cross-validation regressor performance ' \
                                                                    'report'

    def displayName(self) -> str:
        return 'Regression workflow'

    def shortDescription(self) -> str:
        return 'The regression workflow combines regressor fitting and map prediction.' \
               'Optionally, the cross-validation performance of the regressor can be assessed.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Training dataset pickle file used for fitting the regressor.'),
            (self._REGRESSOR, 'Scikit-Learn Python code specifying a regressor.'),
            (self._RASTER, 'A raster layer with bands used as features for mapping. '
                           'Regressor features and raster bands are matched by name. '
                           'Will be ignored, if map prediction is skipped.'),
            (self._NFOLD, 'The number of folds used for assessing cross-validation performance. '
                          'Will be ignored, if the cross-validation performance assessment is skipped.'),
            (self._OPEN_REPORT, 'Whether to open the cross-validation performance report in the web browser. '
                                'Will be ignored, if the cross-validation performance assessment is skipped.'),
            (self._OUTPUT_REPORT, 'Output cross-validation performance report file destination.'),
            (self._OUTPUT_REGRESSOR, self.PickleFileDestination),
            (self._OUTPUT_REGRESSION, 'Predicted map file destination.')
        ]

    def group(self):
        return Group.Test.value + Group.Regression.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRegressionDataset(self.P_DATASET, self._DATASET)
        self.addParameterRegressorCode(self.P_REGRESSOR, self._REGRESSOR)
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterInt(self.P_NFOLD, self._NFOLD, 10, True, 2, 100)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(
            self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter, None, True, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_REGRESSOR, self._OUTPUT_REGRESSOR, self.PickleFileFilter)
        self.addParameterRasterDestination(self.P_OUTPUT_REGRESSION, self._OUTPUT_REGRESSION, None, True, True)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        code = self.parameterAsString(parameters, self.P_REGRESSOR, context)
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        nfold = self.parameterAsInt(parameters, self.P_NFOLD, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)
        filenameRegressor = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REGRESSOR, context)
        filenameRegression = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_REGRESSION, context)
        filenameReport = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)

        with open(filenameRegressor + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # fit regressor
            alg = FitGenericRegressorAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_DATASET: filenameDataset,
                alg.P_REGRESSOR: code,
                alg.P_OUTPUT_REGRESSOR: filenameRegressor
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)

            # prediction regression
            if filenameRegression is not None:
                alg = PredictRegressionAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_RASTER: raster,
                    alg.P_REGRESSOR: filenameRegressor,
                    alg.P_OUTPUT_REGRESSION: filenameRegression
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)

            # regressor performance
            if filenameReport is not None:
                alg = RegressorPerformanceAlgorithm()
                parameters = {
                    alg.P_DATASET: filenameDataset,
                    alg.P_REGRESSOR: filenameRegressor,
                    alg.P_NFOLD: nfold,
                    alg.P_OPEN_REPORT: openReport,
                    alg.P_OUTPUT_REPORT: filenameReport
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {
                self.P_OUTPUT_REGRESSOR: filenameRegressor,
                self.P_OUTPUT_REGRESSION: filenameRegression,
                self.P_OUTPUT_REPORT: filenameReport,
            }
            self.toc(feedback, result)

        return result
