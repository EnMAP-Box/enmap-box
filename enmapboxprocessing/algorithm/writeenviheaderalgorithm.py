from os.path import exists
from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapbox.qgispluginsupport.qps.speclib.io.envi import findENVIHeader, readENVIHeader
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)
from typeguard import typechecked


@typechecked
class WriteEnviHeaderAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'

    def displayName(self):
        return 'Write ENVI header'

    def shortDescription(self):
        return 'Write/update the ENVI *.hdr header file to enable full compatibility to the ENVI software. ' \
               'The header file stores wavelength, FWHM and bad band multiplier (BBL) information.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Source GeoTiff /ENVI raster layer.'),
        ]

    def group(self):
        return Group.Test.value + Group.RasterConversion.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)

        if not exists(raster.source()):
            raise QgsProcessingException(f'Raster layer source is not a valid filename: {raster.source()}')
        ds: gdal.Dataset = gdal.Open(raster.source())
        driver: gdal.Driver = ds.GetDriver()
        if driver.ShortName not in ['GTiff', 'ENVI']:
            raise QgsProcessingException('Raster layer is not a GeoTiff or ENVI file')

        reader = RasterReader(ds)
        if driver.ShortName == 'GTiff':

            text = 'ENVI\n' \
                   'file type = TIFF\n' \
                   f'samples = {reader.width()}\n' \
                   f'lines = {reader.height()}\n' \
                   f'bands = {reader.bandCount()}\n'

            if reader.isSpectralRasterLayer(quickCheck=True):
                wavelength = [str(reader.wavelength(bandNo)) for bandNo in range(1, reader.bandCount() + 1)]
                fwhm = [str(reader.fwhm(bandNo)) for bandNo in range(1, reader.bandCount() + 1)]
                bbl = [str(reader.badBandMultiplier(bandNo)) for bandNo in range(1, reader.bandCount() + 1)]
                text += 'wavelength units = Nanometer\n' \
                        'wavelength = {' + ', '.join(wavelength) + '}\n'
                if fwhm[0] != 'None':
                    text += 'fwhm = {' + ', '.join(fwhm) + '}\n'
                if bbl[0] != 'None':
                    text += 'bbl = {' + ', '.join(bbl) + '}\n'

            if ds.GetRasterBand(1).GetNoDataValue() is not None:
                text += f'data ignore value = {ds.GetRasterBand(1).GetNoDataValue()}\n'
            filenameHeader = raster.source() + '.hdr'
        else:
            filenameHeader = findENVIHeader(raster.source())[0]
            metadata = readENVIHeader(raster.source(), False)
            metadata['band names'] = [reader.bandName(bandNo) for bandNo in range(1, reader.bandCount() + 1)]
            metadata['bbl'] = [str(reader.badBandMultiplier(bandNo)) for bandNo in range(1, reader.bandCount() + 1)]
            if reader.isSpectralRasterLayer(quickCheck=False):
                metadata['wavelength units'] = 'Nanometers'
                metadata['wavelength'] = [str(reader.wavelength(bandNo)) for bandNo in range(1, reader.bandCount() + 1)]
                if reader.fwhm(1) is not None:
                    metadata['fwhm'] = [str(reader.fwhm(bandNo)) for bandNo in range(1, reader.bandCount() + 1)]

            if ds.GetRasterBand(1).GetNoDataValue() is not None:
                metadata['data ignore value'] = str(ds.GetRasterBand(1).GetNoDataValue())

            lines = ['ENVI']
            for key, value in metadata.items():
                if isinstance(value, list):
                    value = '{' + ', '.join(value) + '}'
                lines.append(f'{key} = {value}')
            text = '\n'.join(lines)

        with open(filenameHeader, 'w') as file:
            file.write(text)

        return {}
