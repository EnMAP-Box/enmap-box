import numpy as np
from osgeo import gdal

from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.processing.enmapalgorithm import *


class SubsetRasterBands(EnMAPAlgorithm):
    def displayName(self):
        return 'Subset Raster Bands'

    def description(self):
        return 'Subset raster bands by band numbers, band number ranges and wavelength ranges.'

    def group(self):
        return Group.ResamplingAndSubsetting.value

    P_RASTER = 'raster'
    P_NUMBERS = 'numbers'
    P_EXCLUDE_BAB_BANDS = 'excludeBadBands'
    P_OUTPUT_RASTER = 'outraster'

    def defineCharacteristics(self):

        self.addParameter(
            EnMAPProcessingParameterRasterLayer(
                name=self.P_RASTER, description='Raster')
        )

        self.addParameter(
            EnMAPProcessingParameterString(
                name=self.P_NUMBERS, description='Band subset', optional=True,
                help=Help(
                    'List of bands, band ranges or waveband ranges to subset. E.g. 1, 2, 4 6, 900. 1200. will select the first band, the second band, bands between 4 to 6, and wavebands between 900 to 1200 nanometers.')
            )
        )

        self.addParameter(
            EnMAPProcessingParameterBoolean(
                name=self.P_EXCLUDE_BAB_BANDS, description='Exclude Bad Bands',
                help=Help('Wether to exclude bad bands.')
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTPUT_RASTER, description='Output Raster'
            )
        )

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        qgsRasterLayer: QgsRasterLayer = self.parameter(parameters, self.P_RASTER, context)
        raster = GdalRaster.open(qgsRasterLayer.source())

        # parse band subset
        text = self.parameter(parameters, self.P_NUMBERS, context)
        excludeBadBands = self.parameter(parameters, self.P_EXCLUDE_BAB_BANDS, context)
        numbers = self.parseNumbers(text=text, gdalRaster=raster, excludeBadBands=excludeBadBands)

        # write subset
        filename = self.parameter(parameters, self.P_OUTPUT_RASTER, context)
        outraster = raster.translate(filename=filename, bandList=numbers)

        # write metadata
        for outband, number in zip(outraster.bands, numbers):
            band = raster.band(number=number)
            outband.setWavelength(band.wavelength)
            outband.setFwhm(band.fwhm)
            outband.setIsBadBand(band.isBadBand)
            outband.setMetadataDict(band.metadataDict)

        return {self.P_OUTPUT_RASTER: filename}

    @classmethod
    def parseNumbers(cls, text: str, gdalRaster: GdalRaster, excludeBadBands: bool) -> List[int]:
        """Return list of band numbers."""
        assert isinstance(text, str)
        assert isinstance(gdalRaster, GdalRaster)
        assert isinstance(excludeBadBands, bool)
        if text == '':
            numbers = list(range(1, gdalRaster.shape.z + 1))
        else:
            tmp = [v.strip() for v in text.split(',')]
            tmp = [v.split(' ') for v in tmp]
            numbers = list()
            for v in tmp:
                if len(v) == 1:
                    numbers.append(cls.findBandNumber(text=v[0], raster=gdalRaster))
                elif len(v) == 2:
                    number1 = cls.findBandNumber(text=v[0], raster=gdalRaster)
                    number2 = cls.findBandNumber(text=v[1], raster=gdalRaster)
                    numbers.extend(list(range(number1, number2 + 1)))

        for number in numbers:
            assert 1 <= number <= gdalRaster.shape.z, f'number out of range: {number}'

        if excludeBadBands:
            numbers = [number for number in numbers if not gdalRaster.band(number).isBadBand]

        if len(numbers) == 0:
            raise ValueError('empty band list')

        return numbers

    @staticmethod
    def findBandNumber(text: str, raster: GdalRaster) -> int:
        if '.' in text:
            targetWavelength = float(text)
            wavelengths = list()
            for band in raster.bands:
                wavelength = band.wavelength
                if wavelength is None:
                    raise ValueError('raster band center wavelength is undefined')
                wavelengths.append(wavelength)

            number = np.argmin(np.abs(np.subtract(wavelengths, targetWavelength))) + 1
        else:
            number = int(text)

        return number
