from math import nan
from typing import Dict, Any, List, Tuple

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback
from typeguard import typechecked


@typechecked
class SpectralIndexOptimizerAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Training dataset'
    P_FORMULAR, _FORMULAR = 'formular', 'Formular'
    P_MAX_FEATURES, _MAX_FEATURES = 'maxFeatures', 'Max. features'
    P_F1, _F1 = 'f1', 'Fixed feature F1'
    P_F2, _F2 = 'f2', 'Fixed feature F2'
    P_F3, _F3 = 'f3', 'Fixed feature F3'
    P_OUTPUT_MATRIX, _OUTPUT_MATRIX = 'outScoreMatrix', 'Output score matrix'

    @classmethod
    def displayName(cls) -> str:
        return 'Spectral Index Optimizer'

    def shortDescription(self) -> str:
        return 'This algorithm finds the optimal two-feature index by modelling a target variable via linear ' \
               'regression.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'The regression dataset.'),
            (self._FORMULAR, 'The formular with variable features A and B to be optimized, '
                             'and up to three fixed features F1, F2 and F3.'),
            (self._MAX_FEATURES, 'Limit the number of features to be evaluated. Default is to use all features.'),
            (self._F1, 'Specify to use a fixed feature F1 in the formular.'),
            (self._F2, 'Specify to use a fixed feature F2 in the formular.'),
            (self._F3, 'Specify to use a fixed feature F3 in the formular.'),
            (self._OUTPUT_MATRIX, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Regression.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRegressionDataset(self.P_DATASET, self._DATASET)
        self.addParameterString(self.P_FORMULAR, self._FORMULAR, '(A-B) / (A+B)')
        self.addParameterInt(self.P_MAX_FEATURES, self._MAX_FEATURES, None, True, 2, None, True)
        self.addParameterInt(self.P_F1, self._F1, None, True, 1, None, True)
        self.addParameterInt(self.P_F2, self._F2, None, True, 1, None, True)
        self.addParameterInt(self.P_F3, self._F3, None, True, 1, None, True)
        self.addParameterRasterDestination(self.P_OUTPUT_MATRIX, self._OUTPUT_MATRIX)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        formular = self.parameterAsString(parameters, self.P_FORMULAR, context)
        maxFeatures = self.parameterAsInt(parameters, self.P_MAX_FEATURES, context)
        f1No = self.parameterAsInt(parameters, self.P_F1, context)
        f2No = self.parameterAsInt(parameters, self.P_F2, context)
        f3No = self.parameterAsInt(parameters, self.P_F3, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_MATRIX, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            dump = RegressorDump.fromDict(Utils.pickleLoad(filenameDataset))
            features = np.array(dump.features)
            targets = dump.targets
            X = np.array(dump.X, np.float32)
            y = np.array(dump.y, np.float32)

            F1 = F2 = F3 = None
            if f1No is not None:
                F1 = X[:, f1No - 1]
            if f2No is not None:
                F2 = X[:, f2No - 1]
            if f3No is not None:
                F3 = X[:, f3No - 1]

            if maxFeatures is not None:
                maxFeatures = min(maxFeatures, len(features))
                select = np.round(np.linspace(0, len(features) - 1, maxFeatures)).astype(int)
                features = features[select]
                X = X[:, select]

            feedback.pushInfo('Used features:')
            for featureNo, feature in enumerate(features, 1):
                feedback.pushInfo(f'{featureNo}: {feature}')
            nfeatures = len(features)
            ntargets = len(targets)
            olsr = LinearRegression()
            nbands = ntargets * 3
            scores = np.full((nbands, nfeatures, nfeatures), nan)
            feedback.pushInfo('Scores (A, B): RMSE, MAE, R2')
            for ai in range(nfeatures):
                feedback.setProgress(ai / nfeatures * 100)
                A = X[:, ai]
                for bi in range(ai + 1, nfeatures):
                    B = X[:, bi]
                    for yi in range(ntargets):
                        S = eval(formular, {'A': A, 'B': B, 'F1': F1, 'F2': F2, 'F3': F3})
                        assert isinstance(S, np.ndarray)
                        S = S.reshape((-1, 1))
                        Y = y[:, yi].flatten()
                        olsr.fit(S, Y)
                        yP = olsr.predict(S)

                        rmse = mean_squared_error(Y, yP) ** 0.5
                        mae = mean_absolute_error(Y, yP)
                        r2 = r2_score(Y, yP)
                        scores[yi * 3 + 0, ai, bi] = scores[yi * 3 + 0, bi, ai] = rmse
                        scores[yi * 3 + 1, ai, bi] = scores[yi * 3 + 1, bi, ai] = mae
                        scores[yi * 3 + 2, ai, bi] = scores[yi * 3 + 2, bi, ai] = r2

            bandNames = list()
            scoreNames = ['RMSE', 'MAE', 'R^2']
            for target in targets:
                for scoreName in scoreNames:
                    bandNames.append(f'{target.name} - {scoreName}')

            writer = Driver(filename).createFromArray(scores)
            for bandNo, bandName in enumerate(bandNames, 1):
                writer.setBandName(bandName, bandNo)
            writer.setNoDataValue(nan)
            writer.setMetadataItem('features', list(features))
            result = {self.P_OUTPUT_MATRIX: filename}

            self.toc(feedback, result)

        return result
