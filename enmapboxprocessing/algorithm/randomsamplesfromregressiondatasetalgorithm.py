from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.algorithm.randomsamplesfromclassificationdatasetalgorithm import \
    RandomSamplesFromClassificationDatasetAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClassifierDump, Category, RegressorDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class RandomSamplesFromRegressionDatasetAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Regression dataset'
    P_BINS, _BINS = 'bins', 'Number of stratification bins'
    P_N, _N = 'n', 'Number of samples per bin'
    P_REPLACE, _REPLACE = 'replace', 'Draw with replacement'
    P_PROPORTIONAL, _PROPORTIONAL = 'proportional', 'Draw proportional'
    P_SEED, _SEED = 'seed', 'Random seed'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputDatasetRandomSample', 'Output dataset'
    P_OUTPUT_COMPLEMENT, _OUTPUT_COMPLEMENT = 'outputDatasetRandomSampleComplement', 'Output dataset complement'

    def displayName(self) -> str:
        return 'Random samples from regression dataset'

    def shortDescription(self) -> str:
        return 'Split a dataset by randomly drawing samples.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Regression dataset pickle file with feature data X and target data y to draw from.'),
            (self._BINS, 'Number of bins used to stratify the target range.'),
            (self._N,
             'Number of samples to draw from each bin. '
             'Set a single value N to draw N samples for each bin. '
             'Set a list of values N1, N2, ... Ni, ... to draw Ni samples for bin i.'),
            (self._REPLACE, 'Whether to draw samples with replacement.'),
            (self._PROPORTIONAL,
             'Whether to interprete number of samples N or Ni as percentage to be drawn from each bin.'),
            (self._SEED, 'The seed for the random generator can be provided.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination + 'Stores sampled data.'),
            (self._OUTPUT_COMPLEMENT, self.PickleFileDestination + 'Stores remaining data that was not sampled.')
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRegressionDataset(self.P_DATASET, self._DATASET)
        self.addParameterInt(self.P_BINS, self._BINS, 1, False, 1)
        self.addParameterString(self.P_N, self._N)
        self.addParameterBoolean(self.P_REPLACE, self._REPLACE, False, advanced=True)
        self.addParameterBoolean(self.P_PROPORTIONAL, self._PROPORTIONAL, False, advanced=True)
        self.addParameterInt(self.P_SEED, self._SEED, None, True, 1, advanced=True)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)
        self.addParameterFileDestination(
            self.P_OUTPUT_COMPLEMENT, self._OUTPUT_COMPLEMENT, self.PickleFileFilter, None, True, False
        )

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        dump = self.parameterAsRegressorDump(parameters, self.P_DATASET, context)
        bins = self.parameterAsInt(parameters, self.P_BINS, context)
        N = self.parameterAsValues(parameters, self.P_N, context)
        replace = self.parameterAsBoolean(parameters, self.P_REPLACE, context)
        proportional = self.parameterAsBoolean(parameters, self.P_PROPORTIONAL, context)
        seed = self.parameterAsInt(parameters, self.P_SEED, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)
        filename2 = self.parameterAsFileOutput(parameters, self.P_OUTPUT_COMPLEMENT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            feedback.pushInfo(
                f'Load dataset: X=array{list(np.shape(dump.X))} y=array{list(np.shape(dump.y))} targets={[t.name for t in dump.targets]}')

            if seed is not None:
                np.random.seed(seed)

            # draw samples
            indices = list()
            categories = [Category(i, f'Bin {i + 1}', None) for i in range(bins)]
            for i, target in enumerate(dump.targets):
                feedback.pushInfo(f'Target: {target.name}')
                ymin = np.min(dump.y[:, i])
                ymax = np.max(dump.y[:, i])
                y = np.array([int(round(v)) for v in (dump.y[:, i] - ymin) / ymax * (bins - 1)])
                dump2 = ClassifierDump(categories, dump.features, dump.X, y)
                indices_, _ = RandomSamplesFromClassificationDatasetAlgorithm.drawSamples(
                    N, dump2, proportional, replace, feedback
                )
                indices.extend(indices_)
            indices = list(set(indices))
            indices2 = np.full((dump.X.shape[0],), True, bool)
            indices2[indices] = False

            # store sample
            dump2 = RegressorDump(dump.targets, dump.features, dump.X[indices], dump.y[indices], None)
            Utils.pickleDump(dump2.__dict__, filename)

            # store conmplement
            if filename2 is not None:
                dump2 = RegressorDump(dump.targets, dump.features, dump.X[indices2], dump.y[indices2], None)
                Utils.pickleDump(dump2.__dict__, filename2)

            result = {self.P_OUTPUT_DATASET: filename, self.P_OUTPUT_COMPLEMENT: filename2}
            self.toc(feedback, result)

        return result
