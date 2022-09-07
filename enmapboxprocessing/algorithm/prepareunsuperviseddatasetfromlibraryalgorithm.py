from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import FIELD_VALUES, SpectralLibraryUtils
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingParameterField,
                       QgsProcessingException)
from typeguard import typechecked


@typechecked
class PrepareUnsupervisedDatasetFromLibraryAlgorithm(EnMAPProcessingAlgorithm):
    P_LIBRARY, _LIBRARY = 'library', 'Spectral library'
    P_FIELD, _FIELD = 'field', 'Field with spectral profiles used as features'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputUnsupervisedDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create unsupervised dataset (from spectral library)'

    def shortDescription(self) -> str:
        return 'Create an unsupervised dataset from spectral profiles ' \
               'and store the result as a pickle file.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._LIBRARY,
             'Spectral library with feature data X (i.e. spectral profiles). '
             'It is assumed, but not enforced, that the spectral characteristics of all spectral profiles match. '
             'If not all spectral profiles share the same number of spectral bands, an error is raised.'),
            (self._FIELD, 'Field with spectral profiles used as feature data X. '
                          'If not selected, the default field named "profiles" is used. '
                          'If that is also not available, an error is raised.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_LIBRARY, self._LIBRARY)
        self.addParameterField(
            self.P_FIELD, self._FIELD, None, self.P_LIBRARY, QgsProcessingParameterField.Any, False, True,
            False, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        library = self.parameterAsLayer(parameters, self.P_LIBRARY, context)
        binaryField = self.parameterAsField(parameters, self.P_FIELD, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # open library
            if binaryField is None:
                binaryField = FIELD_VALUES
            feedback.pushInfo('Read data')

            # prepare data
            n = library.featureCount()
            X = list()
            for i, profile in enumerate(SpectralLibraryUtils.profiles(library, profile_field=binaryField)):
                feedback.setProgress(i / n * 100)
                try:
                    Xi = profile.yValues()
                except TypeError:
                    raise QgsProcessingException(f'Profiles field must be Binary: {binaryField}')

                X.append(Xi)

            if len(set(map(len, X))) != 1:
                raise QgsProcessingException('Number of features do not match across all spectral profiles.')

            try:
                X = np.array(X, dtype=np.float32)
            except Exception as error:
                ValueError(f'invalid feature data: {error}')

            features = [f'Band {i + 1}' for i in range(X.shape[1])]
            dump = TransformerDump(features=features, X=X)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
