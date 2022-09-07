from collections import OrderedDict
from typing import Dict, Any, List, Tuple, Optional

from osgeo import gdal

from enmapboxprocessing.algorithm.vrtbandmathalgorithm import VrtBandMathAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException,
                       QgsRasterLayer)
from typeguard import typechecked


@typechecked
class CreateSpectralIndicesAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_INDICES, _INDICES = 'indices', 'Indices'
    P_SCALE, _SCALE = 'scale', 'Scale factor'

    P_A, _A = 'A', 'Aerosols band'
    P_B, _B = 'B', 'Blue band'
    P_G, _G = 'G', 'Green band'
    P_R, _R = 'R', 'Red band'
    P_RE1, _RE1 = 'RE1', 'Red Edge 1 band'
    P_RE2, _RE2 = 'RE2', 'Red Edge 2 band'
    P_RE3, _RE3 = 'RE3', 'Red Edge 3 band'
    P_RE4, _RE4 = 'RE4', 'Red Edge 4 band'
    P_N, _N = 'N', 'NIR band'
    P_S1, _S1 = 'S1', 'SWIR 1 band'
    P_S2, _S2 = 'S2', 'SWIR 2 band'
    P_T1, _T1 = 'T1', 'Thermal 1 band'
    P_T2, _T2 = 'T2', 'Thermal 2 band'

    P_L, _L = 'L', 'Canopy background adjustment'
    P_g, _g = 'g', 'Gain factor'
    P_C1, _C1 = 'C1', 'Coefficient 1 for the aerosol resistance term'
    P_C2, _C2 = 'C2', 'Coefficient 2 for the aerosol resistance term'
    P_cexp, _cexp = 'cexp', 'Exponent used for OCVI'
    P_nexp, _nexp = 'nexp', 'Exponent used for GDVI'
    P_alpha, _alpha = 'alpha', 'Weighting coefficient used for WDRVI'
    P_gamma, _gamma = 'gamma', 'Weighting coefficient used for ARVI'
    P_sla, _sla = 'sla', 'Soil line slope'
    P_slb, _slb = 'slb', 'Soil line intercept'

    P_OUTPUT_VRT, _OUTPUT_VRT = 'outputVrt', 'Output VRT layer'

    ShortNames = ['A', 'B', 'G', 'R', 'RE1', 'RE2', 'RE3', 'RE4', 'N', 'S1', 'S2', 'T1', 'T2']

    WavebandMapping = {  # (<center wavelength>, <fwhm>)
        'A': (443, 21), 'B': (492, 66), 'G': (560, 36), 'R': (665, 31), 'RE1': (704, 15), 'RE2': (741, 15),
        'RE3': (783, 20), 'RE4': (865, 21), 'N': (833, 106), 'S1': (1614, 91), 'S2': (2202, 175), 'T1': (10895, 590),
        'T2': (12005, 1010)}
    ConstantMapping = {
        'L': 1.0, 'g': 2.5, 'C1': 6.0, 'C2': 7.5, 'cexp': 1.16, 'nexp': 2.0, 'alpha': 0.1, 'gamma': 1.0, 'sla': 1.0,
        'slb': 0.0
    }
    LongNameMapping = {
        'A': 'Aerosols band', 'B': 'Blue band', 'G': 'Green band', 'R': 'Red band', 'RE1': 'Red Edge 1 band',
        'RE2': 'Red Edge 2 band', 'RE3': 'Red Edge 3 band', 'RE4': 'Red Edge 4 band', 'N': 'NIR band',
        'S1': 'SWIR 1 band', 'S2': 'SWIR 2 band', 'T1': 'Thermal 1 band', 'T2': 'Thermal 2 band',
        'L': 'Canopy background adjustment', 'g': 'Gain factor', 'C1': 'Coefficient 1 for the aerosol resistance term',
        'C2': 'Coefficient 2 for the aerosol resistance term', 'cexp': 'Exponent used for OCVI',
        'nexp': 'Exponent used for GDVI', 'alpha': 'Weighting coefficient used for WDRVI',
        'gamma': 'Weighting coefficient used for ARVI', 'sla': 'Soil line slope', 'slb': 'Soil line intercept'
    }

    IndexDatabase = Utils.jsonLoad(__file__.replace('.py', '.json'))['SpectralIndices']  # AwesomeSpectralIndices
    IndexDatabase.update(Utils.jsonLoad(__file__.replace('.py', '.other.json'))['SpectralIndices'])  # more indices

    linkAwesomeSpectralIndices = EnMAPProcessingAlgorithm.htmlLink(
        'https://awesome-ee-spectral-indices.readthedocs.io/en/latest/list.html',
        'Awesome Spectral Indices')

    def displayName(self) -> str:
        return 'Create spectral indices'

    def shortDescription(self) -> str:
        linkMaintainer = EnMAPProcessingAlgorithm.htmlLink('https://github.com/davemlz', 'David Montero Loaiza')
        return f'Create a stack of {self.linkAwesomeSpectralIndices} and/or custom indices.\n' \
               f'Credits: the Awesome Spectral Indices project provides a ready-to-use curated list ' \
               f'of Spectral Indices for Remote Sensing applications, maintained by {linkMaintainer}. \n' \
               f'Note that the list of available indices was last updated on 2021-11-15. ' \
               f'Should you need other indices added after this date, please file an issue.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        helpParameters = [
            (self._RASTER, 'A spectral raster layer.'),
            (self._INDICES, 'The list of indices to be created. Usage examples:\n'
                            'Create (predefined) NDVI: <code>NDVI</code>\n'
                            'Create stack of NDVI and EVI: <code>NDVI, EVI</code>\n'
                            'Create custom index: <code>MyNDVI = (N - R) / (N + R)</code>\n'
                            f'See the full list of predefined  {self.linkAwesomeSpectralIndices}.'),
            (self._SCALE, 'Spectral reflectance scale factor. '
                          'Some indices require data to be scaled into the 0 to 1 range. '
                          'If your data is scaled differently, specify an appropriate scale factor.'
                          'E.g. for Int16 data scaled into the 0 to 10000 range, use a value of 10000.\n'),
            ('Aerosols band (A), ..., Thermal 2 band (T2)',
             'The band mapping from source to standardized bands A, ..., T2 used in the formulas.\n'
             'If the source raster has proper wavelength information, mapping is done automatically.'),
            ('Canopy background adjustment (L), ..., Soil line intercept (slb)',
             'Standardized additional index parameters L, ..., slb used in the formulas.'),
            (self._OUTPUT_VRT, 'VRT file destination.'),
        ]
        keys = [self._A, self._B, self._G, self._R, self._RE1, self._RE2, self._RE3, self._RE4, self._N, self._S1,
                self._S2, self._T1, self._T2, self._L, self._g, self._C1, self._C2, self._cexp, self._nexp, self._alpha,
                self._gamma, self._sla, self._slb]
        helpParameters.extend([(key, '') for key in keys])
        return helpParameters

    def group(self):
        return Group.Test.value + Group.RasterAnalysis.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterString(self.P_INDICES, self._INDICES, 'NDVI', True)
        self.addParameterFloat(self.P_SCALE, self._SCALE, None, True)
        for name in self.WavebandMapping:
            description = getattr(self, '_' + name)
            self.addParameterBand(name, description, -1, self.P_RASTER, True, False, True)
        for name in self.ConstantMapping:
            description = getattr(self, '_' + name)
            self.addParameterFloat(name, description, self.ConstantMapping[name], True, None, None, True)
        self.addParameterVrtDestination(self.P_OUTPUT_VRT, self._OUTPUT_VRT)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        text = self.parameterAsString(parameters, self.P_INDICES, context)
        text = ', '.join(text.splitlines())  # multiline to comma separated list
        scale = self.parameterAsFloat(parameters, self.P_SCALE, context)
        if scale is None:
            scale = 1
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_VRT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)

            # get band mapping
            bandNos = dict()
            for name in self.WavebandMapping:
                bandNo = self.parameterAsInt(parameters, name, context)
                if bandNo is None or bandNo == -1:
                    bandNo = self.findBroadBand(raster, name, True)
                bandNos[name] = bandNo

            # eval requested indices
            indices = OrderedDict()
            for item in text.split(','):

                if '=' in item:  # custom index
                    short_name, formula = [s.strip() for s in item.split('=')]
                    if short_name in self.IndexDatabase:
                        raise QgsProcessingException(
                            f'custom index name already exists in as predefined index: {short_name}'
                        )
                    # derive bands from formular
                    formula_ = formula
                    bands = list()
                    for name in sorted(self.WavebandMapping.keys(), key=len, reverse=True):  # long names first!
                        if name in formula_:
                            bands.append(name)
                            formula_ = formula_.replace(name, '')
                    long_name = None
                    bandName = short_name
                else:  # predefined index
                    short_name = item.strip()
                    if short_name not in self.IndexDatabase:
                        raise QgsProcessingException(f'unknown index: {short_name}')
                    formula = self.IndexDatabase[short_name]['formula']
                    bands = self.IndexDatabase[short_name]['bands']
                    bands = [name for name in bands if name not in self.ConstantMapping]  # skip constants
                    long_name = self.IndexDatabase[short_name]['long_name']
                    bandName = short_name + ' - ' + long_name

                bandList = [bandNos[name] for name in bands]
                code = self.deriveParameters(short_name, formula, bands, bandList, reader, scale)
                indices[short_name] = long_name, formula, bandList, code, bandName

            # build index VRTs
            filenames = list()
            metadatas = list()
            for short_name, (long_name, formula, bandList, code, bandName) in indices.items():
                alg = VrtBandMathAlgorithm()
                parameters = {
                    alg.P_RASTER: raster,
                    alg.P_BAND_LIST: bandList,
                    alg.P_BAND_NAME: bandName,
                    alg.P_NODATA: -9999,
                    alg.P_DATA_TYPE: self.Float32,
                    alg.P_CODE: code,
                    alg.P_OUTPUT_VRT: Utils.tmpFilename(filename, short_name + '.vrt')
                }
                result = self.runAlg(alg, parameters, None, feedback2, context, True)
                filenames.append(result[alg.P_OUTPUT_VRT])
                metadatas.append({'short_name': short_name, 'long_name': long_name, 'formula': formula})

            # create stack VRT
            ds = gdal.BuildVRT(filename, filenames, separate=True)
            writer = RasterWriter(ds)
            for bandNo, (ifilename, metadata) in enumerate(zip(filenames, metadatas), 1):
                writer.setBandName(metadata['short_name'], bandNo)
                writer.setMetadataDomain(metadata, '', bandNo)
            writer = None
            ds = None

            result = {self.P_OUTPUT_VRT: filename}
            self.toc(feedback, result)

        return result

    def deriveParameters(
            self, short_name: str, formula: str, bands: List[str], bandList: List[int], reader: RasterReader,
            scale: Optional[float]
    ):

        noDataValues = [reader.noDataValue(bandNo) for bandNo in bandList]

        # add imports
        code = 'import numpy as np\n\n'

        # add constants
        extraNewLine = False
        for name in self.ConstantMapping:
            if name in formula:
                code += f'{name} = {self.ConstantMapping[name]}\n'
                extraNewLine = True

        # add ufunc
        if extraNewLine:
            code += '\n'
        code += 'def ufunc(in_ar, out_ar, *args, **kwargs):\n'

        # prepare input band variables; use the same identifier as in the formulas; also cast to Float32
        for i, name in enumerate(bands):
            if scale == 1:
                code += f'    {name} = np.float32(in_ar[{i}])\n'
            else:
                code += f'    {name} = np.float32(in_ar[{i}]) / {scale}\n'

        # add formula
        code += f'    {short_name} = {formula}\n'

        # mask noDataRegion
        for i, noDataValue in enumerate(noDataValues):
            code += f'    {short_name}[in_ar[{i}] == {noDataValue}] = -9999\n'

        # fill out_ar
        code += f'    out_ar[:] = {short_name}\n'

        return code

    @classmethod
    def findBroadBand(cls, raster: QgsRasterLayer, name: str, strict=False) -> Optional[int]:
        reader = RasterReader(raster)
        wavelength, fwhm = cls.WavebandMapping[name]
        bandNo = reader.findWavelength(wavelength)
        if bandNo is None:
            return None
        if strict:
            if abs(wavelength - reader.wavelength(bandNo)) > (fwhm / 2):
                return None
        return bandNo

    @classmethod
    def translateSentinel2Band(cls, name: str):
        return {'B1': 'A', 'B2': 'B', 'B3': 'G', 'B4': 'R', 'B5': 'RE1', 'B6': 'RE2', 'B7': 'RE3', 'B8A': 'RE4',
                'B8': 'N', 'B11': 'S1', 'B12': 'S2'}[name]

    @classmethod
    def sentinel2Visualizations(cls) -> Dict[str, Tuple[str, str, str]]:
        # rgb visualizations adopted from:
        # https://github.com/sandroklippel/qgis_gee_data_catalog/blob/master/datasets.py

        mapping = {
            'Natural color': ('B4', 'B3', 'B2'),
            'False color': ('B4', 'B8', 'B3'),
            'Color infrared': ('B8', 'B4', 'B3'),
            'Shortwave infrared 1': ('B12', 'B8', 'B4'),
            'Shortwave infrared 2': ('B12', 'B8A', 'B4'),
            'Shortwave infrared 3': ('B12', 'B8A', 'B2'),
            'Agriculture 1': ('B11', 'B8', 'B2'),
            'Agriculture 2': ('B11', 'B8A', 'B2'),
            'Atmospheric penetration / Soil': ('B12', 'B11', 'B8A'),
            'Geology': ('B12', 'B11', 'B2'),
            'Bathymetric': ('B4', 'B3', 'B1'),
            'False color urban': ('B12', 'B11', 'B4'),
            'Healthy vegetation': ('B8', 'B11', 'B2'),
            'Vegetation analysis 1': ('B8', 'B11', 'B4'),
            'Vegetation analysis 2': ('B11', 'B8', 'B4'),
            'Forestry / Recent harvest areas': ('B12', 'B8', 'B3')
        }

        mapping2 = {name: tuple(cls.translateSentinel2Band(bandName) for bandName in bandNames)
                    for name, bandNames in mapping.items()}

        return mapping2

    @classmethod
    def filterVisualizations(
            cls, visualizations: Dict[str, Tuple[str, str, str]], bandNames: List[str]
    ) -> Dict[str, Tuple[str, str, str]]:
        return {name: (redBand, greenBand, blueBand)
                for name, (redBand, greenBand, blueBand) in visualizations.items()
                if redBand in bandNames and greenBand in bandNames and blueBand in bandNames}
