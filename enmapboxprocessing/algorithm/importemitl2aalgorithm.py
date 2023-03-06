from os.path import basename
from typing import Dict, Any, List, Tuple

import netCDF4
import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.utils import Utils
from qgis._core import QgsRectangle, QgsCoordinateReferenceSystem
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)


@typechecked
class ImportEmitL2AAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'NetCDF file'
    P_SKIP_BAD_BANDS, _SKIP_BAD_BANDS = 'skipBadBands', 'Skip bad bands'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputEmitL2ARaster', 'Output raster layer'

    def displayName(self):
        return 'Import EMIT L2A product'

    def shortDescription(self):
        url = 'https://earth.jpl.nasa.gov/emit/'
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength and FWHM information is set and data is scaled into the 0 to 1 range.\n' \
               f'EMIT website: <a href="{url}">{url}</a>'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The EMIT L2A RFL NetCDF product file.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the NetCDF file directly from your system file browser onto '
                         'the EnMAP-Box map view area.'),
            (self._SKIP_BAD_BANDS, 'Whether to exclude bad bands.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FILE, self._FILE, extension='nc')
        self.addParameterBoolean(self.P_SKIP_BAD_BANDS, self._SKIP_BAD_BANDS, True)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def isValidFile(self, file: str) -> bool:
        return basename(file).startswith('EMIT_L2A_RFL') & \
               basename(file).endswith('.nc')

    def defaultParameters(self, ncFilename: str):
        return {
            self.P_FILE: ncFilename,
            self.P_OUTPUT_RASTER: ncFilename.replace('.nc', '.tif'),
        }

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:

        # Credits: code was adopted from a script provided by Philip G. Brodrick (philip.brodrick@jpl.nasa.govCode)
        # https://github.com/emit-sds/emit-utils/blob/develop/emit_utils/reformat.py

        ncFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        skipBadBands = self.parameterAsBool(parameters, self.P_SKIP_BAD_BANDS, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)
        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'EMIT_L2A_RFL_001_20220815T042838_2222703_003.nc'
            if not self.isValidFile(ncFilename):
                message = f'not a valid EMIT L2A RFL product: {ncFilename}'
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            nc_ds = netCDF4.Dataset(ncFilename, 'r', format='NETCDF4')
            glt = np.zeros(list(nc_ds.groups['location']['glt_x'].shape) + [2], dtype=np.int32)
            glt[..., 0] = np.array(nc_ds.groups['location']['glt_x'])
            glt[..., 1] = np.array(nc_ds.groups['location']['glt_y'])

            metadata = dict()
            for key, value in nc_ds.__dict__.items():
                metadata[key] = value
            for key, value in nc_ds['sensor_band_parameters'].variables.items():
                metadata[key] = np.array(value).tolist()
            metadata.pop('geotransform')

            def single_image_ortho(array, glt, noDataValue):
                array2 = np.full((glt.shape[0], glt.shape[1], array.shape[-1]), noDataValue, np.float32)
                valid = np.all(glt != 0, axis=-1)
                glt[valid] -= 1  # account for 1-based indexing
                array2[valid, :] = array[glt[valid, 1], glt[valid, 0], :]
                return array2

            noDataValue = -9999
            array = single_image_ortho(np.array(nc_ds['reflectance']), glt, noDataValue)
            array = np.transpose(array, (2, 0, 1))
            xmin = float(metadata['easternmost_longitude'])
            xmax = float(metadata['westernmost_longitude'])
            ymin, ymax = sorted([float(metadata['northernmost_latitude']), float(metadata['southernmost_latitude'])])
            extent = QgsRectangle(xmin, ymin, xmax, ymax)
            crs = QgsCoordinateReferenceSystem.fromWkt(metadata['spatial_ref'])

            if 'good_wavelengths' not in metadata:
                metadata['good_wavelengths'] = [1] * len(array)
            if skipBadBands:
                goodBands = np.equal(metadata['good_wavelengths'], 1)
                array = array[goodBands]
                metadata['wavelengths'] = [v for v, goodBand in zip(metadata['wavelengths'], goodBands) if goodBand]
                metadata['fwhm'] = [v for v, goodBand in zip(metadata['fwhm'], goodBands) if goodBand]
                metadata['good_wavelengths'] = [1] * len(array)

            writer = Driver(filename).createFromArray(array, extent, crs)
            writer.setNoDataValue(noDataValue)
            writer.setMetadataDomain(metadata)
            writer.setStartTime(Utils.parseDateTime(metadata['time_coverage_start']))
            writer.setEndTime(Utils.parseDateTime(metadata['time_coverage_end']))
            for bandNo in writer.bandNumbers():
                wavelength = metadata['wavelengths'][bandNo - 1]
                writer.setWavelength(wavelength, bandNo)
                writer.setFwhm(metadata['fwhm'][bandNo - 1], bandNo)
                writer.setBadBandMultiplier(metadata['good_wavelengths'][bandNo - 1], bandNo)
                writer.setBandName(f'band {bandNo} ({wavelength} Nanometers)', bandNo)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
