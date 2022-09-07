import webbrowser
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.algorithm.regressionperformancealgorithm import RegressionPerformanceAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer)
from typeguard import typechecked


@typechecked
class RegressorPerformanceAlgorithm(EnMAPProcessingAlgorithm):
    P_REGRESSOR, _REGRESSOR = 'regressor', 'Regressor'
    P_DATASET, _DATASET = 'dataset', 'Test dataset'
    P_NFOLD, _NFOLD = 'nfold', 'Number of cross-validation folds'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outputRegressorPerformance', 'Output report'

    def displayName(self) -> str:
        return 'Regressor performance report'

    def shortDescription(self) -> str:
        return 'Evaluates regressor performance.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._REGRESSOR, 'Regressor pickle file.'),
            (self._DATASET, 'Test dataset pickle file used for assessing the regressor performance.'),
            (self._NFOLD, 'The number of folds used for assessing cross-validation performance. '
                          'If not specified (default), simple test performance is assessed.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Regression.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterPickleFile(self.P_REGRESSOR, self._REGRESSOR)
        self.addParameterRegressionDataset(self.P_DATASET, self._DATASET)
        self.addParameterInt(self.P_NFOLD, self._NFOLD, None, True, 2, 100, True)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameRegressor = self.parameterAsFile(parameters, self.P_REGRESSOR, context)
        filenameSample = self.parameterAsFile(parameters, self.P_DATASET, context)
        nfold = self.parameterAsInt(parameters, self.P_NFOLD, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            dump = RegressorDump(**Utils.pickleLoad(filenameRegressor))
            sample = RegressorDump.fromDict(Utils.pickleLoad(filenameSample))
            feedback.pushInfo(f'Load regressor: {dump.regressor}')
            feedback.pushInfo(f'Load sample data: X{list(sample.X.shape)} y{list(sample.y.shape)}')

            if nfold is None:
                feedback.pushInfo('Evaluate regressor test performance')
                y2 = dump.regressor.predict(sample.X)
                y2 = np.reshape(y2, (len(dump.targets), -1, 1))
            else:
                feedback.pushInfo('Evaluate cross-validation performance')
                from sklearn.model_selection import cross_val_predict
                if sample.y.shape[1] == 1:
                    y = sample.y.flatten()
                else:
                    y = sample.y
                y2 = cross_val_predict(dump.regressor, X=sample.X, y=y, cv=nfold)
                y2 = np.reshape(y2, (len(dump.targets), -1, 1))

            # prepare raster layers
            y = sample.y[None].T
            reference = Driver(Utils.tmpFilename(filename, 'reference.tif')).createFromArray(y)
            prediction = Driver(Utils.tmpFilename(filename, 'prediction.tif')).createFromArray(y2)
            for bandNo, target in enumerate(dump.targets, 1):
                reference.setBandName(target.name, bandNo)
                prediction.setBandName(target.name, bandNo)
            reference.close()
            prediction.close()
            reference = QgsRasterLayer(reference.source())
            prediction = QgsRasterLayer(prediction.source())
            # eval
            alg = RegressionPerformanceAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_REGRESSION: prediction,
                alg.P_REFERENCE: reference,
                alg.P_OPEN_REPORT: False,
                alg.P_OUTPUT_REPORT: filename,
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {self.P_OUTPUT_REPORT: filename}

            if openReport:
                webbrowser.open_new_tab(filename)

            self.toc(feedback, result)

        return result
