from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.parameter.processingparametercodeeditwidget import ProcessingParameterCodeEditWidgetWrapper
from enmapboxprocessing.rasterwriter import RasterWriter
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingParameterString)
from typeguard import typechecked


@typechecked
class VrtBandMathAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_BAND_LIST, _BAND_LIST = 'bandList', 'Selected bands'
    P_CODE, _CODE = 'code', 'Code'
    P_DATA_TYPE, _DATA_TYPE = 'dataType', 'Data type'
    P_NODATA, _NODATA = 'noData', 'No data value'
    P_BAND_NAME, _BAND_NAME = 'bandName', 'Band name'
    P_OVERLAP, _OVERLAP = 'overlap', 'Buffer radius'
    P_OUTPUT_VRT, _OUTPUT_VRT = 'outputVrt', 'Output VRT layer'

    linkNumpy = EnMAPProcessingAlgorithm.htmlLink('https://numpy.org/doc/stable/reference/', 'NumPy')
    linkVrtPixelFunction = EnMAPProcessingAlgorithm.htmlLink(
        'https://gdal.org/drivers/raster/vrt.html#using-derived-bands-with-pixel-functions-in-python',
        'VRT Python Pixel Function')

    def displayName(self) -> str:
        return 'VRT band math'

    def shortDescription(self) -> str:
        return f'Create a single-band VRT raster layer specifying a {self.linkVrtPixelFunction}. ' \
               f'Use any {self.linkNumpy}-based arithmetic, or even arbitrary Python code.'

    def helpParameters(self) -> List[Tuple[str, str]]:

        return [
            (self._RASTER, 'Input raster layer.'),
            (self._BAND_LIST, 'List of input bands.'),
            (self._CODE, 'The mathematical calculation to be performed on the selected input bands in_ar.'
                         'Result must be copied to out_ar.\n'
                         f'For detailed usage information read the {self.linkVrtPixelFunction} docs.'),
            (self._DATA_TYPE, 'Output data type.'),
            (self._NODATA, 'Output no data value.'),
            (self._BAND_NAME, 'Output band name.'),
            (self._OVERLAP, 'The number of columns and rows to read from the neighbouring blocks. '
                            'Needs to be specified only when performing spatial operations, '
                            'to avoid artifacts at block borders.'),
            (self._OUTPUT_VRT, 'VRT file destination.'),
        ]

    def group(self):
        return Group.Test.value + Group.RasterAnalysis.value

    def addParameterMathCode(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        param = QgsProcessingParameterString(name, description, optional=optional)
        param.setMetadata({'widget_wrapper': {'class': ProcessingParameterCodeEditWidgetWrapper}})
        param.setDefaultValue(defaultValue)
        self.addParameter(param)
        self.flagParameterAsAdvanced(name, advanced)

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterBandList(self.P_BAND_LIST, self._BAND_LIST, parentLayerParameterName=self.P_RASTER)
        self.addParameterMathCode(self.P_CODE, self._CODE, None)
        self.addParameterEnum(self.P_DATA_TYPE, self._DATA_TYPE, self.O_DATA_TYPE, False, self.Float32, True, True)
        self.addParameterFloat(self.P_NODATA, self._NODATA, None, True, None, None, True)
        self.addParameterString(self.P_BAND_NAME, self._BAND_NAME, None, False, True, True)
        self.addParameterInt(self.P_OVERLAP, self._OVERLAP, None, True, 0, None, True)
        self.addParameterVrtDestination(self.P_OUTPUT_VRT, self._OUTPUT_VRT)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        bandList = self.parameterAsInts(parameters, self.P_BAND_LIST, context)
        code = self.parameterAsString(parameters, self.P_CODE, context)
        dataType = self.O_DATA_TYPE[self.parameterAsEnum(parameters, self.P_DATA_TYPE, context)]
        noDataValue = self.parameterAsFloat(parameters, self.P_NODATA, context)
        bandName = self.parameterAsString(parameters, self.P_BAND_NAME, context)
        overlap = self.parameterAsInt(parameters, self.P_OVERLAP, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_VRT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # create base VRT with proper CRS and source band definitions
            ds: gdal.Dataset = gdal.Translate(filename, raster.source(), bandList=bandList, noData="none")
            ds.SetMetadata({})
            for i in range(ds.RasterCount):
                ds.GetRasterBand(i + 1).SetMetadata({})
            ds = None

            # edit base VRT
            with open(filename) as file:
                text0 = file.read()

            # - take CRS definition
            text = text0[:text0.find('<VRTRasterBand')]

            # - add pixel function logic
            code_ = f'<VRTRasterBand dataType="{dataType}" band="1" subClass="VRTDerivedRasterBand">\n' \
                    f'  <PixelFunctionType>ufunc</PixelFunctionType>\n' \
                    f'  <PixelFunctionLanguage>Python</PixelFunctionLanguage>\n' \
                    f'  <PixelFunctionCode><![CDATA[\n' \
                    f'{code}\n' \
                    f'  ]]></PixelFunctionCode>\n' \
                    f'  <BufferRadius>{overlap}</BufferRadius>\n' \
                    f'    '
            text += code_

            # - take source definitions
            for line in text0[text0.find('<SimpleSource>'):].splitlines(keepends=True):
                if ('VRTRasterBand' in line) or ('VRTDataset' in line):  # skip thoose
                    continue
                text += line
            text += '  </VRTRasterBand>\n</VRTDataset>\n'

            # write final VRT
            with open(filename, 'w') as file:
                file.write(text)
            ds = gdal.Open(filename)
            writer = RasterWriter(ds)
            writer.setNoDataValue(noDataValue, 1)
            writer.setBandName(bandName, 1)
            writer.setScale(1, 1)  # unset any input scaling (fixes #1389)
            writer.setOffset(0, 1)  # unset any input offset

            # prepare results
            result = {self.P_OUTPUT_VRT: filename}

            self.toc(feedback, result)

        return result
