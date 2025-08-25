import re
from os.path import join, dirname
from typing import Dict, Any, List, Tuple

import processing
from qgis.core import QgsProcessingOutputRasterLayer, QgsProcessingException, QgsProcessingContext, \
    QgsProcessingFeedback, QgsRasterLayer

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils


@typechecked
class SpectralIndexLayerAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_FORMULA, _FORMULA = 'formula', 'Formula'
    P_BAND_MAPPING, _BAND_MAPPING = 'bandMapping', 'Band mapping'
    P_LAYER_NAME, _LAYER_NAME = 'layerName', 'Layer name'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    Bands = Utils.jsonLoad(join(dirname(__file__), 'spyndex/data/bands.json'))
    Constants = Utils.jsonLoad(join(dirname(__file__), 'spyndex/data/constants.json'))
    Indices = Utils.jsonLoad(join(dirname(__file__), 'spyndex/data/spectral-indices-dict.json'))['SpectralIndices']
    Indices = {k: v for k, v in Indices.items() if v['application_domain'] not in ['radar', 'kernel']}

    linkGitHub = EnMAPProcessingAlgorithm.htmlLink('https://github.com/davemlz', 'David Montero Loaiza')
    linkAsiIndices = EnMAPProcessingAlgorithm.htmlLink(
        'https://awesome-ee-spectral-indices.readthedocs.io/en/latest/list.html',
        'Awesome Spectral Indices'
    )
    linkAsiBands = EnMAPProcessingAlgorithm.htmlLink(
        'https://awesome-ee-spectral-indices.readthedocs.io/en/latest/index.html#expressions',
        'ASI bands'
    )

    def displayName(self) -> str:
        return 'Spectral index layer'

    def shortDescription(self) -> str:

        return f'Use a predefined spectral index from the list of {self.linkAsiIndices} or create a custom index.\n' \
               f'Credits: the Awesome Spectral Indices project provides a ready-to-use curated list ' \
               f'of Spectral Indices for Remote Sensing applications, maintained by {self.linkGitHub}. \n' \
               f'Note that the list of available indices was last updated on 2025-08-11. ' \
               f'Should you need other indices added after this date, please file an issue.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        helpParameters = [
            (self._RASTER, 'A spectral raster layer.'),
            (self._FORMULA, 'Name of a predefined index (e.g. NDVI) or '
                            'a custom formula (e.g. (N-R)/(N+R)) to be created.\n'
                            f'Here is the list of {self.linkAsiIndices}.\n'
                            f'In a custom formula use '
                            f'i) the predefined {self.linkAsiBands}, '
                            'ii) a band matching a specific wavelength (e.g. r123 for the band nearest to 123 nm, or '
                            'iii) a specific band (e.g. r@42 for the band 42).'),
            (self._LAYER_NAME, 'Output layer name.'),
            (self._BAND_MAPPING, 'Specify to map ASI bands and constants manually. '
                                 'If not specified, ASI bands are mapped automatically to the nearest wavebands.')
        ]
        return helpParameters

    def group(self):
        return Group.RasterAnalysis.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterString(self.P_FORMULA, self._FORMULA, '', False)
        self.addParameterString(self.P_LAYER_NAME, self._LAYER_NAME, None, False, True)

        defaultValue = list()
        for k in self.Bands:
            defaultValue.append(k)
            defaultValue.append('')
        for k in self.Constants:
            defaultValue.append(k)
            defaultValue.append(self.Constants[k]['default'])
        self.addParameterMatrix(
            self.P_BAND_MAPPING, self._BAND_MAPPING, len(self.Bands) + len(self.Constants), True,
            ['Band/Constant', 'Number/Value'], defaultValue, True, True
        )

        self.addOutput(QgsProcessingOutputRasterLayer(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER))

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        formula = self.parameterAsString(parameters, self.P_FORMULA, context)
        layerName = self.parameterAsString(parameters, self.P_LAYER_NAME, context)

        # init mapping derived from layer
        mapping = self.bandMapping(raster)

        # update mapping with defaults
        for k, v in self.Constants.items():
            if v['default'] is None:
                continue
            mapping[k] = v['default']

        # update mapping with user input
        mapping2 = self.parameterAsMatrix(parameters, self.P_BAND_MAPPING, context)
        for k, v in zip(mapping2[0::2], mapping2[1::2]):
            if v == '' or v is None:
                continue
            if k in self.Bands:
                mapping[k] = int(v)
            elif k in self.Constants:
                mapping[k] = float(v)
            else:
                raise QgsProcessingException(f'unknown identifier: "{k}"')

        # update mapping with bands from r123 syntax
        reader = RasterReader(raster)
        for k in set(re.findall(r'r\d+', formula)):
            wavelength = float(k[1:])
            bandNo = reader.findWavelength(wavelength)
            mapping[k] = bandNo

        # update mapping with bands from r@42 syntax
        for k in set(re.findall(r'r@\d+', formula)):
            bandNo = int(k[2:])
            mapping[k] = bandNo

        raster = raster.clone()
        raster.setName('r')  # use "r" as a short layer name

        expression = self.asiFormulaToRasterCalcFormula(formula, raster, mapping)
        if formula in self.Indices:
            feedback.pushInfo(f'ASI formula: {self.Indices[formula]['formula']}')
        else:
            feedback.pushInfo('ASI formula: ' + formula)
        feedback.pushInfo('Virtual raster expression: ' + expression)

        result = processing.run(
            "native:virtualrastercalc",
            {
                'LAYERS': [raster],
                'EXPRESSION': expression,
                'LAYER_NAME': layerName
            }
        )
        layer: QgsRasterLayer = result['OUTPUT']
        if formula in self.Indices:
            for k, v in self.Indices[formula].items():
                layer.setCustomProperty('SI:' + k, v)
        else:
            layer.setCustomProperty('SI:formula', formula)
        context.temporaryLayerStore().addMapLayer(layer)
        result = {self.P_OUTPUT_RASTER: layer.id()}
        return result

    @classmethod
    def asiFormulaToRasterCalcFormula(cls, formula: str, layer: QgsRasterLayer, mapping: Dict[str, float]) -> str:
        if formula in cls.Indices:  # replace short name by actual formula
            formula = cls.Indices[formula]['formula']

        # check for unmapped ASI bands
        for k in cls.Bands:
            if k in formula and k not in mapping:
                raise QgsProcessingException(f'unmapped ASI band: "{k}"')

        # check for unmapped Constants
        for k in cls.Constants:
            if k in formula and k not in mapping:
                raise QgsProcessingException(f'unmapped constant: "{k}"')

        for key in sorted(mapping, key=len, reverse=True):
            if key in cls.Bands:
                formula = formula.replace(key, f'"$@{mapping[key]}"')
            elif key in cls.Constants:
                formula = formula.replace(key, f'{mapping[key]}')
            elif key.startswith('r'):
                formula = formula.replace(key, f'"$@{mapping[key]}"')
            else:
                raise QgsProcessingException(f'unknown identifier: "{key}"')

        formula = formula.replace('$', layer.name())
        formula = formula.replace('**', '^')

        return formula

    @classmethod
    def bandMapping(cls, layer: QgsRasterLayer) -> Dict[str, int]:
        reader = RasterReader(layer)
        mapping = {}
        for key, value in cls.Bands.items():
            targetWavelength = (value['min_wavelength'] + value['max_wavelength']) / 2
            bandNo = reader.findWavelength(targetWavelength)
            if bandNo is not None:
                bandWavelength = reader.wavelength(bandNo)
                if (bandWavelength > value['min_wavelength']) and (bandWavelength < value['max_wavelength']):
                    mapping[key] = bandNo
        return mapping
