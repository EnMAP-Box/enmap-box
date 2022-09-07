from random import randint
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import Category, ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class PrepareClassificationDatasetFromFilesAlgorithm(EnMAPProcessingAlgorithm):
    P_FEATURE_FILE, _FEATURE_FILE = 'featureFile', 'File with features'
    P_VALUE_FILE, _VALUE_FILE = 'valueFile', 'File with class values'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputClassificationDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create classification dataset (from text files)'

    def shortDescription(self) -> str:
        link = self.htmlLink(
            "https://force-eo.readthedocs.io/en/latest/components/higher-level/smp/index.html",
            "FORCE Higher Level Sampling Submodule"
        )
        return 'Create a classification dataset from tabulated text files ' \
               'and store the result as a pickle file. \n' \
               f'The format matches that of the {link}.\n' \
               f'Example files (force_features.csv and force_labels.csv) can be found in the EnMAP-Box testdata folder).'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FEATURE_FILE,
             'Text file with tabulated feature data X (no headers). '
             'Each row represents the feature vector of a sample.'),
            (self._VALUE_FILE,
             'Text file with tabulated target data y (no headers). '
             'Each row represents the class value of a sample.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FEATURE_FILE, self._FEATURE_FILE)
        self.addParameterFile(self.P_VALUE_FILE, self._VALUE_FILE)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameFeatures = self.parameterAsFile(parameters, self.P_FEATURE_FILE, context)
        filenameLabels = self.parameterAsFile(parameters, self.P_VALUE_FILE, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # read data
            X = list()
            with open(filenameFeatures) as file:
                for line in file.readlines():
                    X.append(line.split())
            X = np.array(X, dtype=np.float32)
            features = [f'feature {i + 1}' for i in range(X.shape[1])]

            y = list()
            with open(filenameLabels) as file:
                for line in file.readlines():
                    y.append(line.split())
            y = np.array(y, dtype=np.float32).astype(dtype=np.int32, casting='unsafe')

            # prepare categories
            values = np.unique(y)
            categories = [Category(int(v), str(v), QColor(randint(0, 2 ** 24 - 1)).name()) for v in values]

            dump = ClassifierDump(categories=categories, features=features, X=X, y=y)
            Utils.pickleDump(dump.__dict__, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
