import inspect
import traceback
from typing import Dict, Any, List, Tuple

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback
from typeguard import typechecked


@typechecked
class FitRegressorAlgorithmBase(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Training dataset'
    P_REGRESSOR, _REGRESSOR = 'regressor', 'Regressor'
    P_OUTPUT_REGRESSOR, _OUTPUT_REGRESSOR = 'outputRegressor', 'Output regressor'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Training dataset pickle file used for fitting the classifier. '
                            'If not specified, an unfitted classifier is created.'),
            (self._REGRESSOR, self.helpParameterCode()),
            (self._OUTPUT_REGRESSOR, self.PickleFileDestination)
        ]

    def displayName(self) -> str:
        raise NotImplementedError()

    def shortDescription(self) -> str:
        raise NotImplementedError()

    def code(self):
        raise NotImplementedError()

    def helpParameterCode(self) -> str:
        raise NotImplementedError()

    def group(self):
        return Group.Test.value + Group.Regression.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterCode(self.P_REGRESSOR, self._REGRESSOR, self.defaultCodeAsString())
        self.addParameterRegressionDataset(self.P_DATASET, self._DATASET, None, True)
        self.addParameterFileDestination(self.P_OUTPUT_REGRESSOR, self._OUTPUT_REGRESSOR, self.PickleFileFilter)

    def defaultCodeAsString(self):
        try:
            lines = [line[8:] for line in inspect.getsource(self.code).split('\n')][1:-2]
        except OSError:
            lines = ['']
        lines = '\n'.join(lines)
        return lines

    def parameterAsRegressor(self, parameters: Dict[str, Any], name, context: QgsProcessingContext):
        namespace = dict()
        code = self.parameterAsString(parameters, name, context)
        exec(code, namespace)
        return namespace['regressor']

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        valid, message = super().checkParameterValues(parameters, context)
        if not valid:
            return valid, message
        # check code
        try:
            self.parameterAsRegressor(parameters, self.P_REGRESSOR, context)
        except Exception:
            return False, traceback.format_exc()
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        dump = self.parameterAsRegressorDump(parameters, self.P_DATASET, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REGRESSOR, context)
        regressor = self.parameterAsRegressor(parameters, self.P_REGRESSOR, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            if dump is not None:
                feedback.pushInfo(
                    f'Load training dataset: X=array{list(dump.X.shape)} y=array{list(dump.y.shape)} '
                    f'targets={[c.name for c in dump.targets]}')
                feedback.pushInfo('Fit regressor')
                if dump.y.shape[1] == 1:
                    regressor.fit(dump.X, dump.y.ravel())
                else:
                    regressor.fit(dump.X, dump.y)
            else:
                feedback.pushInfo('Store unfitted classifier')
                dump = RegressorDump(None, None, None, None, regressor)

            dump.regressor = regressor
            Utils.pickleDump(dump.__dict__, filename)

            result = {self.P_OUTPUT_REGRESSOR: filename}
            self.toc(feedback, result)

        return result
