import inspect
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class PrepareClassificationDatasetFromCodeAlgorithm(EnMAPProcessingAlgorithm):
    P_CODE, _CODE = 'code', 'Code'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputClassificationDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create classification dataset (from Python code)'

    def shortDescription(self) -> str:
        return 'Create a classification dataset from Python code ' \
               'and store the result as a pickle file.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CODE, 'Python code specifying the classification dataset.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def code(cls):
        from enmapboxprocessing.typing import Number, List, Category, ClassifierDump

        # specify categories and feature names
        categories: List[Category] = [
            Category(value=1, name='class 1', color='#ff0000'),
            Category(value=2, name='class 2', color='#00ff00')
        ]
        features: List[str] = ['Feature 1', 'Feature 2', 'Feature 3']

        # specify features X as 2d-array with shape (samples, features)
        X: List[List[Number]] = [
            [1, 2, 3],
            [4, 5, 6]
        ]
        # specify targets y as 2d-array with shape (samples, 1)
        y: List[List[int]] = [
            [1], [2]
        ]

        return ClassifierDump(categories, features, X, y)

    def defaultCodeAsString(self):
        try:
            lines = [line[8:] for line in inspect.getsource(self.code).split('\n')][1:-2]
        except OSError:
            lines = ['']
        lines = '\n'.join(lines)
        return lines

    def classifierDump(
            self, parameters: Dict[str, Any], context: QgsProcessingContext
    ) -> ClassifierDump:
        namespace = dict()
        code = self.parameterAsString(parameters, self.P_CODE, context)
        exec(code, namespace)
        categories, features, X, y = [namespace[key] for key in ['categories', 'features', 'X', 'y']]
        X = np.array(X)
        y = np.array(y)
        classifierDump = ClassifierDump(categories, features, X, y)
        return classifierDump

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

            classifierDump = self.classifierDump(parameters, context)
            Utils.pickleDump(classifierDump.__dict__, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
