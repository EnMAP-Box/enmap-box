from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import checkSampleShape, ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsFeature, QgsProcessingParameterField)
from typeguard import typechecked


@typechecked
class PrepareClassificationDatasetFromTableAlgorithm(EnMAPProcessingAlgorithm):
    P_TABLE, _TABLE = 'table', 'Table'
    P_FEATURE_FIELDS, _FEATURE_FIELDS = 'featureFields', 'Fields with features'
    P_VALUE_FIELD, _VALUE_FIELD = 'valueField', 'Field with class values'
    P_NAME_FIELD, _NAME_FIELD = 'nameField', 'Field with class names'
    P_COLOR_FIELD, _COLOR_FIELD = 'colorField', 'Field with class colors'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputClassificationDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create classification dataset (from table with categories and feature fields)'

    def shortDescription(self) -> str:
        return 'Create a classification dataset from attribute table rows that match the given categories ' \
               'and store the result as a pickle file. \n'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._TABLE, 'Table with feature data X and target data y.'),
            (self._FEATURE_FIELDS, 'Fields used as features. '
                                   'Values may be given as strings, but must be castable to float.'),
            (self._VALUE_FIELD, 'Field used as class value.'),
            (self._NAME_FIELD, 'Field used as class name. If not specified, class values are used as class names.'),
            (self._COLOR_FIELD, 'Field used as class color. '
                                'Values may be given as hex-colors, rgb-colors or int-colors.'),
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
            self.P_VALUE_FIELD, self._VALUE_FIELD, None, self.P_TABLE, QgsProcessingParameterField.Any
        )
        self.addParameterField(
            self.P_NAME_FIELD, self._NAME_FIELD, None, self.P_TABLE, QgsProcessingParameterField.Any, False, True
        )
        self.addParameterField(
            self.P_COLOR_FIELD, self._COLOR_FIELD, None, self.P_TABLE, QgsProcessingParameterField.Any, False, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        table = self.parameterAsLayer(parameters, self.P_TABLE, context)
        featureFields = self.parameterAsFields(parameters, self.P_FEATURE_FIELDS, context)
        classField = self.parameterAsField(parameters, self.P_VALUE_FIELD, context)
        nameField = self.parameterAsField(parameters, self.P_NAME_FIELD, context)
        colorField = self.parameterAsField(parameters, self.P_COLOR_FIELD, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            feedback.pushInfo('Read data')
            # prepare categories
            categories_ = Utils.categoriesFromVectorField(table, classField, nameField, colorField)
            categories, valueLookup = Utils.prepareCategories(categories_, valuesToInt=True, removeLastIfEmpty=True)
            # prepare data
            n = table.featureCount()
            X = np.zeros(shape=(n, len(featureFields)), dtype=np.float32)
            y = np.zeros(shape=(n, 1), dtype=np.float32)
            feature: QgsFeature
            for i, feature in enumerate(table.getFeatures()):
                feedback.setProgress(i / n * 100)
                yi = valueLookup.get(feature.attribute(classField), None)
                if yi is None:  # if category is not of interest ...
                    continue  # ... skip the profile
                y[i, 0] = yi
                for k, featureField in enumerate(featureFields):
                    Xik = feature.attribute(featureField)
                    if Xik is None:
                        Xik = np.nan
                    X[i, k] = Xik
            checkSampleShape(X, y)

            dump = ClassifierDump(categories=categories, features=featureFields, X=X, y=y)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
