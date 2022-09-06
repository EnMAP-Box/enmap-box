import inspect
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class PrepareUnsupervisedDatasetFromCodeAlgorithm(EnMAPProcessingAlgorithm):
    P_CODE, _CODE = 'code', 'Code'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputUnsupervisedDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create unsupervised dataset (from Python code)'

    def shortDescription(self) -> str:
        return 'Create an unsupervised dataset from Python code ' \
               'and store the result as a pickle file.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CODE, 'Python code specifying the unsupervised dataset.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def code(cls):
        from enmapboxprocessing.typing import Number, List

        # specify feature names
        features: List[str] = ['Feature 1', 'Feature 2', 'Feature 3']

        # specify features X as 2d-array with shape (samples, features)
        X: List[List[Number]] = [
            [1, 2, 3],
            [4, 5, 6]
        ]

        return TransformerDump(features, X)

    def defaultCodeAsString(self):
        try:
            lines = [line[8:] for line in inspect.getsource(self.code).split('\n')][1:-2]
        except OSError:
            lines = ['']
        lines = '\n'.join(lines)
        return lines

    def parameterAsTransformerDump(
            self, parameters: Dict[str, Any], name, context: QgsProcessingContext
    ) -> TransformerDump:
        namespace = dict()
        code = self.parameterAsString(parameters, name, context)
        exec(code, namespace)
        features, X = [namespace[key] for key in ['features', 'X']]
        X = np.array(X)
        transformerDump = TransformerDump(features, X)
        return transformerDump

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterCode(self.P_CODE, self._CODE, self.defaultCodeAsString())
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            transformerDump = self.parameterAsTransformerDump(parameters, self.P_CODE, context)
            Utils.pickleDump(transformerDump.__dict__, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
