import shutil
import traceback
from os.path import basename, exists
from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsMapLayer)
from typeguard import typechecked


@typechecked
class ImportPrismaL1Algorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'File'
    P_SPECTRAL_REGION, _SPECTRAL_REGION = 'spectralRegion', 'Spectral region'
    O_SPECTRAL_REGION = ['VNIR/SWIR combined', 'VNIR only', 'SWIR only', ]
    VnirSwirRegion, VnirRegion, SwirRegion = range(3)
    P_OUTPUT_SPECTRAL_CUBE, _OUTPUT_SPECTRAL_CUBE = 'outputPrismaL1_spectralCube', 'Output VNIR/SWIR Cube raster layer'
    P_OUTPUT_PAN_CUBE, _OUTPUT_PAN_CUBE = 'outputPrismaL1_panCube', 'Output PAN raster layer'
    P_OUTPUT_CLOUD_MASK, _OUTPUT_CLOUD_MASK = 'outputPrismaL1_cloudMask', 'Output Cloud Mask raster layer'
    P_OUTPUT_LANDCOVER_MASK, _OUTPUT_LANDCOVER_MASK = 'outputPrismaL1_landCoverMask', \
                                                      'Output Land Cover Mask raster layer'
    P_OUTPUT_SUN_GLINT_MASK, _OUTPUT_SUN_GLINT_MASK = 'outputPrismaL1_sunGlintMask', \
                                                      'Output Sun Glint Mask raster layer'
    P_OUTPUT_SPECTRAL_ERROR, _OUTPUT_SPECTRAL_ERROR = 'outputPrisma1_spectralErrorMatrix', \
                                                      'Output VNIR/SWIR Error Matrix raster layer'
    P_OUTPUT_SPECTRAL_GEOLOCATION, _OUTPUT_SPECTRAL_GEOLOCATION = 'outputPrismaL1_spectralGeolocationFields', \
                                                                  'Output VNIR/SWIR Geolocation Fields raster layer'
    P_OUTPUT_PAN_GEOLOCATION, _OUTPUT_PAN_GEOLOCATION = 'outputPrismaL1_panGeolocationFields', \
                                                        'Output PAN Geolocation Fields raster layer'
    P_OUTPUT_PAN_ERROR, _OUTPUT_PAN_ERROR = 'outputPrismaL1_panErrorMatrix', \
                                            'Output PAN Error Matrix raster layer'

    def displayName(self):
        return 'Import PRISMA L1 product'

    def shortDescription(self):
        link = EnMAPProcessingAlgorithm.htmlLink(
            'http://prisma.asi.it/missionselect/docs.php', 'PRISMA Documentation Area'
        )
        return 'Import PRISMA L1 product from HE5 file to QGIS/GDAL conform GTiff/VRT file format.' \
               'Note that for the spectral cube and error matrix, the interleave is transposed ' \
               'and stored as GTiff to enable proper visualization in QGIS.' \
               'All other sub-datasets are stored as light-weight VRT files.\n' \
               f'For further details visit the {link}.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The HE5 product file.\n'
                         'The main data contained in the PRS_L1_HRC Swath is the Radiometric Calibrated '
                         'Coregistersed Hyperspectral Cube. All bands of VNIR Cube and all bands of SWIR Cube are '
                         'keystone corrected with respect to VNIR Cube band 128 only considering shift Across track.\n'
                         'The PRS_L1_PCO Swath basically contains the Radiometric Calibrated Coregistered Panchromatic '
                         'Image. The PAN Cube is coregistered with respect to VNIR Cube taking into account of the '
                         'Along Track coregistration. PAN Cube also takes into account the Across track offset '
                         'PAN – VNIR. All pixel of PAN Cube are keystone corrected with respect to VNIR Cube band 128 '
                         'only considering shift Across track.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the HE5 file directly from your system file browser on '
                         'the EnMAP-Box map view area.'),
            (self._SPECTRAL_REGION, 'Spectral region to be imported.'),
            (self._OUTPUT_SPECTRAL_CUBE, 'VNIR/SWIR Cube GTiff raster file destination.'),
            (self._OUTPUT_PAN_CUBE, 'PAN VRT raster file destination.'),
            (self._OUTPUT_CLOUD_MASK, 'Cloud Mask VRT raster file destination.'),
            (self._OUTPUT_LANDCOVER_MASK, 'Land Cover Mask VRT raster file destination.'),
            (self._OUTPUT_SUN_GLINT_MASK, 'Sun Glint Mask VRT raster file destination.'),
            (self._OUTPUT_SPECTRAL_GEOLOCATION, 'VNIR/SWIR Geolocation Fields VRT raster file destination. '
                                                'Includes Latitude and Longitude bands.'),
            (self._OUTPUT_SPECTRAL_ERROR, 'VNIR/SWIR Pixel Error Matrix GTiff raster file destination.'),
            (self._OUTPUT_PAN_GEOLOCATION, 'PAN Geolocation Fields VRT raster file destination. '
                                           'Includes Latitude and Longitude bands.'),
            (self._OUTPUT_PAN_ERROR, 'PAN Pixel Error Matrix VRT raster file destination.'),
        ]

    def group(self):
        return Group.Test.value + Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FILE, self._FILE, extension='he5')
        self.addParameterEnum(self.P_SPECTRAL_REGION, self._SPECTRAL_REGION, self.O_SPECTRAL_REGION, False, 0)
        self.addParameterRasterDestination(self.P_OUTPUT_SPECTRAL_CUBE, self._OUTPUT_SPECTRAL_CUBE)
        self.addParameterVrtDestination(self.P_OUTPUT_PAN_CUBE, self._OUTPUT_PAN_CUBE, None, True, False)
        self.addParameterVrtDestination(self.P_OUTPUT_CLOUD_MASK, self._OUTPUT_CLOUD_MASK, None, True, False)
        self.addParameterVrtDestination(self.P_OUTPUT_LANDCOVER_MASK, self._OUTPUT_LANDCOVER_MASK, None, True, False)
        self.addParameterVrtDestination(self.P_OUTPUT_SUN_GLINT_MASK, self._OUTPUT_SUN_GLINT_MASK, None, True, False)
        self.addParameterRasterDestination(self.P_OUTPUT_SPECTRAL_ERROR, self._OUTPUT_SPECTRAL_ERROR, None, True, False)
        self.addParameterVrtDestination(
            self.P_OUTPUT_SPECTRAL_GEOLOCATION, self._OUTPUT_SPECTRAL_GEOLOCATION, None, True, False
        )
        self.addParameterVrtDestination(self.P_OUTPUT_PAN_GEOLOCATION, self._OUTPUT_PAN_GEOLOCATION, None, True, False)
        self.addParameterVrtDestination(self.P_OUTPUT_PAN_ERROR, self._OUTPUT_PAN_ERROR, None, True, False)

    def defaultParameters(self, file: str):
        return {
            self.P_FILE: file,
            self.P_OUTPUT_SPECTRAL_CUBE: file.replace('.he5', '_SPECTRAL.tif'),
            self.P_OUTPUT_PAN_CUBE: file.replace('.he5', '_PAN.vrt'),
            self.P_OUTPUT_CLOUD_MASK: file.replace('.he5', '_CLOUD_MASK.vrt'),
            self.P_OUTPUT_LANDCOVER_MASK: file.replace('.he5', '_LANDCOVER_MASK.vrt'),
            self.P_OUTPUT_SUN_GLINT_MASK: file.replace('.he5', '_SUNGLINT_MASK.vrt'),
            self.P_OUTPUT_SPECTRAL_ERROR: file.replace('.he5', '_SPECTRAL_ERROR.tif'),
            self.P_OUTPUT_SPECTRAL_GEOLOCATION: file.replace('.he5', '_SPECTRAL_GEOLOCATION.vrt'),
            self.P_OUTPUT_PAN_GEOLOCATION: file.replace('.he5', '_PAN_GEOLOCATION.vrt'),
            self.P_OUTPUT_PAN_ERROR: file.replace('.he5', '_PAN_ERROR.vrt')
        }

    def isValidFile(self, file: str) -> bool:
        return basename(file).startswith('PRS_L1') & \
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
        filenameSpectralCube = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_SPECTRAL_CUBE, context)
        filenameCloudMask = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_CLOUD_MASK, context)
        filenameLandCoverMask = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_LANDCOVER_MASK, context)
        filenameSunGlintMask = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_SUN_GLINT_MASK, context)
        filenameSpectralError = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_SPECTRAL_ERROR, context)
        filenameSpectralGeolocation = self.parameterAsOutputLayer(
            parameters, self.P_OUTPUT_SPECTRAL_GEOLOCATION, context
        )
        filenamePanCube = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PAN_CUBE, context)
        filenamePanGeolocation = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PAN_GEOLOCATION, context)
        filenamePanError = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PAN_ERROR, context)

        with open(filenameSpectralCube + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'PRS_L1_STD_OFFL_20201107101404_20201107101408_0001.he5'
            if not self.isValidFile(he5Filename):
                message = f'not a valid PRISMA L1 product: {he5Filename}'
                raise QgsProcessingException(message)

            self.writeSpectralErrorMatrix(filenameSpectralError, he5Filename, spectralRegion, feedback)
            self.writeSpectralCube(filenameSpectralCube, he5Filename, spectralRegion, feedback)
            self.writeSpectralGeolocationFields(filenameSpectralGeolocation, he5Filename)

            self.writePanCube(filenamePanCube, he5Filename)
            self.writePanGeolocationFields(filenamePanGeolocation, he5Filename)
            self.writePanErrorMatrix(filenamePanError, he5Filename)
            self.writeCloudMask(filenameCloudMask, he5Filename)
            self.writeLandCoverMask(filenameLandCoverMask, he5Filename)
            self.writeSinGlintMask(filenameSunGlintMask, he5Filename)

            utilsDeleteCopy(he5Filename)

            result = {
                self.P_OUTPUT_SPECTRAL_CUBE: filenameSpectralCube,
                self.P_OUTPUT_SPECTRAL_GEOLOCATION: filenameSpectralGeolocation,
                self.P_OUTPUT_SPECTRAL_ERROR: filenameSpectralError,
                self.P_OUTPUT_PAN_CUBE: filenamePanCube,
                self.P_OUTPUT_PAN_GEOLOCATION: filenamePanGeolocation,
                self.P_OUTPUT_PAN_ERROR: filenamePanError,
                self.P_OUTPUT_CLOUD_MASK: filenameCloudMask,
                self.P_OUTPUT_LANDCOVER_MASK: filenameLandCoverMask,
                self.P_OUTPUT_SUN_GLINT_MASK: filenameSunGlintMask
            }

            self.toc(feedback, result)

        return result

    def writeSpectralCube(self, filenameSpectralCube, he5Filename, spectralRegion, feedback):
        parseFloatList = lambda text: [float(item) for item in text.split()]
        array = list()
        metadata = dict()
        wavelength = list()
        fwhm = list()
        # - VNIR
        if spectralRegion in [self.VnirSwirRegion, self.VnirRegion]:
            key = 'HDFEOS/SWATHS/PRS_L1_HCO/Data Fields/VNIR_Cube'
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
            key = 'HDFEOS/SWATHS/PRS_L1_HCO/Data Fields/SWIR_Cube'
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
        # - mask no data region
        mask = np.all(np.equal(array, 0), axis=0)
        array = np.clip(array, 1, None)
        array[:, mask] = 0
        assert len(wavelength) == len(array)
        assert len(fwhm) == len(array)
        driver = Driver(filenameSpectralCube, feedback=feedback)
        writer = driver.createFromArray(array)
        writer.setNoDataValue(0)
        writer.setMetadataDomain(metadata)
        for bandNo in range(1, writer.bandCount() + 1):
            wl = wavelength[bandNo - 1]
            writer.setBandName(f'Band {bandNo} ({wl} Nanometers)', bandNo)
            writer.setWavelength(wl, bandNo)
            writer.setFwhm(fwhm[bandNo - 1], bandNo)

    def writeSpectralErrorMatrix(self, filenameSpectralError, he5Filename, spectralRegion, feedback):
        if filenameSpectralError is None:
            return None
        parseFloatList = lambda text: [float(item) for item in text.split()]
        array = list()
        metadata = dict()
        wavelength = list()
        # - VNIR
        if spectralRegion in [self.VnirSwirRegion, self.VnirRegion]:
            key = 'HDFEOS/SWATHS/PRS_L1_HCO/Data Fields/VNIR_PIXEL_SAT_ERR_MATRIX'
            dsVnir = self.openDataset(he5Filename, key)
            arrayVnir = utilsReadAsArray(dsVnir, he5Filename, key, feedback)
            metadataVnir = dsVnir.GetMetadata('')
            selectedVnir = [v != 0 for v in parseFloatList(metadataVnir['List_Cw_Vnir'])]
            arrayVnir = np.transpose(arrayVnir, [1, 0, 2])[selectedVnir][::-1]
            wavelengthVnir = list(reversed(
                [float(v) for v, flag in zip(parseFloatList(metadataVnir['List_Cw_Vnir']), selectedVnir) if flag]
            ))
            array.extend(arrayVnir)
            wavelength.extend(wavelengthVnir)
            metadata.update(metadataVnir)
        # - SWIR
        if spectralRegion in [self.VnirSwirRegion, self.SwirRegion]:
            key = 'HDFEOS/SWATHS/PRS_L1_HCO/Data Fields/SWIR_PIXEL_SAT_ERR_MATRIX'
            dsSwir = self.openDataset(he5Filename, key)
            arraySwir = utilsReadAsArray(dsSwir, he5Filename, key, feedback)
            metadataSwir = dsSwir.GetMetadata('')
            selectedSwir = [v != 0 for v in parseFloatList(metadataSwir['List_Cw_Swir'])]
            arraySwir = np.transpose(arraySwir, [1, 0, 2])[selectedSwir][::-1]
            wavelengthSwir = list(reversed(
                [float(v) for v, flag in zip(parseFloatList(metadataSwir['List_Cw_Swir']), selectedSwir) if flag]
            ))
            array.extend(arraySwir)
            wavelength.extend(wavelengthSwir)
            metadata.update(metadataSwir)
        # - mask no data region
        assert len(wavelength) == len(array)
        driver = Driver(filenameSpectralError, feedback=feedback)
        writer = driver.createFromArray(array)
        writer.setMetadataDomain(metadata)
        for bandNo in range(1, writer.bandCount() + 1):
            wl = wavelength[bandNo - 1]
            writer.setBandName(f'Pixel Error Band {bandNo} ({wl} Nanometers)', bandNo)
            writer.setWavelength(wl, bandNo)

    def writeSpectralGeolocationFields(self, filenameSpectralGeolocation, he5Filename):
        if filenameSpectralGeolocation is None:
            return
        # We have Geolocation Fields for VNIR and SWIR, but both seam to be identical, so we just use the VNIR version.
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L1_HCO/Geolocation_Fields/Longitude_VNIR')
        ds2 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L1_HCO/Geolocation_Fields/Latitude_VNIR')
        metadata = ds1.GetMetadata('')
        ds: gdal.Dataset = gdal.BuildVRT(filenameSpectralGeolocation, [ds1, ds2], separate=True)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setBandName('Longitude', 1)
        writer.setBandName('Latitude', 2)

    def writePanCube(self, filenamePanCube, he5Filename):
        if filenamePanCube is None:
            return
        key = 'HDFEOS/SWATHS/PRS_L1_PCO/Data Fields/Cube'
        ds1 = self.openDataset(he5Filename, key)
        metadata = ds1.GetMetadata('')
        ds: gdal.Dataset = gdal.BuildVRT(filenamePanCube, [ds1], separate=True)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setNoDataValue(0)
        writer.setBandName('Panchromatic', 1)

    def writePanGeolocationFields(self, filenamePanGeolocation, he5Filename):
        if filenamePanGeolocation is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L1_PCO/Geolocation Fields/Longitude')
        ds2 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L1_PCO/Geolocation Fields/Latitude')
        metadata = ds1.GetMetadata('')
        ds: gdal.Dataset = gdal.BuildVRT(filenamePanGeolocation, [ds1, ds2], separate=True)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setBandName('Longitude', 1)
        writer.setBandName('Latitude', 2)

    def writePanErrorMatrix(self, filenamePanError, he5Filename):
        if filenamePanError is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L1_PCO/Data_Fields/PIXEL_SAT_ERR_MATRIX')
        metadata = ds1.GetMetadata('')
        ds: gdal.Dataset = gdal.BuildVRT(filenamePanError, [ds1], separate=True)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setBandName('PAN Band Pixel Error', 1)

    def writeCloudMask(self, filenameCloudMask, he5Filename):
        if filenameCloudMask is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L1_HCO/Data_Fields/Cloud_Mask')
        metadata = ds1.GetMetadata('')
        ds: gdal.Dataset = gdal.BuildVRT(filenameCloudMask, [ds1], separate=True)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setBandName('Cloud Mask', 1)
        del writer, ds

        reader = RasterReader(filenameCloudMask)
        categories = [
            Category(0, 'not cloudy pixel', '#000000'),
            Category(1, 'cloudy pixel', '#ffffff'),
            Category(10, 'not of all previous classification', '#ffff00'),
            Category(255, 'error', '#ff1dce'),
        ]
        renderer = Utils.palettedRasterRendererFromCategories(reader.provider, 1, categories)
        reader.layer.setRenderer(renderer)
        reader.layer.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

    def writeLandCoverMask(self, filenameLandCoverMask, he5Filename):
        if filenameLandCoverMask is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L1_HCO/Data_Fields/LandCover_Mask')
        metadata = ds1.GetMetadata('')
        ds: gdal.Dataset = gdal.BuildVRT(filenameLandCoverMask, [ds1], separate=True)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setBandName('Land Cover Mask', 1)
        del writer, ds

        reader = RasterReader(filenameLandCoverMask)
        categories = [
            Category(0, 'water', '#0064ff'), Category(1, 'snow', '#fffafa'),
            Category(2, 'not-vegetated land pixel / bare soil', '#a87000'),
            Category(3, 'crop and rangeland', '#98e600'),
            Category(4, 'forst ', '#267300'),
            Category(5, 'wetland', '#41cdc5'),
            Category(6, 'not-vegetated land pixel / urban component', '#e60000'),
            Category(10, 'not of all previous classification', '#ffff00'),
            Category(255, 'error', '#ff1dce'),
        ]
        renderer = Utils.palettedRasterRendererFromCategories(reader.provider, 1, categories)
        reader.layer.setRenderer(renderer)
        reader.layer.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

    def writeSinGlintMask(self, filenameSunGlintMask, he5Filename):
        if filenameSunGlintMask is None:
            return
        ds1 = self.openDataset(he5Filename, 'HDFEOS/SWATHS/PRS_L1_HCO/Data_Fields/SunGlint_Mask')
        metadata = ds1.GetMetadata('')
        ds: gdal.Dataset = gdal.BuildVRT(filenameSunGlintMask, [ds1], separate=True)
        writer = RasterWriter(ds)
        writer.setMetadataDomain(metadata)
        writer.setBandName('Sun Glint Mask', 1)
        del writer, ds

        reader = RasterReader(filenameSunGlintMask)
        categories = [
            Category(0, 'not sun glint', '#000000'),
            Category(1, 'sun glint', '#ffffff'),
            Category(10, 'not of all previous classification', '#ffff00'),
            Category(255, 'error', '#ff1dce'),
        ]
        renderer = Utils.palettedRasterRendererFromCategories(reader.provider, 1, categories)
        reader.layer.setRenderer(renderer)
        reader.layer.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)


