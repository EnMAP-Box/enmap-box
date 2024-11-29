from os.path import basename
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from osgeo import gdal

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.algorithm.importprismal1algorithm import utilsReadAsArray, utilsDeleteCopy
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsRectangle, \
    QgsCoordinateReferenceSystem, QgsRasterLayer, QgsMapLayer


@typechecked
class ImportPrismaL2DAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'File'
    P_SPECTRAL_REGION, _SPECTRAL_REGION = 'spectralRegion', 'Spectral region'
    O_SPECTRAL_REGION = ['VNIR/SWIR combined', 'VNIR only', 'SWIR only', ]
    VnirSwirRegion, VnirRegion, SwirRegion, = range(3)
    P_BAD_BAND_THRESHOLD, _BAD_BAND_THRESHOLD = 'badBandThreshold', 'Bad band threshold'
    P_BAD_PIXEL_TYPE, _BAD_PIXEL_TYPE = 'badPixelType', 'Select bad pixel'
    O_BAD_PIXEL_TYPE = ['Invalid pixel from L1 product', 'Negative value after atmospheric correction',
                        'Saturated value after atmospheric correction']
    InvalidL1Pixel, NegativeAtmosphericCorrectionPixel, SaturatedAtmosphericCorrectionPixel = range(3)
    P_OUTPUT_SPECTRAL_CUBE, _OUTPUT_SPECTRAL_CUBE = 'outputPrismaL2D_spectralCube', 'Output VNIR/SWIR Cube raster layer'
    P_OUTPUT_PAN_CUBE, _OUTPUT_PAN_CUBE = 'outputPrismaL2D_panCube', 'Output PAN raster layer'

    P_OUTPUT_SPECTRAL_GEOLOCATION, _OUTPUT_SPECTRAL_GEOLOCATION = 'outputPrismaL2D_spectralGeolocationFields', \
                                                                  'Output VNIR/SWIR Geolocation Fields raster layer'
    P_OUTPUT_SPECTRAL_GEOMETRIC, _OUTPUT_SPECTRAL_GEOMETRIC = 'outputPrismaL2D_spectralGeometricFields', \
                                                              'Output VNIR/SWIR Geometric Fields raster layer'
    P_OUTPUT_SPECTRAL_ERROR, _OUTPUT_SPECTRAL_ERROR = 'outputPrismaL2D_spectralErrorMatrix', \
                                                      'Output VNIR/SWIR Error Matrix raster layer'
    P_OUTPUT_PAN_GEOLOCATION, _OUTPUT_PAN_GEOLOCATION = 'outputPrismaL2D_panGeolocationFields', \
                                                        'Output PAN Geolocation Fields raster layer'
    P_OUTPUT_PAN_ERROR, _OUTPUT_PAN_ERROR = 'outputPrismaL2D_panErrorMatrix', \
                                            'Output PAN Error Matrix raster layer'

    def displayName(self):
        return 'Import PRISMA L2D product'

    def shortDescription(self):
        link = EnMAPProcessingAlgorithm.htmlLink(
            'http://prisma.asi.it/missionselect/docs.php', 'PRISMA Documentation Area'
        )
        return 'Import PRISMA L2D product from HE5 file to QGIS/GDAL conform GTiff/VRT file format ' \
               'with proper coordinate reference system.' \
               'Note that for the spectral cube and error matrix, the interleave is transposed ' \
               'and stored as GTiff to enable proper visualization in QGIS.' \
               'All other sub-datasets are stored as light-weight VRT files.\n' \
               f'For further details visit the {link}.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The HE5 product file.\n'
                         'The main data contained in the PRS_L2d_HCO Swath is the surface spectral reflectance '
                         'Coregistersed Hyperspectral Cube (in instrument geometric reference).\n'
                         'The main data contained in the PRS_L2d_PCO Swath is the surface panchromatic reflectance '
                         'image (in instrument geometric reference).\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the HE5 file directly from your system file browser '
                         'a) onto the EnMAP-Box map view area, or b) onto the Sensor Product Import panel.'),
            (self._SPECTRAL_REGION, 'Spectral region to be imported.'),
            (self._BAD_BAND_THRESHOLD, 'If the proportion of erroneous pixels in the VNIR/SWIR Pixel Error Matrix,'
                                       'exceeds the bad band threshold (a value between 0 and 1), '
                                       'the band is marked as a bad band.\n'
                                       'If specified, Output VNIR/SWIR Error Matrix raster layer needs to be '
                                       'specified as well.'),
            (self._BAD_PIXEL_TYPE, 'Pixels concidered to be erroneous.'),
            (self._OUTPUT_SPECTRAL_CUBE, 'VNIR/SWIR Cube GTiff raster file destination. '
                                         'The surface spectral reflectance Coregistersed Hyperspectral Cube '
                                         '(in instrument geometric reference).'),
            (self._OUTPUT_PAN_CUBE, 'PAN VRT raster file destination. '
                                    'The surface panchromatic reflectance image (in instrument geometric reference).'),
            (self._OUTPUT_SPECTRAL_GEOLOCATION, 'VNIR/SWIR Geolocation Fields VRT raster file destination. '
                                                'Includes Latitude and Longitude bands.'),
            (self._OUTPUT_SPECTRAL_GEOMETRIC, 'VNIR/SWIR Geometric Fields VRT raster file destination. '
                                              'Includes Observing Angle, Relative Azimuth Angle and '
                                              'Solar Zenith Angle bands.'),
            (self._OUTPUT_SPECTRAL_ERROR, 'VNIR/SWIR Pixel Error Matrix GTiff raster file destination.'),
            (self._OUTPUT_PAN_GEOLOCATION, 'PAN Geolocation Fields VRT raster file destination. '
                                           'Includes Latitude and Longitude bands.'),
            (self._OUTPUT_PAN_ERROR, 'PAN Pixel Error Matrix VRT raster file destination.'),
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FILE, self._FILE, extension='he5')
        self.addParameterEnum(self.P_SPECTRAL_REGION, self._SPECTRAL_REGION, self.O_SPECTRAL_REGION, False, 0)
        self.addParameterFloat(self.P_BAD_BAND_THRESHOLD, self._BAD_BAND_THRESHOLD, None, True, 0, 1, False)
        self.addParameterEnum(self.P_BAD_PIXEL_TYPE, self._BAD_PIXEL_TYPE, self.O_BAD_PIXEL_TYPE, True, [0], True)
        self.addParameterRasterDestination(self.P_OUTPUT_SPECTRAL_CUBE, self._OUTPUT_SPECTRAL_CUBE)
        self.addParameterVrtDestination(
            self.P_OUTPUT_PAN_CUBE, self._OUTPUT_PAN_CUBE, None, True, False, True
        )
        self.addParameterVrtDestination(
            self.P_OUTPUT_SPECTRAL_GEOLOCATION, self._OUTPUT_SPECTRAL_GEOLOCATION, None, True, False, True
        )
        self.addParameterVrtDestination(
            self.P_OUTPUT_SPECTRAL_GEOMETRIC, self._OUTPUT_SPECTRAL_GEOMETRIC, None, True, False, True
        )
        self.addParameterRasterDestination(self.P_OUTPUT_SPECTRAL_ERROR, self._OUTPUT_SPECTRAL_ERROR, None, True, False)
        self.addParameterVrtDestination(
            self.P_OUTPUT_PAN_GEOLOCATION, self._OUTPUT_PAN_GEOLOCATION, None, True, False, True
        )
        self.addParameterVrtDestination(self.P_OUTPUT_PAN_ERROR, self._OUTPUT_PAN_ERROR, None, True, False, True)

    def defaultParameters(self, file: str):
        return {
            self.P_FILE: file,
            self.P_OUTPUT_SPECTRAL_CUBE: file.replace('.he5', '_SPECTRAL.tif'),
            self.P_OUTPUT_PAN_CUBE: file.replace('.he5', '_PAN.vrt'),
            self.P_OUTPUT_SPECTRAL_GEOLOCATION: file.replace('.he5', '_SPECTRAL_GEOLOCATION.vrt'),
            self.P_OUTPUT_SPECTRAL_GEOMETRIC: file.replace('.he5', '_SPECTRAL_GEOMETRIC.vrt'),
            self.P_OUTPUT_SPECTRAL_ERROR: file.replace('.he5', '_SPECTRAL_ERROR.tif'),
            self.P_OUTPUT_PAN_GEOLOCATION: file.replace('.he5', '_PAN_GEOLOCATION.vrt'),
            self.P_OUTPUT_PAN_ERROR: file.replace('.he5', '_PAN_ERROR.vrt')
        }

    def isValidFile(self, file: str) -> bool:
        return basename(file).startswith('PRS_L2D') & \
               basename(file).endswith('.he5')

    def openDataset(self, he5Filename: str, key: str) -> gdal.Dataset:
        key = key.replace(' ', '_')
        source = f'HDF5:"""{he5Filename}"""://{key}'
        ds: gdal.Dataset = gdal.Open(source)
        if ds is None:
            raise QgsProcessingException(f'unable to open PRISMA subdataset: {he5Filename}')
        return ds

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        he5Filename = self.parameterAsFile(parameters, self.P_FILE, context)

        spectralRegion = self.parameterAsEnum(parameters, self.P_SPECTRAL_REGION, context)
        badBandThreshold = self.parameterAsFloat(parameters, self.P_BAD_BAND_THRESHOLD, context)
        badPixelTypes = self.parameterAsEnums(parameters, self.P_BAD_PIXEL_TYPE, context)
        filenameSpectralCube = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_SPECTRAL_CUBE, context)
        filenameSpectralGeolocation = self.parameterAsOutputLayer(
            parameters, self.P_OUTPUT_SPECTRAL_GEOLOCATION, context
        )
        filenameSpectralGeometric = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_SPECTRAL_GEOMETRIC, context)
        filenameSpectralError = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_SPECTRAL_ERROR, context)

        filenamePanCube = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PAN_CUBE, context)
        filenamePanGeolocation = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PAN_GEOLOCATION, context)
        filenamePanError = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PAN_ERROR, context)

        if badBandThreshold is not None:
            if filenameSpectralError is None:
                raise QgsProcessingException(f'Wrong or missing parameter value: {self._OUTPUT_SPECTRAL_ERROR}')

        with open(filenameSpectralCube + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'PRS_L2D_STD_20201107101404_20201107101408_0001.he5'
            if not self.isValidFile(he5Filename):
                message = f'not a valid PRISMA L2D product: {he5Filename}'
                raise QgsProcessingException(message)

            badBandMultipliers = self.writeSpectralErrorMatrix(
                filenameSpectralError, he5Filename, spectralRegion, badBandThreshold, badPixelTypes, feedback
            )
            self.writeSpectralCube(filenameSpectralCube, he5Filename, spectralRegion, badBandMultipliers, feedback)
            self.writeSpectralGeolocationFields(filenameSpectralGeolocation, he5Filename)
            self.writeSpectralGeometricFields(filenameSpectralGeometric, he5Filename)

            self.writePanCube(filenamePanCube, he5Filename)
            self.writePanGeolocationFields(filenamePanGeolocation, he5Filename)
            self.writePanErrorMatrix(filenamePanError, he5Filename)

            utilsDeleteCopy(he5Filename)

            result = {
                self.P_OUTPUT_SPECTRAL_CUBE: filenameSpectralCube,
                self.P_OUTPUT_SPECTRAL_GEOLOCATION: filenameSpectralGeolocation,
                self.P_OUTPUT_SPECTRAL_GEOMETRIC: filenameSpectralGeometric,
                self.P_OUTPUT_SPECTRAL_ERROR: filenameSpectralError,
                self.P_OUTPUT_PAN_CUBE: filenamePanCube,
                self.P_OUTPUT_PAN_GEOLOCATION: filenamePanGeolocation,
                self.P_OUTPUT_PAN_ERROR: filenamePanError,
            }

            self.toc(feedback, result)

        return result

    def writeSpectralCube(
            self, filenameSpectralCube, he5Filename, spectralRegion, badBandMultipliers: Optional[List[int]],
            feedback
    ):
        parseFloatList = lambda text: [float(item) for item in text.split()]
        array = list()
        metadata = dict()
        wavelength = list()
        fwhm = list()
        # - VNIR
        if spectralRegion in [self.VnirSwirRegion, self.VnirRegion]:
            key = 'HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/VNIR_Cube'
            dsVnir = self.openDataset(he5Filename, key)
            arrayVnir = utilsReadAsArray(dsVnir, he5Filename, key, feedback)

            metadataVnir = dsVnir.GetMetadata('')
            selectedVnir = [v != 0 for v in parseFloatList(metadataVnir['List_Cw_Vnir'])]
            arrayVnir = np.transpose(arrayVnir, [1, 0, 2])[selectedVnir][::-1]
            wavelengthVnir = list(reversed(
                [float(v) for v, flag in zip(parseFloatList(metadataVnir['List_Cw_Vnir']), selectedVnir)
                 if flag]
            ))
            fwhmVnir = list(reversed(
                [float(v) for v, flag in zip(parseFloatList(metadataVnir['List_Fwhm_Vnir']), selectedVnir)
                 if flag]
            ))
            array.extend(arrayVnir)
            wavelength.extend(wavelengthVnir)
            fwhm.extend(fwhmVnir)
            metadata.update(metadataVnir)
        # - SWIR
        if spectralRegion in [self.VnirSwirRegion, self.SwirRegion]:
            key = 'HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/SWIR_Cube'
            dsSwir = self.openDataset(he5Filename, key)
            arraySwir = utilsReadAsArray(dsSwir, he5Filename, key, feedback)
            metadataSwir = dsSwir.GetMetadata('')
            selectedSwir = [v != 0 for v in parseFloatList(metadataSwir['List_Cw_Swir'])]
            arraySwir = np.transpose(arraySwir, [1, 0, 2])[selectedSwir][::-1]
            wavelengthSwir = list(reversed(
                [float(v) for v, flag in zip(parseFloatList(metadataSwir['List_Cw_Swir']), selectedSwir)
                 if flag]
            ))
            fwhmSwir = list(reversed(
                [float(v) for v, flag in zip(parseFloatList(metadataSwir['List_Fwhm_Swir']), selectedSwir)
                 if flag]
            ))
            array.extend(arraySwir)
            wavelength.extend(wavelengthSwir)
            fwhm.extend(fwhmSwir)
            metadata.update(metadataSwir)
        # - scale data and mask no data region
        mask = np.all(np.equal(array, 0), axis=0)
        array = np.clip(array, 1, None, dtype=np.float32)
        array /= 65535
        array[:, mask] = 0
        assert len(wavelength) == len(array)
        assert len(fwhm) == len(array)
        crs, extent, geoTransform = self.spatialInfo(metadata, 30)
        driver = Driver(filenameSpectralCube)
        writer = driver.createFromArray(array, extent, crs)
        writer.setNoDataValue(0)
        writer.setMetadataDomain(metadata)
        for bandNo in range(1, writer.bandCount() + 1):
            wl = wavelength[bandNo - 1]
            writer.setBandName(f'Band {bandNo} ({wl} Nanometers)', bandNo)
            writer.setWavelength(wl, bandNo)
            writer.setFwhm(fwhm[bandNo - 1], bandNo)
        if badBandMultipliers is not None:
            for bandNo, badBandMultiplier in enumerate(badBandMultipliers, 1):
                writer.setBadBandMultiplier(badBandMultiplier, bandNo)

        writer.close()
        del writer

        # setup default renderer
        layer = QgsRasterLayer(filenameSpectralCube)
        reader = RasterReader(layer)
        redBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['R'][0])
        greenBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['G'][0])
        blueBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['B'][0])
        redMin, redMax = reader.provider.cumulativeCut(redBandNo, 0.02, 0.98)
        greenMin, greenMax = reader.provider.cumulativeCut(greenBandNo, 0.02, 0.98)
        blueMin, blueMax = reader.provider.cumulativeCut(blueBandNo, 0.02, 0.98)
        renderer = Utils().multiBandColorRenderer(
            reader.provider, [redBandNo, greenBandNo, blueBandNo], [redMin, greenMin, blueMin],
            [redMax, greenMax, blueMax]
        )
        layer.setRenderer(renderer)
        layer.saveDefaultStyle(QgsMapLayer.StyleCategory.Rendering)

    def writeSpectralErrorMatrix(
            self, filenameSpectralError, he5Filename, spectralRegion, badPixelThreshold: Optional[float],
            badPixelTypes: List[int], feedback: QgsProcessingFeedback
    ) -> Optional[List[int]]:
        if filenameSpectralError is None:
            return None
        parseFloatList = lambda text: [float(item) for item in text.split()]
        array = list()
        metadata = dict()
        wavelength = list()
        # - VNIR
        if spectralRegion in [self.VnirSwirRegion, self.VnirRegion]:
            key = 'HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/VNIR_PIXEL_L2_ERR_MATRIX'
            dsVnir = self.openDataset(he5Filename, key)
            arrayVnir = utilsReadAsArray(dsVnir, he5Filename, key, feedback)
            metadataVnir = dsVnir.GetMetadata('')
            selectedVnir = [v != 0 for v in parseFloatList(metadataVnir['List_Cw_Vnir'])]
            arrayVnir = np.transpose(arrayVnir, [1, 0, 2])[selectedVnir][::-1]
            wavelengthVnir = list(reversed(
                [float(v) for v, flag in zip(parseFloatList(metadataVnir['List_Cw_Vnir']), selectedVnir)
                 if flag]
            ))
            array.extend(arrayVnir)
            wavelength.extend(wavelengthVnir)
            metadata.update(metadataVnir)
        # - SWIR
        if spectralRegion in [self.VnirSwirRegion, self.SwirRegion]:
            key = 'HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/SWIR_PIXEL_L2_ERR_MATRIX'
            dsSwir = self.openDataset(he5Filename, key)
            arraySwir = utilsReadAsArray(dsSwir, he5Filename, key, feedback)
            metadataSwir = dsSwir.GetMetadata('')
            selectedSwir = [v != 0 for v in parseFloatList(metadataSwir['List_Cw_Swir'])]
            arraySwir = np.transpose(arraySwir, [1, 0, 2])[selectedSwir][::-1]
            wavelengthSwir = list(reversed(
                [float(v) for v, flag in zip(parseFloatList(metadataSwir['List_Cw_Swir']), selectedSwir)
                 if flag]
            ))
            array.extend(arraySwir)
            wavelength.extend(wavelengthSwir)
            metadata.update(metadataSwir)
        # - mask no data region
        assert len(wavelength) == len(array)
        crs, extent, geoTransform = self.spatialInfo(metadata, 30)
        driver = Driver(filenameSpectralError, feedback=feedback)
        writer = driver.createFromArray(array, extent, crs)
        writer.setMetadataDomain(metadata)
        for bandNo in range(1, writer.bandCount() + 1):
            wl = wavelength[bandNo - 1]
            writer.setBandName(f'Pixel Error Band {bandNo} ({wl} Nanometers)', bandNo)
            writer.setWavelength(wl, bandNo)
        writer.close()

        # bad pixel thresholding
        if badPixelThreshold is None:
            badBandMultipliers = None
        else:
            badBandMultipliers = list()
            for bandNo, a in enumerate(array, 1):
                badPixelMask = np.full_like(a, False, bool)
                # Note that we just compare against individual bit flags.
                # That should be fine, because all flags are mutually exclusive.
                # We wouldn't expect values other than 0, 1, 2 and 4.'
                if self.InvalidL1Pixel in badPixelTypes:
                    np.logical_or(badPixelMask, a == 1, out=badPixelMask)
                if self.NegativeAtmosphericCorrectionPixel in badPixelTypes:
                    np.logical_or(badPixelMask, a == 2, out=badPixelMask)
                if self.SaturatedAtmosphericCorrectionPixel in badPixelTypes:
                    np.logical_or(badPixelMask, a == 4, out=badPixelMask)
                badPixelProportion = np.mean(badPixelMask)
                message = f'Band {bandNo} bad pixel proportion: {round(badPixelProportion, 4)}'
                if badPixelProportion < badPixelThreshold:
                    badBandMultiplier = 1
                else:
                    badBandMultiplier = 0
                    message += ' (marked as bad band)'
                badBandMultipliers.append(badBandMultiplier)
                feedback.pushInfo(message)

        return badBandMultipliers

    def writeSpectralGeolocationFields(self, filenameSpectralGeolocation, he5Filename):
        if filenameSpectralGeolocation is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L2D_HCO/Geolocation_Fields/Longitude')
        ds2 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L2D_HCO/Geolocation_Fields/Latitude')
        metadata = ds1.GetMetadata('')
        crs, extent, geoTransform = self.spatialInfo(metadata, 30)
        ds: gdal.Dataset = gdal.BuildVRT(filenameSpectralGeolocation, [ds1, ds2], separate=True)
        ds.SetProjection(crs.toWkt())
        ds.SetGeoTransform(geoTransform)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setBandName('Longitude', 1)
        writer.setBandName('Latitude', 2)
        writer.close()

    def writeSpectralGeometricFields(self, filenameSpectralGeometric, he5Filename):
        if filenameSpectralGeometric is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L2D_HCO/Geometric_Fields/Observing_Angle')
        ds2 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L2D_HCO/Geometric_Fields/Rel_Azimuth_Angle')
        ds3 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L2D_HCO/Geometric_Fields/Solar_Zenith_Angle')
        metadata = ds1.GetMetadata('')
        crs, extent, geoTransform = self.spatialInfo(metadata, 30)
        ds: gdal.Dataset = gdal.BuildVRT(filenameSpectralGeometric, [ds1, ds2, ds3], separate=True)
        ds.SetProjection(crs.toWkt())
        ds.SetGeoTransform(geoTransform)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setNoDataValue(0)
        writer.setBandName('Observing Angle', 1)
        writer.setBandName('Relative Azimuth Angle', 2)
        writer.setBandName('Solar Zinith Angle', 3)
        writer.close()

    def writePanCube(self, filenamePanCube, he5Filename):
        if filenamePanCube is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L2D_PCO/Data_Fields/Cube')
        metadata = ds1.GetMetadata('')
        crs, extent, geoTransform = self.spatialInfo(metadata, 5)
        ds: gdal.Dataset = gdal.BuildVRT(filenamePanCube, [ds1], separate=True)
        ds.SetProjection(crs.toWkt())
        ds.SetGeoTransform(geoTransform)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setNoDataValue(0)
        writer.setScale(1. / 65535., 1)
        writer.setBandName('Panchromatic', 1)
        writer.close()

    def writePanGeolocationFields(self, filenamePanGeolocation, he5Filename):
        if filenamePanGeolocation is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L2D_PCO/Geolocation_Fields/Longitude')
        ds2 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L2D_PCO/Geolocation_Fields/Latitude')
        metadata = ds1.GetMetadata('')
        crs, extent, geoTransform = self.spatialInfo(metadata, 5)
        ds: gdal.Dataset = gdal.BuildVRT(filenamePanGeolocation, [ds1, ds2], separate=True)
        ds.SetProjection(crs.toWkt())
        ds.SetGeoTransform(geoTransform)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setBandName('Longitude', 1)
        writer.setBandName('Latitude', 2)
        writer.close()

    def writePanErrorMatrix(self, filenamePanError, he5Filename):
        if filenamePanError is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L2D_PCO/Data_Fields/PIXEL_L2_ERR_MATRIX')
        metadata = ds1.GetMetadata('')
        crs, extent, geoTransform = self.spatialInfo(metadata, 5)
        ds: gdal.Dataset = gdal.BuildVRT(filenamePanError, [ds1], separate=True)
        ds.SetProjection(crs.toWkt())
        ds.SetGeoTransform(geoTransform)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setBandName('PAN Band Pixel Error', 1)
        writer.close()

    def spatialInfo(self, metadata, res):
        extent = QgsRectangle(
            float(metadata['Product_ULcorner_easting']) - res / 2,
            float(metadata['Product_LRcorner_northing']) - res / 2,
            float(metadata['Product_LRcorner_easting']) + res / 2,
            float(metadata['Product_ULcorner_northing']) + res / 2
        )
        crs = QgsCoordinateReferenceSystem.fromEpsgId(int(metadata['Epsg_Code']))
        geoTransform = (extent.xMinimum(), res, -0., extent.yMaximum(), -0., -res)
        return crs, extent, geoTransform
