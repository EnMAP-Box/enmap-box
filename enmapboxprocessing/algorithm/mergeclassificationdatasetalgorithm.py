from collections import OrderedDict
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsProcessing)
from typeguard import typechecked


@typechecked
class MergeClassificationDatasetsAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASETS, _DATASETS = 'datasets', 'Datasets'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputClassificationDataset', 'Output dataset'

    def displayName(self) -> str:
        return 'Merge classification datasets'

    def shortDescription(self) -> str:
        return 'Merges a list of classification datasets.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASETS, 'Classification datasets to be merged.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterMultipleLayers(self.P_DATASETS, self._DATASETS, QgsProcessing.TypeFile, None)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        pklFilenames = self.parameterAsFileList(parameters, self.P_DATASETS, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # read all datasets
            dumps = list()
            for pklFilename in pklFilenames:
                try:
                    dumps.append(ClassifierDump.fromDict(Utils.pickleLoad(pklFilename)))
                except Exception:
                    raise QgsProcessingException(f'invalid classification dataset: {pklFilename}')

            # Check if each dataset contains the same category names.
            # If so, the resulting categories will match input categories.
            categories = OrderedDict()
            features = dumps[0].features
            for dump in dumps:
                for category in dump.categories:
                    if category.name in categories:
                        if categories[category.name].value != category.value:
                            raise QgsProcessingException(
                                f'category value mismatch for category named "{category.name}": '
                                f'{categories[category.name].value} != {category.value}'
                            )
                    else:
                        categories[category.name] = category

                if dump.features != features:
                    raise QgsProcessingException(f'feature names do not match:\n{dump.features}\n{dumps[0].features}')

            # merge datasets
            categories = list(categories.values())
            X = np.concatenate([dump.X for dump in dumps])
            y = np.concatenate([dump.y for dump in dumps])
            dump = ClassifierDump(categories=categories, features=features, X=X, y=y)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)
            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)

        return result
