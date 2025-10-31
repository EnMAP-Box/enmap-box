from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import FIELD_VALUES
from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import checkSampleShape, Target, RegressorDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingParameterField,
                       QgsProcessingException)
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import decodeProfileValueDict


@typechecked
class PrepareRegressionDatasetFromContinuousLibraryAlgorithm(EnMAPProcessingAlgorithm):
    P_CONTINUOUS_LIBRARY, _CONTINUOUS_LIBRARY = 'continuousLibrary', 'Continuous-valued spectral library'
    P_FIELD, _FIELD = 'field', 'Field with spectral profiles used as features'
    P_TARGET_FIELDS, _TARGET_FIELDS = 'targetFields', 'Fields with target values'
    P_EXCLUDE_BAD_BANDS, _EXCLUDE_BAD_BANDS, = 'excludeBadBands', 'Exclude bad bands'
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
            (self._EXCLUDE_BAD_BANDS, 'Whether to exclude bands, that are marked as bad bands, '
                                      'or contain no data, inf or nan values in all samples.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.DatasetCreation.value

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
        self.addParameterBoolean(self.P_EXCLUDE_BAD_BANDS, self._EXCLUDE_BAD_BANDS, True, True, True)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        library = self.parameterAsLayer(parameters, self.P_CONTINUOUS_LIBRARY, context)
        binaryField = self.parameterAsField(parameters, self.P_FIELD, context)
        targetFields = self.parameterAsFields(parameters, self.P_TARGET_FIELDS, context)
        excludeBadBands = self.parameterAsBoolean(parameters, self.P_EXCLUDE_BAD_BANDS, context)
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
            locations = list()
            for i, feature in enumerate(library.getFeatures()):
                feedback.setProgress(i / n * 100)

                profileDict = decodeProfileValueDict(feature.attribute(binaryField))
                if len(profileDict) == 0:
                    raise QgsProcessingException(f'Not a valid Profiles field: {binaryField}')

                yi = list()
                for field in targetFields:
                    yik = feature.attribute(field)
                    if yik is None:
                        yik = np.nan
                    yi.append(yik)

                try:
                    Xi = np.array(profileDict['y'])
                except KeyError:
                    raise QgsProcessingException(f'Not a valid Profiles field: {binaryField}')

                if excludeBadBands:
                    if 'bbl' in profileDict:
                        valid = np.equal(profileDict['bbl'], 1)
                        Xi = Xi[valid]

                y.append(yi)
                X.append(Xi)

                point = feature.geometry().asPoint()
                locations.append((point.x(), point.y()))

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

            locations = np.array(locations)
            if excludeBadBands:
                # skip not finite bands
                validBands = np.any(np.isfinite(X), axis=0)
                X = X[:, validBands]

                # skip samples that contain not finite values
                validSamples = np.all(np.isfinite(X), axis=1)
                X = X[validSamples]
                y = y[validSamples]
                locations = locations[validSamples]

            checkSampleShape(X, y, raise_=True)

            features = [f'Band {i + 1}' for i in range(X.shape[1])]
            if library.crs().isValid():
                crs = library.crs().toWkt()
            else:
                locations = crs = None

            dump = RegressorDump(targets=targets, features=features, X=X, y=y, locations=locations, crs=crs)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
