from typing import Dict, Any, List, Tuple

from qgis._core import QgsProcessingParameterFile
from qgis.core import QgsProcessingContext, QgsProcessingFeedback

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm


@typechecked
class EniccsCloudMaskAlgorithm(EnMAPProcessingAlgorithm):
    P_PRODUCT, _PRODUCT = 'product', 'EnMAP L2A product folder'
    P_AUTO_OPTIMIZE, _AUTO_OPTIMIZE = 'autoOptimize', 'Auto optimize'
    P_SMOOTH, _SMOOTH = 'smoothOutput', 'Smooth output'
    P_CONTAMINATION, _CONTAMINATION = 'contamination', 'Contamination'
    P_PERCENTILE, _PERCENTILE = 'percentile', 'Percentile'
    P_SAMPLES, _SAMPLES = 'samples', 'Samples'
    P_BUFFER, _BUFFER = 'buffer', 'Buffer'

    def displayName(self) -> str:
        return 'EnICCS - EnMAP L2A cloud and cloud shadow mask'

    def shortDescription(self) -> str:
        return ('EnICCS - a tool for generating improved EnMAP L2A cloud and cloud shadow masks. '
                'See https://github.com/leleist/eniccs for more details.')

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._PRODUCT, 'Path to EnMAP L2A data.'),
            (self._AUTO_OPTIMIZE, 'Optimize the number of latent variables for PLS-DA automatically.'),
            (self._SMOOTH, 'Apply conservative morphological processing for smooting the output masks.'),
            (self._CONTAMINATION, 'Contamination parameter for LOF outlier detection.'),
            (self._PERCENTILE, 'Percentile for cloud-to-shadow matching routine distance threshol.'),
            (self._SAMPLES, 'Number of samples for PLS-DA training.'),
            (self._BUFFER, 'Buffer size for dilation of CCS mask outputs.')
        ]

    def group(self):
        return 'Pre-Processing'

    def groupId(self):
        return 'PreProcessing'

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_PRODUCT, self._PRODUCT, QgsProcessingParameterFile.Behavior.Folder)
        self.addParameterBoolean(self.P_AUTO_OPTIMIZE, self._AUTO_OPTIMIZE, False, True)
        self.addParameterBoolean(self.P_SMOOTH, self._SMOOTH, True, True)
        self.addParameterFloat(self.P_CONTAMINATION, self._CONTAMINATION, 0.25)
        self.addParameterInt(self.P_PERCENTILE, self._PERCENTILE, 85, True)
        self.addParameterInt(self.P_SAMPLES, self._SAMPLES, 3000, True)
        self.addParameterInt(self.P_BUFFER, self._BUFFER, 1, True)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        folder = self.parameterAsFile(parameters, self.P_PRODUCT, context)
        autoOptimize = self.parameterAsBoolean(parameters, self.P_AUTO_OPTIMIZE, context)
        contamination = self.parameterAsFloat(parameters, self.P_CONTAMINATION, context)
        percentile = self.parameterAsInt(parameters, self.P_PERCENTILE, context)
        samples = self.parameterAsInt(parameters, self.P_SAMPLES, context)
        buffer = self.parameterAsInt(parameters, self.P_BUFFER, context)

        # TODO use run_eniccs(...)

        result = {}
        return result
