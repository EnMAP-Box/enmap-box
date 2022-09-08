from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import RegressorDump, Target
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class PrepareRegressionDatasetFromJsonAlgorithm(EnMAPProcessingAlgorithm):
    P_JSON_FILE, _JSON_FILE = 'jsonFile', 'JSON file'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputRegressionDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create regression dataset (from JSON file)'

    def shortDescription(self) -> str:
        return 'Create a regression dataset from a JSON file and store the result as a pickle file. \n' \
               'Example file (regressor.pkl.json) can be found in the EnMAP-Box testdata folder).'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._JSON_FILE, 'JSON file containing all information.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_JSON_FILE, self._JSON_FILE, extension=self.JsonFileExtension)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameJson = self.parameterAsFile(parameters, self.P_JSON_FILE, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            json = Utils.jsonLoad(filenameJson)
            json['targets'] = [Target(**values) for values in json['targets']]
            json['X'] = np.array(json['X'])
            json['y'] = np.array(json['y'])
            json['regressor'] = None
            dump = RegressorDump.fromDict(json)
            Utils.pickleDump(dump.__dict__, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
