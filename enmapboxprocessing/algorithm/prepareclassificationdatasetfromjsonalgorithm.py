from typing import Dict, Any, List, Tuple

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClassifierDump
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class PrepareClassificationDatasetFromJsonAlgorithm(EnMAPProcessingAlgorithm):
    P_JSON_FILE, _JSON_FILE = 'jsonFile', 'JSON file'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputClassificationDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create classification dataset (from JSON file)'

    def shortDescription(self) -> str:
        return 'Create a classification dataset from a JSON file and store the result as a pickle file. \n' \
               'Example file (classifier.pkl.json) can be found in the EnMAP-Box testdata folder).'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._JSON_FILE, 'JSON file containing all information.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.DatasetCreation.value

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

            dump = ClassifierDump.fromFile(filenameJson)
            dump.write(filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
