from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import checkSampleShape, SampleX, SampleY, Target, \
    RegressorDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsFeature, QgsProcessingParameterField,
                       QgsVectorLayer, QgsProcessingException)
from typeguard import typechecked


@typechecked
class PrepareRegressionDatasetFromContinuousVectorAndFieldsAlgorithm(EnMAPProcessingAlgorithm):
    P_CONTINUOUS_VECTOR, _CONTINUOUS_VECTOR = 'continuousVector', 'Continuous-valued vector layer'
    P_FEATURE_FIELDS, _FEATURE_FIELDS = 'featureFields', 'Fields with features'
    P_TARGET_FIELDS, _TARGET_FIELDS = 'targetFields', 'Fields with targets'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputRegressionDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create regression dataset (from continuous-valued layer with attribute table)'

    def shortDescription(self) -> str:
        return 'Create a regression dataset from attribute table rows that matches the given target variables ' \
               'and store the result as a pickle file.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CONTINUOUS_VECTOR,
             'Continuous-valued vector layer specifying feature data X and target data y.'),
            (self._FEATURE_FIELDS, 'Fields with values used as feature data X.'),
            (self._TARGET_FIELDS, 'Fields with values used as used as target data y. '
                                  'If not selected, the fields defined by the renderer are used. '
                                  'If those are also not specified, an error is raised.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_CONTINUOUS_VECTOR, self._CONTINUOUS_VECTOR)
        self.addParameterField(
            self.P_FEATURE_FIELDS, self._FEATURE_FIELDS, None, self.P_CONTINUOUS_VECTOR,
            QgsProcessingParameterField.Numeric, True
        )
        self.addParameterField(
            self.P_TARGET_FIELDS, self._TARGET_FIELDS, None, self.P_CONTINUOUS_VECTOR,
            QgsProcessingParameterField.Numeric, True, True, False, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        vector = self.parameterAsVectorLayer(parameters, self.P_CONTINUOUS_VECTOR, context)
        featureFields = self.parameterAsFields(parameters, self.P_FEATURE_FIELDS, context)
        targetFields = self.parameterAsFields(parameters, self.P_TARGET_FIELDS, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # derive target fields
            renderer = vector.renderer()
            diagramRenderer = vector.diagramRenderer()

            if targetFields is None:
                targets = Utils.targetsFromRenderer(renderer, diagramRenderer)
                if targets is None:
                    message = 'Select either a continuous-valued vector layer, or fields with targets.'
                    raise QgsProcessingException(message)
                targetFields = [target.name for target in targets]
            else:
                targets = [Target(field, None) for field in targetFields]

            feedback.pushInfo('Read data')
            X, y = self.readDataset(vector, featureFields, targetFields, feedback)

            dump = RegressorDump(targets=targets, features=featureFields, X=X, y=y)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result

    def readDataset(
            self, vector: QgsVectorLayer, featureFields: List[str], targetFields: List[str],
            feedback: QgsProcessingFeedback
    ) -> Tuple[SampleX, SampleY]:

        n = vector.featureCount()
        X = list()
        y = list()
        feature: QgsFeature
        for i, feature in enumerate(vector.getFeatures()):
            feedback.setProgress(i / n * 100)
            for field in targetFields:
                yik = feature.attribute(field),
                if yik is None:
                    yik = np.nan
                y.append(yik)

            for field in featureFields:
                Xik = feature.attribute(field)
                if Xik is None:
                    Xik = np.nan
                X.append(Xik)

        try:
            X = np.array(X, dtype=np.float32)
            X = X.reshape(-1, len(featureFields))
        except Exception as error:
            raise ValueError(f'invalid feature data: {error}')

        try:
            y = np.array(y, dtype=np.float32)
            y = y.reshape(-1, len(targetFields))
        except Exception as error:
            raise ValueError(f'invalid target data: {error}')

        checkSampleShape(X, y, raise_=True)
        return X, y