def utilsReadAsArray(dataset: gdal.Dataset, filename, key: str, feedback: QgsProcessingFeedback):
    # We first try to read PRISMA data with the h5py API, which is super fast.
    # Only if that fails, we use GDAL API, which is super slow, because of the dumb BIP interleave storage.

    # use HE5 copy: Workaround for issue #1330 to avoid OSError: Unable to open file (file close degree doesn't match)
    filename2 = filename + '.copy.he5'
    if not exists(filename2):
        shutil.copyfile(filename, filename2)
    try:
        import h5py
        feedback.pushInfo(f'Reading data with h5py (v{h5py.__version__}) API: {key}')
        with h5py.File(filename2, 'r') as file:
            array = file[key][()]
    except Exception:
        traceback.print_exc()
        feedback.pushWarning(
            'Reading data with h5py API failed. Fall back to GDAL API, which is very slow on PRISMA BIP '
            f'interleaved data: {dataset.GetDescription()}'
        )
        array = dataset.ReadAsArray()
    return array


def utilsDeleteCopy(filename):
    # Workaround for issue #1330 to avoid OSError: Unable to open file (file close degree doesn't match)

    try:
        import os
        filename2 = filename + '.copy.he5'
        if exists(filename2):
            os.remove(filename2)
    except Exception:
        traceback.print_exc()
        pass
