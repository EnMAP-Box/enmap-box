from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class PrepareUnsupervisedDatasetFromFileAlgorithm(EnMAPProcessingAlgorithm):
    P_FEATURE_FILE, _FEATURE_FILE = 'featureFile', 'File with features'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputUnsupervisedDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create unsupervised dataset (from text file)'

    def shortDescription(self) -> str:
        link = self.htmlLink(
            "https://force-eo.readthedocs.io/en/latest/components/higher-level/smp/index.html",
            "FORCE Higher Level Sampling Submodule"
        )
        return 'Create an unsupervised dataset from a tabulated text file ' \
               'and store the result as a pickle file. \n' \
               f'The format matches that of the {link}.\n' \
               f'An example file (force_features.csv) can be found in the EnMAP-Box testdata folder).'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FEATURE_FILE,
             'Text file with tabulated feature data X (no headers). '
             'Each row represents the feature vector of a sample.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FEATURE_FILE, self._FEATURE_FILE)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameFeatures = self.parameterAsFile(parameters, self.P_FEATURE_FILE, context)
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

            # prepare categories
            dump = TransformerDump(features=features, X=X)
            Utils.pickleDump(dump.__dict__, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
