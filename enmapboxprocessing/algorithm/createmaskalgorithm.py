from typing import Dict, Any, List, Tuple
from urllib.parse import urlencode

from enmapbox.provider.maskrasterdataprovider import MaskRasterDataProvider
from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsProcessingOutputRasterLayer


@typechecked
class CreateMaskAlgorithmBase(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_BAND, _BAND = 'band', 'Band'
    P_MASK_NO_DATA_VALUES, _MASK_NO_DATA_VALUES = 'maskNoDataValues', 'Mask no data values'
    P_MASK_NONFINITE_VALUES, _MASK_NONFINITE_VALUES = 'maskNonFiniteValues', 'Mask non-finite values'
    P_MASK_VALUES, _MASK_VALUES = 'maskValues', 'Mask values'
    P_MASK_VALUE_RANGES, _MASK_VALUE_RANGES = 'maskValueRanges', 'Mask value ranges'
    P_MASK_BITS, _MASK_BITS = 'maskBits', 'Mask bits'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Raster layer.'),
            (self._BAND, 'Band to be evaluated.'),
            (self._MASK_NO_DATA_VALUES, 'Whether to mask no data values.'),
            (self._MASK_NONFINITE_VALUES, 'Whether to mask non-finite values (i.e. Inf and NaN).'),
            (self._MASK_VALUES, 'Values to be masked.'),
            (self._MASK_VALUE_RANGES, 'Value-ranges to be masked.'),
            (self._MASK_BITS, 'Bits to be masked. A bit mask part is specified by the "First bit", the "Bit count" '
                              'and a list of "Values" (space- or comma-separated) to be masked.')
        ]

    def group(self):
        return Group.Masking.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterBand(self.P_BAND, self._BAND, None, self.P_RASTER)
        self.addParameterBoolean(self.P_MASK_NO_DATA_VALUES, self._MASK_NO_DATA_VALUES, True, True)
        self.addParameterBoolean(self.P_MASK_NONFINITE_VALUES, self._MASK_NONFINITE_VALUES, True, True)
        self.addParameterMatrix(self.P_MASK_VALUES, self._MASK_VALUES, 0, False, ['Value'], None, True)
        self.addParameterMatrix(
            self.P_MASK_VALUE_RANGES, self._MASK_VALUE_RANGES, 0, False, ['Minimum', 'Maximum'], None, True
        )
        self.addParameterMatrix(
            self.P_MASK_BITS, self._MASK_BITS, 0, False, ['First bit', 'Bit count', 'Values'], None, True
        )


@typechecked
class CreateMaskVirtualAlgorithm(CreateMaskAlgorithmBase):
    P_LAYER_NAME, _LAYER_NAME = 'layerName', 'Layer name'
    P_OUTPUT_MASK, _OUTPUT_MASK = 'outputMask', 'Output mask raster layer'

    def displayName(self) -> str:
        return 'Create mask raster layer (virtual)'

    def shortDescription(self) -> str:
        return 'Create an in-memory mask raster layer by evaluating a source raster layer.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return super().helpParameters() + [
            (self._LAYER_NAME, 'Output layer name.')
        ]

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        super().initAlgorithm(configuration)
        self.addParameterString(self.P_LAYER_NAME, self._LAYER_NAME, None, False, True)
        self.addOutput(QgsProcessingOutputRasterLayer(self.P_OUTPUT_MASK, self._OUTPUT_MASK))

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        bandNo = self.parameterAsBand(parameters, self.P_BAND, context)
        maskNoDataValues = self.parameterAsBoolean(parameters, self.P_MASK_NO_DATA_VALUES, context)
        maskNonFiniteValues = self.parameterAsBoolean(parameters, self.P_MASK_NONFINITE_VALUES, context)
        maskValues = self.parameterAsMatrix(parameters, self.P_MASK_VALUES, context)
        maskValueRanges = self.parameterAsMatrix(parameters, self.P_MASK_VALUE_RANGES, context)
        maskBits = self.parameterAsMatrix(parameters, self.P_MASK_BITS, context)
        layerName = self.parameterAsString(parameters, self.P_LAYER_NAME, context)

        p = MaskRasterDataProvider
        parameters = {
            p.P_Uri: raster.source(),
            p.P_Provider: raster.providerType(),
            p.P_Band: bandNo,
            p.P_MaskNoDataValues: maskNoDataValues,
            p.P_MaskNonFiniteValues: maskNonFiniteValues
        }
        if maskValues is not None:
            parameters[p.P_MaskValues] = [float(v) for v in maskValues]
        if maskValueRanges is not None:
            parameters[p.P_MaskValueRanges] = [
                (float(a), float(b)) for a, b in zip(maskValueRanges[0::2], maskValueRanges[1::2])
            ]
        if maskBits is not None:
            parameters[p.P_MaskBits] = [
                (int(first), int(count), [int(v) for v in values.replace(',', ' ').split(' ') if v != ''])
                for first, count, values in zip(maskBits[0::3], maskBits[1::3], maskBits[2::3])
            ]

        uri = '?' + urlencode(parameters)
        layer = QgsRasterLayer(uri, layerName, p.NAME)
        assert layer.isValid()
        context.temporaryLayerStore().addMapLayer(layer)
        context.addLayerToLoadOnCompletion(layer.id(), QgsProcessingContext.LayerDetails(layerName, context.project(),
                                                                                         self.P_OUTPUT_MASK))
        result = {self.P_OUTPUT_MASK: layer.id()}
        return result


@typechecked
class CreateMaskAlgorithm(CreateMaskAlgorithmBase):
    P_OUTPUT_MASK, _OUTPUT_MASK = 'outputMask', 'Output mask raster layer'

    def displayName(self) -> str:
        return 'Create mask raster layer'

    def shortDescription(self) -> str:
        return 'Create a mask raster layer by evaluating a source raster layer.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return super().helpParameters() + [
            (self._OUTPUT_MASK, self.RasterFileDestination)
        ]

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        super().initAlgorithm(configuration)
        self.addParameterRasterDestination(
            self.P_OUTPUT_MASK, self._OUTPUT_MASK, None, True, True
        )

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_MASK, context)
        alg = CreateMaskVirtualAlgorithm()
        result = self.runAlgorithm(alg, parameters, None, None, context)
        layer = context.takeResultLayer(result[alg.P_OUTPUT_MASK])
        RasterReader(layer).saveAs(filename)
        result = {self.P_OUTPUT_MASK: filename}
        return result
