from typing import Dict, Any, List, Tuple

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)
from typeguard import typechecked


@typechecked
class SelectFeaturesFromDatasetAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Dataset'
    P_FEATURE_LIST, _FEATURE_LIST = 'featureList', 'Selected features'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputDatasetFeatureSubset', 'Output dataset'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Dataset pickle file to select features from.'),
            (self._FEATURE_LIST,
             'Comma separated list of feature names or positions. '
             "E.g. use <code>1, 'Feature 2', 3</code> to select the first three features."),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def displayName(self) -> str:
        return 'Select features from dataset'

    def shortDescription(self) -> str:
        return 'Subset and/or reorder features in feature data X.'

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_DATASET, self._DATASET, extension=self.PickleFileExtension)
        self.addParameterString(self.P_FEATURE_LIST, self._FEATURE_LIST)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        values = self.parameterAsValues(parameters, self.P_FEATURE_LIST, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            dump = ClassifierDump(**Utils.pickleLoad(filenameDataset))
            feedback.pushInfo(
                f'Load feature data: X=array{list(dump.X.shape)}')

            indices = list()
            for value in values:
                if isinstance(value, str):
                    if value not in dump.features:
                        raise QgsProcessingException(f"Feature '{value}' not found in sample.")
                    value = dump.features.index(value) + 1
                if not isinstance(value, int):
                    raise QgsProcessingException(
                        f'Feature must be given by name (string) or position (integer): {value}, {type(value)}.'
                    )
                index = value - 1
                if not (0 <= index < len(dump.features)):
                    raise QgsProcessingException(
                        f'Feature position {value} out of valid range [1, {len(dump.features)}]'
                    )
                indices.append(index)

            dumpDict = dump.__dict__.copy()
            dumpDict['X'] = dump.X[:, indices]
            dumpDict['features'] = [dump.features[index] for index in indices]
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)

        return result
