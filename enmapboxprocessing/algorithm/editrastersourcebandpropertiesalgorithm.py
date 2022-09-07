from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)
from typeguard import typechecked


@typechecked
class EditRasterSourceBandPropertiesAlgorithm(EnMAPProcessingAlgorithm):
    P_SOURCE, _SOURCE = 'source', 'GDAL raster source'
    P_NAMES, _NAMES = 'names', 'Band names'
    P_WAVELENGTHS, _WAVELENGTHS = 'wavelengths', 'Center wavelength values'
    P_FWHMS, _FWHMS = 'fwhms', 'Full width at half maximum (FWHM) values'
    P_BAD_BAND_MULTIPLIERS, _BAD_BAND_MULTIPLIERS = 'badBandMultipliers', 'Bad band multipliers'
    P_START_TIMES, _START_TIMES = 'startTimes', 'Start times'
    P_END_TIMES, _END_TIMES = 'endTimes', 'End times'
    P_OFFSETS, _OFFSETS = 'offsets', 'Offsets'
    P_SCALES, _SCALES = 'scales', 'Scales'
    P_NO_DATA_VALUES, _NO_DATA_VALUES = 'noDataValues', 'No data values'

    def displayName(self):
        return 'Edit raster source band properties'

    def shortDescription(self):
        return 'Set band properties for the given GDAL raster source. ' \
               'Be sure to close the raster in QGIS beforehand.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._SOURCE, 'GDAL raster source.'),
            (self._NAMES, 'List of band name strings (e.g".'),
            (self._WAVELENGTHS, 'List of band center wavelength values in nanometers. '
                                'Use nan value to unset property.'),
            (self._FWHMS, 'List of band FWHM values in nanometers. '
                          'Use nan value to unset property.'),
            (self._BAD_BAND_MULTIPLIERS, 'List of bad band multiplier values (BBL).'),
            (self._START_TIMES, 'List of band start time timestamps strings. Format is: 2009-08-20T09:44:50. '
                                'Use empty string to unset property'),
            (self._END_TIMES, 'List of band end time timestamps strings. Format is: 2009-08-20T09:44:50. '
                              'Use empty string to unset property'),
            (self._OFFSETS, 'List of band data offset values.'),
            (self._SCALES, 'List of band data scale/gain values.'),
            (self._NO_DATA_VALUES, 'List of band no data values. '
                                   'Use None to unset property.')
        ]

    def group(self):
        return Group.Test.value + Group.RasterMiscellaneous.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_SOURCE, self._SOURCE)
        self.addParameterString(self.P_NAMES, self._NAMES, optional=True)
        self.addParameterString(self.P_WAVELENGTHS, self._WAVELENGTHS, optional=True)
        self.addParameterString(self.P_FWHMS, self._FWHMS, optional=True)
        self.addParameterString(self.P_BAD_BAND_MULTIPLIERS, self._BAD_BAND_MULTIPLIERS, optional=True)
        self.addParameterString(self.P_START_TIMES, self._START_TIMES, optional=True)
        self.addParameterString(self.P_END_TIMES, self._END_TIMES, optional=True)
        self.addParameterString(self.P_OFFSETS, self._OFFSETS, optional=True)
        self.addParameterString(self.P_SCALES, self._SCALES, optional=True)
        self.addParameterString(self.P_NO_DATA_VALUES, self._NO_DATA_VALUES, optional=True)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        source = self.parameterAsFile(parameters, self.P_SOURCE, context)
        names = self.parameterAsStringValues(parameters, self.P_NAMES, context)
        wavelengths = self.parameterAsFloatValues(parameters, self.P_WAVELENGTHS, context)
        fwhms = self.parameterAsFloatValues(parameters, self.P_FWHMS, context)
        badBandMultipliers = self.parameterAsFloatValues(parameters, self.P_BAD_BAND_MULTIPLIERS, context)
        startTimes = self.parameterAsStringValues(parameters, self.P_START_TIMES, context)
        endTimes = self.parameterAsStringValues(parameters, self.P_END_TIMES, context)
        offsets = self.parameterAsFloatValues(parameters, self.P_OFFSETS, context)
        scales = self.parameterAsFloatValues(parameters, self.P_SCALES, context)
        noDataValues = self.parameterAsFloatValues(parameters, self.P_NO_DATA_VALUES, context, True)

        ds = gdal.Open(source)
        assert ds is not None

        # check number of values values
        for name, values in zip(
                [self._NAMES, self._WAVELENGTHS, self._FWHMS, self._BAD_BAND_MULTIPLIERS, self._START_TIMES,
                 self._END_TIMES, self._OFFSETS, self._SCALES, self._NO_DATA_VALUES],
                [names, wavelengths, fwhms, badBandMultipliers, startTimes, endTimes, offsets, scales, noDataValues]
        ):
            if values is not None:
                if len(values) != ds.RasterCount:
                    raise QgsProcessingException(
                        f'list length ({len(values)}) not matching number of bands ({ds.RasterCount()}): {name}'
                    )

        # set properties
        writer = RasterWriter(ds)
        if names is not None:
            for bandNo, name in enumerate(names, 1):
                writer.setBandName(name, bandNo)
        if wavelengths is not None:
            for bandNo, wavelength in enumerate(wavelengths, 1):
                writer.setWavelength(wavelength, bandNo)
        if fwhms is not None:
            for bandNo, fwhm in enumerate(fwhms, 1):
                writer.setFwhm(fwhm, bandNo)
        if badBandMultipliers is not None:
            for bandNo, badBandMultiplier in enumerate(badBandMultipliers, 1):
                writer.setBadBandMultiplier(badBandMultiplier, bandNo)
        if startTimes is not None:
            for bandNo, startTime in enumerate(startTimes, 1):
                startTime = Utils.parseDateTime(startTime)
                writer.setStartTime(startTime, bandNo)
        if endTimes is not None:
            for bandNo, endTime in enumerate(endTimes, 1):
                if endTime == '':
                    continue
                endTime = Utils.parseDateTime(endTime)
                writer.setEndTime(endTime, bandNo)
        if noDataValues is not None:
            for bandNo, noDataValue in enumerate(noDataValues, 1):
                if noDataValue is None:
                    writer.deleteNoDataValue(bandNo)
                else:
                    writer.setNoDataValue(noDataValue, bandNo)
        if offsets is not None:
            for bandNo, offset in enumerate(offsets, 1):
                writer.setOffset(offset, bandNo)
        if scales is not None:
            for bandNo, scale in enumerate(scales, 1):
                writer.setScale(scale, bandNo)

        del writer
        ds.FlushCache()
        del ds
        return {}
