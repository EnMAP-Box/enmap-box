from collections import OrderedDict
from os.path import exists
from typing import Dict, Any, List, Tuple, Union

from osgeo import gdal

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsRasterLayer)


@typechecked
class WriteStacHeaderAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'

    def displayName(self):
        return 'Write Stac header'

    def shortDescription(self):
        return 'Write STAC *.stac.json metadata file. '

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Raster layer for which to write the STAC file.'),
        ]

    def group(self):
        return Group.RasterConversion.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        self.writeStacHeader(raster)
        return {}

    @staticmethod
    def writeStacHeader(raster: Union[QgsRasterLayer, gdal.Dataset]):

        if isinstance(raster, QgsRasterLayer):
            filename = raster.source()
        elif isinstance(raster, gdal.Dataset):
            filename = raster.GetDescription()
            raster.FlushCache()
        else:
            raise ValueError()

        if not exists(filename):
            raise QgsProcessingException(f'Raster layer source is not a valid filename: {filename}')

        reader = RasterReader(raster)
        metadata = OrderedDict()
        metadata['stac_extensions'] = [
            'https://stac-extensions.github.io/eo/v1.0.0/schema.json',
            'https://stac-extensions.github.io/timestamps/v1.1.0/schema.json'
        ]
        metadata['properties'] = OrderedDict()
        metadata['properties']['eo:bands'] = list()
        for bandNo in reader.bandNumbers():
            bandMetadata = OrderedDict()
            bandMetadata['name'] = reader.bandName(bandNo)
            bandMetadata['color'] = reader.bandColor(bandNo)
            bandMetadata['center_wavelength'] = reader.wavelength(bandNo, reader.Micrometers)
            bandMetadata['full_width_half_max'] = reader.fwhm(bandNo, reader.Micrometers)
            if reader.endTime(bandNo) is None:
                if reader.centerTime(bandNo) is not None:
                    bandMetadata['datetime'] = reader.centerTime(bandNo)
            else:
                bandMetadata['start_datetime'] = reader.startTime(bandNo)
                bandMetadata['end_datetime'] = reader.endTime(bandNo)
            bandMetadata['enmapbox:bad_band_multiplier'] = reader.badBandMultiplier(bandNo)

            # we can skip the bad_band_multiplier for good bands, because that is the default
            if bandMetadata['enmapbox:bad_band_multiplier'] == 1:
                bandMetadata.pop('enmapbox:bad_band_multiplier')

            # skip None Values
            bandMetadata = {k: v for k, v in bandMetadata.items() if v is not None}

            metadata['properties']['eo:bands'].append(bandMetadata)
        Utils().jsonDump(metadata, filename + '.stac.json', timeFormat='yyyy-MM-ddTHH:mm:ss')
