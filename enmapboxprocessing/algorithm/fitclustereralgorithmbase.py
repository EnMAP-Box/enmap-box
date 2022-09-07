import inspect
import traceback
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClustererDump
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback
from typeguard import typechecked


@typechecked
class FitClustererAlgorithmBase(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Training dataset'
    P_CLUSTERER, _CLUSTERER = 'clusterer', 'Clusterer'
    P_OUTPUT_CLUSTERER, _OUTPUT_CLUSTERER = 'outputClusterer', 'Output clusterer'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Training dataset pickle file used for fitting the clusterer. '
                            'If not specified, an unfitted clusterer is created.'),
            (self._CLUSTERER, self.helpParameterCode()),
            (self._OUTPUT_CLUSTERER, self.PickleFileDestination)
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
        return Group.Test.value + Group.Clustering.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterCode(self.P_CLUSTERER, self._CLUSTERER, self.defaultCodeAsString())
        self.addParameterUnsupervisedDataset(self.P_DATASET, self._DATASET, None)
        self.addParameterFileDestination(self.P_OUTPUT_CLUSTERER, self._OUTPUT_CLUSTERER, self.PickleFileFilter)

    def defaultCodeAsString(self):
        try:
            lines = [line[8:] for line in inspect.getsource(self.code).split('\n')][1:-2]
        except OSError:
            lines = ['']
        lines = '\n'.join(lines)
        return lines

    def parameterAsClusterer(self, parameters: Dict[str, Any], name, context: QgsProcessingContext):
        namespace = dict()
        code = self.parameterAsString(parameters, name, context)
        exec(code, namespace)
        return namespace['clusterer']

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        valid, message = super().checkParameterValues(parameters, context)
        if not valid:
            return valid, message
        # check code
        try:
            self.parameterAsClusterer(parameters, self.P_CLUSTERER, context)
        except Exception:
            return False, traceback.format_exc()
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_CLUSTERER, context)
        clusterer = self.parameterAsClusterer(parameters, self.P_CLUSTERER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            if filenameDataset is not None:
                dump = ClustererDump.fromDict(Utils.pickleLoad(filenameDataset))
                feedback.pushInfo(
                    f'Load training dataset: X=array{list(dump.X.shape)}')
                feedback.pushInfo('Fit clusterer')
                clusterer.fit(dump.X)
                clusterCount = int(np.max(clusterer.predict(dump.X))) + 1
            else:
                feedback.pushInfo('Store unfitted clusterer')
                dump = ClustererDump(None, None, clusterer)

            dump = ClustererDump(clusterCount, dump.features, dump.X, clusterer)
            Utils.pickleDump(dump.__dict__, filename)

            result = {self.P_OUTPUT_CLUSTERER: filename}
            self.toc(feedback, result)

        return result
