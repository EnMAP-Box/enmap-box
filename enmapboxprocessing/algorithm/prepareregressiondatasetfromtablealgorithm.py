from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import checkSampleShape, Target, RegressorDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsFeature, QgsProcessingParameterField)
from typeguard import typechecked


@typechecked
class PrepareRegressionDatasetFromTableAlgorithm(EnMAPProcessingAlgorithm):
    P_TABLE, _TABLE = 'table', 'Table'
    P_FEATURE_FIELDS, _FEATURE_FIELDS = 'featureFields', 'Fields with features'
    P_TARGET_FIELDS, _TARGET_FIELDS = 'targetFields', 'Fields with targets'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputRegressionDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create regression dataset (from table with target and feature fields)'

    def shortDescription(self) -> str:
        return 'Create a regression dataset from attribute table rows ' \
               'and store the result as a pickle file.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._TABLE, 'Table with feature data X and target data y.'),
            (self._FEATURE_FIELDS, 'Fields used as features. '
                                   'Values may be given as strings, but must be castable to float.'),
            (self._TARGET_FIELDS, 'Fields used as targets. '
                                  'Values may be given as strings, but must be castable to float.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_TABLE, self._TABLE)
        self.addParameterField(
            self.P_FEATURE_FIELDS, self._FEATURE_FIELDS, None, self.P_TABLE, QgsProcessingParameterField.Any, True
        )
        self.addParameterField(
            self.P_TARGET_FIELDS, self._TARGET_FIELDS, None, self.P_TABLE, QgsProcessingParameterField.Any, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        table = self.parameterAsLayer(parameters, self.P_TABLE, context)
        featureFields = self.parameterAsFields(parameters, self.P_FEATURE_FIELDS, context)
        targetFields = self.parameterAsFields(parameters, self.P_TARGET_FIELDS, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            feedback.pushInfo('Read data')

            # prepare targets
            targets = [Target(targetField, None) for targetField in targetFields]

            # prepare data
            n = table.featureCount()
            X = np.zeros(shape=(n, len(featureFields)), dtype=np.float32)
            y = np.zeros(shape=(n, len(targetFields)), dtype=np.float32)
            feature: QgsFeature
            for i, feature in enumerate(table.getFeatures()):
                feedback.setProgress(i / n * 100)
                for k, targetField in enumerate(targetFields):
                    yik = feature.attribute(targetField)
                    if yik is None:
                        y[i, k] = np.nan
                    else:
                        y[i, k] = yik
                for k, featureField in enumerate(featureFields):
                    Xik = feature.attribute(featureField)
                    if Xik is None:
                        X[i, k] = np.nan
                    else:
                        X[i, k] = Xik

            checkSampleShape(X, y)

            dump = RegressorDump(targets, featureFields, X, y)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
