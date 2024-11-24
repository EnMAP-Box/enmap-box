from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer,
                       QgsMapLayer)


@typechecked
class PrepareRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_OFFSET, _OFFSET = 'offset', 'Data offset value'
    P_SCALE, _SCALE = 'scale', 'Data scale value'
    P_DATA_MIN, _DATA_MIN = 'dataMin', 'Data minimum value'
    P_DATA_MAX, _DATA_MAX = 'dataMax', 'Data maximum value'
    P_DATA_TYPE, _DATA_TYPE = 'dataType', 'Data Type'
    P_NO_DATA_VALUE, _NO_DATA_VALUE = 'noDataValue', 'No data value'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def displayName(self) -> str:
        return 'Scale/truncate/convert raster layer'

    def shortDescription(self) -> str:
        return 'Allows to scale, truncate and convert raster data.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Raster layer to be processed.'),
            (self._OFFSET, 'A data offset value applied to each band.'),
            (self._SCALE, 'A data scale value applied to each band.'),
            (self._DATA_MIN, 'A data minimum value for truncating the data.'),
            (self._DATA_MAX, 'A data maximum value for truncating the data.'),
            (self._DATA_TYPE, 'Output data type.'),
            (self._NO_DATA_VALUE, 'Specify to recode output no data values.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.RasterConversion.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterFloat(self.P_OFFSET, self._OFFSET, None, True)
        self.addParameterFloat(self.P_SCALE, self._SCALE, None, True)
        self.addParameterFloat(self.P_DATA_MIN, self._DATA_MIN, None, True)
        self.addParameterFloat(self.P_DATA_MAX, self._DATA_MAX, None, True)
        self.addParameterFloat(self.P_NO_DATA_VALUE, self._NO_DATA_VALUE, None, True)
        self.addParameterDataType(self.P_DATA_TYPE, self._DATA_TYPE, None, True)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        offset = self.parameterAsFloat(parameters, self.P_OFFSET, context)
        scale = self.parameterAsFloat(parameters, self.P_SCALE, context)
        dataMin = self.parameterAsFloat(parameters, self.P_DATA_MIN, context)
        dataMax = self.parameterAsFloat(parameters, self.P_DATA_MAX, context)
        noDataValue = self.parameterAsFloat(parameters, self.P_NO_DATA_VALUE, context)
        dataType = self.parameterAsQgsDataType(
            parameters, self.P_DATA_TYPE, context, default=raster.dataProvider().dataType(1)
        )
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)
            writer = Driver(filename, feedback=feedback).createLike(reader, dataType, reader.bandCount())
            for bandNo in reader.bandNumbers():
                feedback.setProgress(bandNo / reader.bandCount() * 100)
                array = reader.array(bandList=[bandNo])
                maskArray = reader.maskArray(array, [bandNo])
                array = np.array(array, np.float64)

                if offset is not None:
                    array += offset
                if scale is not None:
                    array *= scale
                if dataMin is not None:
                    array[array < dataMin] = dataMin
                if dataMax is not None:
                    array[array > dataMax] = dataMax
                if noDataValue is not None:
                    array[np.logical_not(maskArray)] = noDataValue
                    writer.setNoDataValue(noDataValue, bandNo)
                else:
                    writer.setNoDataValue(reader.noDataValue(bandNo), bandNo)

                writer.writeArray(array, bandList=[bandNo])
                writer.setMetadata(reader.metadata(bandNo), bandNo)
                writer.setWavelength(reader.wavelength(bandNo), bandNo)
                writer.setFwhm(reader.fwhm(bandNo), bandNo)
                writer.setBandName(reader.bandName(bandNo), bandNo)
                writer.setBandColor(reader.bandColor(bandNo), bandNo)
                writer.setBadBandMultiplier(reader.badBandMultiplier(bandNo), bandNo)
            writer.setMetadata(reader.metadata())
            writer.close()
            del writer

            # create default style
            raster2 = QgsRasterLayer(filename)
            raster2.setRenderer(raster.renderer().clone())
            raster2.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
