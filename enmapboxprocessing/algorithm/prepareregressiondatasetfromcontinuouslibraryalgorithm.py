from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import FIELD_VALUES, SpectralLibraryUtils
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import checkSampleShape, Target, RegressorDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingParameterField,
                       QgsProcessingException)
from typeguard import typechecked


@typechecked
class PrepareRegressionDatasetFromContinuousLibraryAlgorithm(EnMAPProcessingAlgorithm):
    P_CONTINUOUS_LIBRARY, _CONTINUOUS_LIBRARY = 'continuousLibrary', 'Continuous-valued spectral library'
    P_FIELD, _FIELD = 'field', 'Field with spectral profiles used as features'
    P_TARGET_FIELDS, _TARGET_FIELDS = 'targetFields', 'Fields with target values'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputRegressionDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create regression dataset (from continuous-valued spectral library)'

    def shortDescription(self) -> str:
        return 'Create a regression dataset from spectral profiles that matches the given target variables ' \
               'and store the result as a pickle file.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CONTINUOUS_LIBRARY,
             'Continuous-valued spectral library with feature data X (i.e. spectral profiles) and target data y. '
             'It is assumed, but not enforced, that the spectral characteristics of all spectral profiles match. '
             'If not all spectral profiles share the same number of spectral bands, an error is raised.'),
            (self._TARGET_FIELDS, 'Fields with continuous-valued values used as target data y. '
                                  'If not selected, the fields defined by the renderer is used. '
                                  'If those are also not specified, an error is raised.'),
            (self._FIELD, 'Field with spectral profiles used as feature data X. '
                          'If not selected, the default field named "profiles" is used. '
                          'If that is also not available, an error is raised.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_CONTINUOUS_LIBRARY, self._CONTINUOUS_LIBRARY)
        self.addParameterField(
            self.P_TARGET_FIELDS, self._TARGET_FIELDS, None, self.P_CONTINUOUS_LIBRARY,
            QgsProcessingParameterField.Any, True, True, False, True
        )
        self.addParameterField(
            self.P_FIELD, self._FIELD, None, self.P_CONTINUOUS_LIBRARY, QgsProcessingParameterField.Any, False, True,
            False, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        library = self.parameterAsLayer(parameters, self.P_CONTINUOUS_LIBRARY, context)
        binaryField = self.parameterAsField(parameters, self.P_FIELD, context)
        targetFields = self.parameterAsFields(parameters, self.P_TARGET_FIELDS, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # derive target fields
            if targetFields is None:
                targets = Utils.targetsFromLayer(library)
                if targets is None:
                    message = 'Select either a continuous-valued vector layer, or fields with targets.'
                    raise QgsProcessingException(message)
                targetFields = [target.name for target in targets]
            else:
                targets = [Target(field, None) for field in targetFields]

            # open library
            if binaryField is None:
                binaryField = FIELD_VALUES
            feedback.pushInfo('Read data')

            # prepare data
            n = library.featureCount()
            X = list()
            y = list()
            for i, profile in enumerate(SpectralLibraryUtils.profiles(library, profile_field=binaryField)):
                feedback.setProgress(i / n * 100)

                yi = list()
                for field in targetFields:
                    yik = profile.attribute(field)
                    if yik is None:
                        yik = np.nan
                    yi.append(yik)

                Xi = profile.yValues()
                y.append(yi)
                X.append(Xi)

            if len(set(map(len, X))) != 1:
                raise QgsProcessingException('Number of features do not match across all spectral profiles.')

            try:
                X = np.array(X, dtype=np.float32)
            except Exception as error:
                ValueError(f'invalid feature data: {error}')

            try:
                y = np.array(y, dtype=np.float32)
            except Exception as error:
                ValueError(f'invalid target data: {error}')

            checkSampleShape(X, y, raise_=True)

            features = [f'Band {i + 1}' for i in range(X.shape[1])]
            dump = RegressorDump(targets=targets, features=features, X=X, y=y)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
