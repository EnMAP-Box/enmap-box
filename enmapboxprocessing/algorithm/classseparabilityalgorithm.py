from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)


@typechecked
class ClassSeparabilityAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Test dataset'

    def displayName(self) -> str:
        return 'Class separability report'

    def shortDescription(self) -> str:
        return 'Evaluates the pair-wise class separability in terms of the Jeffries Matusita distance.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Dataset pickle file used for assessing the class separability.'),
        ]

    def group(self):
        return Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterClassificationDataset(self.P_DATASET, self._DATASET)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameSample = self.parameterAsFile(parameters, self.P_DATASET, context)

        sample = ClassifierDump(**Utils.pickleLoad(filenameSample))
        feedback.pushInfo(f'Load sample data: X{list(sample.X.shape)} y{list(sample.y.shape)}')

        self.calculateStats(sample, feedback)

        result = {}
        return result

    def calculateStats(self, sample: ClassifierDump, feedback: QgsProcessingFeedback):

        def jeffries_matusita_distance(mu1, cov1, mu2, cov2):  # provided by ChatGPT 3.5
            """
            Calculate the Jeffries-Matusita distance between two multivariate normal distributions.

            Parameters:
            - mu1: Mean vector of the first distribution.
            - cov1: Covariance matrix of the first distribution.
            - mu2: Mean vector of the second distribution.
            - cov2: Covariance matrix of the second distribution.

            Returns:
            - jm_distance: Jeffries-Matusita distance between the two distributions.
            """

            cov_avg = (cov1 + cov2) / 2.0
            diff_mean = mu1 - mu2

            try:
                cov_avg_inv = np.linalg.inv(cov_avg)
            except np.linalg.LinAlgError:
                raise ValueError("Covariance matrix must be positive definite.")

            mahalanobis_term = np.sqrt(np.dot(np.dot(diff_mean, cov_avg_inv), diff_mean))
            jm_distance = np.sqrt(2 * (1 - np.exp(-mahalanobis_term ** 2 / 2)))

            return jm_distance

        for a in range(len(sample.categories) - 1):
            for b in range(a + 1, len(sample.categories)):
                categoryA = sample.categories[a]
                validA = sample.y[:, 0] == categoryA.value
                dataA = sample.X[validA]
                muA = np.mean(dataA, 0)
                covA = np.cov(dataA, rowvar=False)

                categoryB = sample.categories[b]
                validB = sample.y[:, 0] == categoryB.value
                dataB = sample.X[validB]
                muB = np.mean(dataB, 0)
                covB = np.cov(dataB, rowvar=False)

                print()
                print(categoryA.name, 'versus', categoryB.name)
                for data, category in ((dataA, categoryA), (dataB, categoryB)):
                    if data.shape[0] < data.shape[1]:
                        feedback.pushWarning(
                            f'Category {category.name}: '
                            f'sample size ({data.shape[0]}) is smaller than number of features {data.shape[1]}. '
                            f'As a rule of thumb, have at least five times as many samples as features.'
                        )
                jm = jeffries_matusita_distance(muA, covA, muB, covB)

                print('Jeffries-Matusita Distance:', jm)
