from os.path import join
from random import randint
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClassifierDump, Category, checkSampleShape, RegressorDump, Target
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class PrepareRegressionDatasetFromSynthMixAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Classification dataset'
    P_N, _N = 'n', 'Number of mixtures per class'
    P_BACKGROUND, _BACKGROUND = 'background', 'Proportion of background mixtures (%)'
    P_INCLUDE_ENDMEMBER, _INCLUDE_ENDMEMBER = 'includeEndmember', 'Include original endmembers'
    P_MIXING_PROBABILITIES, _MIXING_PROBABILITIES = 'mixingProbabilities', 'Mixing complexity probabilities'
    P_ALLOW_WITHINCLASS_MIXTURES, _ALLOW_WITHINCLASS_MIXTURES = 'allowWithinClassMixtures', 'Allow within-class mixtures'
    P_CLASS_PROBABILITIES, _CLASS_PROBABILITIES = 'classProbabilities', 'Class probabilities'
    P_OUTPUT_FOLDER, _OUTPUT_FOLDER = 'outputFolder', 'Output folder'

    @classmethod
    def displayName(cls) -> str:
        return 'Create regression dataset (SynthMix from classification dataset)'

    def shortDescription(self) -> str:
        return 'Create synthetically mixed regression datasets, one for each category. ' \
               'Results are stored as <category.name>.pkl files inside the destination folder.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'A classification dataset with spectral endmembers used for synthetical mixing.'),
            (self._N, 'Number of mixtures per class'),
            (self._BACKGROUND, 'Proportion of background mixtures.'),
            (self._INCLUDE_ENDMEMBER, 'Whether to include the original library spectra into the dataset.'),
            (self._MIXING_PROBABILITIES, 'A list of probabilities for using 2, 3, 4, ... endmember mixing models. '
                                         'Trailing 0 probabilities can be skipped. The default values of 0.5, 0.5,'
                                         'results in 50% 2-endmember and 50% 3-endmember models.'),
            (self._ALLOW_WITHINCLASS_MIXTURES, 'Whether to allow mixtures with profiles belonging to the same class.'),
            (self._CLASS_PROBABILITIES, 'A list of probabilities for drawing profiles from each class. '
                                        'If not specified, class probabilities are proportional to the class size.'),
            (self._OUTPUT_FOLDER, self.FolderDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_DATASET, self._DATASET)
        self.addParameterInt(self.P_N, self._N, 1000, False, 0)
        self.addParameterInt(self.P_BACKGROUND, self._BACKGROUND, 0, False, 0, 100)
        self.addParameterBoolean(self.P_INCLUDE_ENDMEMBER, self._INCLUDE_ENDMEMBER, True)
        self.addParameterString(self.P_MIXING_PROBABILITIES, self._MIXING_PROBABILITIES, '0.5, 0.5', False, True)
        self.addParameterBoolean(self.P_ALLOW_WITHINCLASS_MIXTURES, self._ALLOW_WITHINCLASS_MIXTURES, True)
        self.addParameterString(self.P_CLASS_PROBABILITIES, self._CLASS_PROBABILITIES, None, False, True)
        self.addParameterFolderDestination(self.P_OUTPUT_FOLDER, self._OUTPUT_FOLDER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        self.n = self.parameterAsInt(parameters, self.P_N, context)
        self.background = self.parameterAsInt(parameters, self.P_BACKGROUND, context)
        self.includeEndmember = self.parameterAsBoolean(parameters, self.P_INCLUDE_ENDMEMBER, context)
        self.mixingProbabilities = self.parameterAsValues(parameters, self.P_MIXING_PROBABILITIES, context)
        self.allowWithinClassMixtures = self.parameterAsBoolean(parameters, self.P_ALLOW_WITHINCLASS_MIXTURES, context)
        self.classProbabilities = self.parameterAsValues(parameters, self.P_CLASS_PROBABILITIES, context)
        foldername = self.parameterAsFileOutput(parameters, self.P_OUTPUT_FOLDER, context)

        with open(join(foldername, 'processing.log'), 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            dump = ClassifierDump(**Utils.pickleLoad(filenameDataset))
            self.X = dump.X
            self.y = dump.y
            self.categories = dump.categories
            feedback.pushInfo(
                f'Load classification dataset: X=array{list(self.X.shape)} y=array{list(self.y.shape)} categories={[c.name for c in self.categories]}')

            if self.classProbabilities is None:
                self.classProbabilities = list()
                for category in self.categories:
                    self.classProbabilities.append(np.average(self.y == category.value))

            for category in self.categories:
                filename = join(foldername, category.name + '.pkl')
                X, y = self.mixCategory(category)

                checkSampleShape(X, y, raise_=True)

                features = [f'Band {i + 1}' for i in range(X.shape[1])]
                dump = RegressorDump([Target(category.name, category.color)], features, X, y)
                Utils.pickleDump(dump.__dict__, filename)

            result = {self.P_OUTPUT_FOLDER: foldername}
            self.toc(feedback, result)

        return result

    def mixCategory(self, targetCategory: Category):

        targetIndex = self.categories.index(targetCategory)
        features, labels = self.X.T, self.y.flatten()
        classes = len(self.categories)
        classProbabilities = {category.value: v for category, v in zip(self.categories, self.classProbabilities)}
        mixingComplexities = {i: v for i, v in enumerate(self.mixingProbabilities, 2)}
        targetRange = [0, 1]

        # cache label indices and setup 0%/100% fractions from class labels
        indices = dict()
        zeroOneFractions = np.zeros((classes, features.shape[1]), dtype=np.float32)
        for i, category in enumerate(self.categories):
            indices[category.value] = np.where(labels == category.value)[0]
            zeroOneFractions[i, indices[category.value]] = 1.

        # create mixtures
        mixtures = list()
        fractions = list()

        classProbabilities2 = {k: v / (1 - classProbabilities[targetCategory.value])
                               for k, v in classProbabilities.items()
                               if k != targetCategory.value}
        for i in range(self.n):
            complexity = np.random.choice(list(mixingComplexities.keys()), p=list(mixingComplexities.values()))

            isBackground = self.background >= randint(1, 100)

            if isBackground:
                drawnLabels = list(
                    np.random.choice(
                        list(classProbabilities2.keys()), size=1, replace=False, p=list(classProbabilities2.values())
                    )
                )
            else:
                drawnLabels = [targetCategory.value]

            if self.allowWithinClassMixtures:
                drawnLabels.extend(np.random.choice(list(classProbabilities.keys()), size=complexity - 1, replace=True,
                                                    p=list(classProbabilities.values())))
            else:
                drawnLabels.extend(
                    np.random.choice(list(classProbabilities2.keys()), size=complexity - 1, replace=False,
                                     p=list(classProbabilities2.values())))

            drawnIndices = [np.random.choice(indices[label]) for label in drawnLabels]
            drawnFeatures = features[:, drawnIndices]
            drawnFractions = zeroOneFractions[:, drawnIndices]

            randomWeights = list()
            for i in range(complexity - 1):
                if i == 0:
                    weight = np.random.random() * (targetRange[1] - targetRange[0]) + targetRange[0]
                else:
                    weight = np.random.random() * (1. - sum(randomWeights))
                randomWeights.append(weight)
            randomWeights.append(1. - sum(randomWeights))

            assert sum(randomWeights) == 1.
            mixtures.append(np.sum(drawnFeatures * randomWeights, axis=1))
            fractions.append(np.sum(drawnFractions * randomWeights, axis=1)[targetIndex])

        if self.includeEndmember:
            mixtures.extend(features.T)
            fractions.extend(np.float32(labels == targetCategory.value))  # 1. for target class, 0. for the rest

        X = np.array(mixtures, dtype=np.float32)
        y = np.array(fractions, dtype=np.float32)[None].T

        return X, y
