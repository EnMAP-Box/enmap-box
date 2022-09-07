from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsFeature, QgsProcessingParameterField)
from typeguard import typechecked


@typechecked
class PrepareUnsupervisedDatasetFromVectorAndFieldsAlgorithm(EnMAPProcessingAlgorithm):
    P_VECTOR, _VECTOR = 'vector', 'Vector layer'
    P_FEATURE_FIELDS, _FEATURE_FIELDS = 'featureFields', 'Fields with features'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputUnsupervisedDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create unsupervised dataset (from vector layer with attribute table)'

    def shortDescription(self) -> str:
        return 'Create an unsupervised dataset from attribute table ' \
               'and store the result as a pickle file.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._VECTOR, 'Vector layer specifying feature data X.'),
            (self._FEATURE_FIELDS, 'Fields with values used as feature data X.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_VECTOR, self._VECTOR)
        self.addParameterField(
            self.P_FEATURE_FIELDS, self._FEATURE_FIELDS, None, self.P_VECTOR,
            QgsProcessingParameterField.Numeric, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        vector = self.parameterAsLayer(parameters, self.P_VECTOR, context)
        featureFields = self.parameterAsFields(parameters, self.P_FEATURE_FIELDS, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            feedback.pushInfo('Read data')

            n = vector.featureCount()
            X = list()
            feature: QgsFeature
            for i, feature in enumerate(vector.getFeatures()):
                feedback.setProgress(i / n * 100)
                for k, field in enumerate(featureFields):
                    Xik = feature.attribute(field)
                    if Xik is None:  # if attribute value is not defined, we inject NaN
                        Xik = np.nan
                    X.append(Xik)
            try:
                X = np.array(X, dtype=np.float32)
                X = X.reshape(-1, len(featureFields))
            except Exception as error:
                raise ValueError(f'invalid feature data: {error}')

            dump = TransformerDump(features=featureFields, X=X)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
