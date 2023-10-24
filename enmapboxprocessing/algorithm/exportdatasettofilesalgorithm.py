from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)


@typechecked
class ExportDatasetToFilesAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Classification/Regression dataset'
    P_OUTPUT_FEATURE_FILE, _OUTPUT_FEATURE_FILE = 'outputFeatureFile', 'Output features file'
    P_OUTPUT_VALUE_FILE, _OUTPUT_VALUE_FILE = 'outputValueFile', 'Output labels file'

    @classmethod
    def displayName(cls) -> str:
        return 'Export classification/regression dataset (to text files)'

    def shortDescription(self) -> str:
        link = self.htmlLink(
            "https://force-eo.readthedocs.io/en/latest/components/higher-level/smp/index.html",
            "FORCE Higher Level Sampling Submodule"
        )
        return 'Export a classification/regression dataset to tabulated text files.\n' \
               f'The format matches that of the {link}.\n' \
               f'Example files (force_features.csv and force_labels.csv) can be found in the EnMAP-Box testdata folder).'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Dataset pickle file to be exported. '),
            (self._OUTPUT_FEATURE_FILE, self.CsvFileDestination),
            (self._OUTPUT_VALUE_FILE, self.CsvFileDestination),
        ]

    def group(self):
        return Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterPickleFile(self.P_DATASET, self._DATASET)
        self.addParameterFileDestination(self.P_OUTPUT_FEATURE_FILE, self._OUTPUT_FEATURE_FILE, self.CsvFileFilter)
        self.addParameterFileDestination(self.P_OUTPUT_VALUE_FILE, self._OUTPUT_VALUE_FILE, self.CsvFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        filenameFeatures = self.parameterAsFileOutput(parameters, self.P_OUTPUT_FEATURE_FILE, context)
        filenameLabels = self.parameterAsFileOutput(parameters, self.P_OUTPUT_VALUE_FILE, context)

        with open(filenameFeatures + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            dump = Utils().pickleLoad(filenameDataset)
            np.savetxt(filenameFeatures, dump['X'])
            np.savetxt(filenameLabels, dump['y'])

            result = {
                self.P_OUTPUT_FEATURE_FILE: filenameFeatures,
                self.P_OUTPUT_VALUE_FILE: filenameLabels
            }

            self.toc(feedback, result)
        return result
