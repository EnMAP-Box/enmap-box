from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class SubsetRasterBandsAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_BAND_LIST, _BAND_LIST = 'bandList', 'Selected bands'
    P_EXCLUDE_BAD_BANDS, _EXCLUDE_BAD_BANDS = 'excludeBadBands', 'Exclude bad bands'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def displayName(self):
        return 'Subset raster layer bands'

    def shortDescription(self):
        return 'Subsets raster layer bands and stores the result as a VRT file.' \
               'This is a slimmed down version of the more powerful "Translate raster layer" algorithm.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Source raster layer.'),
            (self._BAND_LIST, 'Bands to subset and rearrange. '
                              'An empty selection defaults to all bands in native order.'),
            (self._EXCLUDE_BAD_BANDS, 'Whether to exclude bad bands.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.RasterMiscellaneous.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterBandList(self.P_BAND_LIST, self._BAND_LIST, None, self.P_RASTER, True)
        self.addParameterBoolean(self.P_EXCLUDE_BAD_BANDS, self._EXCLUDE_BAD_BANDS, False)
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        bandList = self.parameterAsInts(parameters, self.P_BAND_LIST, context)
        excludeBadBands = self.parameterAsBoolean(parameters, self.P_EXCLUDE_BAD_BANDS, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: raster,
            alg.P_BAND_LIST: bandList,
            alg.P_EXCLUDE_BAD_BANDS: excludeBadBands,
            alg.P_COPY_METADATA: True,
            alg.P_CREATION_PROFILE: self.DefaultVrtCreationProfile,
            alg.P_OUTPUT_RASTER: filename
        }
        self.runAlg(alg, parameters, None, feedback, context, True)

        return {self.P_OUTPUT_RASTER: filename}
