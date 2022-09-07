from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import checkSampleShape, ClassifierDump, Categories, SampleX, SampleY
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsCategorizedSymbolRenderer,
                       QgsFeature, QgsProcessingParameterField, QgsVectorLayer)
from typeguard import typechecked


@typechecked
class PrepareClassificationDatasetFromCategorizedVectorAndFieldsAlgorithm(EnMAPProcessingAlgorithm):
    P_CATEGORIZED_VECTOR, _CATEGORIZED_VECTOR = 'categorizedVector', 'Categorized vector layer'
    P_FEATURE_FIELDS, _FEATURE_FIELDS = 'featureFields', 'Fields with features'
    P_CATEGORY_FIELD, _CATEGORY_FIELD = 'categoryField', 'Field with class values'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputClassificationDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create classification dataset (from categorized vector layer with attribute table)'

    def shortDescription(self) -> str:
        return 'Create a classification dataset from attribute table rows that matches the given categories ' \
               'and store the result as a pickle file. \n' \
               'If the layer is not categorized, or the field with class values is selected manually, ' \
               'categories are derived from the target data y. ' \
               'To be more precise: ' \
               'i) category values are derived from unique attribute values (after excluding no data or zero data values), ' \
               'ii) category names are set equal to the category values, ' \
               'and iii) category colors are picked randomly.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CATEGORIZED_VECTOR,
             'Categorized vector layer specifying feature data X and target data y.'),
            (self._FEATURE_FIELDS, 'Fields with values used as feature data X.'),
            (self._CATEGORY_FIELD, 'Field with class values used as target data y. '
                                   'If not selected, the field defined by the renderer is used. '
                                   'If that is also not specified, an error is raised.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_CATEGORIZED_VECTOR, self._CATEGORIZED_VECTOR)
        self.addParameterField(
            self.P_FEATURE_FIELDS, self._FEATURE_FIELDS, None, self.P_CATEGORIZED_VECTOR,
            QgsProcessingParameterField.Numeric, True
        )
        self.addParameterField(
            self.P_CATEGORY_FIELD, self._CATEGORY_FIELD, None, self.P_CATEGORIZED_VECTOR,
            QgsProcessingParameterField.Any, False, True, False, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        classification = self.parameterAsLayer(parameters, self.P_CATEGORIZED_VECTOR, context)
        featureFields = self.parameterAsFields(parameters, self.P_FEATURE_FIELDS, context)
        classField = self.parameterAsField(parameters, self.P_CATEGORY_FIELD, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # derive classification scheme
            renderer = classification.renderer()
            if classField is None:
                if isinstance(renderer, QgsCategorizedSymbolRenderer):
                    categories = Utils.categoriesFromCategorizedSymbolRenderer(renderer)
                    classField = renderer.classAttribute()
                    feedback.pushInfo(f'Use categories from style: {categories}')
                else:
                    feedback.reportError(
                        'Select either a categorited vector layer, or a field with class values.',
                        fatalError=True
                    )
            else:
                categories = Utils.categoriesFromVectorField(classification, classField)
                feedback.pushInfo(f'Derive categories from selected field: {categories}')

            feedback.pushInfo('Read data')
            X, y, categories = self.readDataset(classification, categories, classField, featureFields, feedback)

            dump = ClassifierDump(categories=categories, features=featureFields, X=X, y=y)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result

    def readDataset(
            self, vector: QgsVectorLayer, categories: Categories, yField: str, xFields: List[str],
            feedback: QgsProcessingFeedback
    ) -> Tuple[SampleX, SampleY, Categories]:
        # map string category values to a suitable integer that can be used for mapping
        categories, valueLookup = Utils.prepareCategories(categories, valuesToInt=True, removeLastIfEmpty=True)

        n = vector.featureCount()
        X = list()
        y = list()
        feature: QgsFeature
        for i, feature in enumerate(vector.getFeatures()):
            feedback.setProgress(i / n * 100)
            yi = valueLookup.get(feature.attribute(yField), None)
            if yi is None:  # if category is not of interest ...
                continue  # ... we skip the sample silently
            y.append(yi)
            for k, field in enumerate(xFields):
                Xik = feature.attribute(field)
                if Xik is None:  # if attribute value is not defined, we inject NaN
                    Xik = np.nan
                X.append(Xik)
        try:
            X = np.array(X, dtype=np.float32)
            X = X.reshape(-1, len(xFields))
        except Exception as error:
            raise ValueError(f'invalid feature data: {error}')

        try:
            y = np.array(y, dtype=np.float32)
            y = y.reshape(-1, 1)
        except Exception as error:
            raise ValueError(f'invalid target data: {error}')

        checkSampleShape(X, y, raise_=True)
        return X, y, categories
