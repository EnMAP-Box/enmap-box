from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import FIELD_VALUES, \
    SpectralLibraryUtils
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import checkSampleShape, ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsCategorizedSymbolRenderer,
                       QgsProcessingParameterField, QgsProcessingException)
from typeguard import typechecked


@typechecked
class PrepareClassificationDatasetFromCategorizedLibraryAlgorithm(EnMAPProcessingAlgorithm):
    P_CATEGORIZED_LIBRARY, _CATEGORIZED_LIBRARY = 'categorizedLibrary', 'Categorized spectral library'
    P_FIELD, _FIELD = 'field', 'Field with spectral profiles used as features'
    P_CATEGORY_FIELD, _CATEGORY_FIELD = 'categoryField', 'Field with class values'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputClassificationDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create classification dataset (from categorized spectral library)'

    def shortDescription(self) -> str:
        return 'Create a classification dataset from spectral profiles that matches the given categories ' \
               'and store the result as a pickle file.\n' \
               'If the spectral library is not categorized, or the field with class values is selected manually, ' \
               'categories are derived from target data y. ' \
               'To be more precise: ' \
               'i) category values are derived from unique attribute values (after excluding no data or zero data values), ' \
               'ii) category names are set equal to the category values, ' \
               'and iii) category colors are picked randomly.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CATEGORIZED_LIBRARY,
             'Categorized spectral library with feature data X (i.e. spectral profiles) and target data y. '
             'It is assumed, but not enforced, that the spectral characteristics of all spectral profiles match. '
             'If not all spectral profiles share the same number of spectral bands, an error is raised.'),
            (self._CATEGORY_FIELD, 'Field with class values used as target data y. '
                                   'If not selected, the field defined by the renderer is used. '
                                   'If that is also not specified, an error is raised.'),
            (self._FIELD, 'Field with spectral profiles used as feature data X. '
                          'If not selected, the default field named "profiles" is used. '
                          'If that is also not available, an error is raised.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_CATEGORIZED_LIBRARY, self._CATEGORIZED_LIBRARY)
        self.addParameterField(
            self.P_CATEGORY_FIELD, self._CATEGORY_FIELD, None, self.P_CATEGORIZED_LIBRARY,
            QgsProcessingParameterField.Any, False, True, False, True
        )
        self.addParameterField(
            self.P_FIELD, self._FIELD, None, self.P_CATEGORIZED_LIBRARY, QgsProcessingParameterField.Any, False, True,
            False, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        library = self.parameterAsLayer(parameters, self.P_CATEGORIZED_LIBRARY, context)
        binaryField = self.parameterAsField(parameters, self.P_FIELD, context)
        classField = self.parameterAsField(parameters, self.P_CATEGORY_FIELD, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # derive classification scheme
            renderer = library.renderer()
            if classField is None:
                if isinstance(renderer, QgsCategorizedSymbolRenderer):
                    categories = Utils.categoriesFromCategorizedSymbolRenderer(renderer)
                    classField = renderer.classAttribute()
                    feedback.pushInfo(f'Use categories from style: {categories}')
                else:
                    message = 'Select either a categorized spectral library or a field with class values.'
                    feedback.reportError(message, fatalError=True)
                    raise QgsProcessingException(message)
            else:
                categories = Utils.categoriesFromVectorField(library, classField)
                if len(categories) > 0:
                    feedback.pushInfo(f'Derive categories from selected field: {categories}')
                else:
                    raise QgsProcessingException(f'Unable to derive categories from field: {classField}')

            # open library
            if binaryField is None:
                binaryField = FIELD_VALUES
            feedback.pushInfo('Read data')

            # prepare categories
            categories, valueLookup = Utils.prepareCategories(categories, valuesToInt=True, removeLastIfEmpty=True)

            # prepare data
            n = library.featureCount()
            X = list()
            y = list()
            for i, profile in enumerate(SpectralLibraryUtils.profiles(library, profile_field=binaryField)):
                feedback.setProgress(i / n * 100)
                yi = valueLookup.get(profile.attribute(classField), None)
                if yi is None:  # if category is not of interest ...
                    continue  # ... we skip the profile
                try:
                    Xi = profile.yValues()
                except TypeError:
                    raise QgsProcessingException(f'Profiles field must be Binary: {binaryField}')

                y.append(yi)
                X.append(Xi)

            if len(set(map(len, X))) != 1:
                raise QgsProcessingException('Number of features do not match across all spectral profiles.')

            try:
                X = np.array(X, dtype=np.float32)
            except Exception as error:
                ValueError(f'invalid feature data: {error}')

            try:
                y = np.array(y)
                y = y.reshape(-1, 1)
            except Exception as error:
                ValueError(f'invalid target data: {error}')

            checkSampleShape(X, y, raise_=True)

            features = [f'Band {i + 1}' for i in range(X.shape[1])]
            dump = ClassifierDump(categories=categories, features=features, X=X, y=y)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
