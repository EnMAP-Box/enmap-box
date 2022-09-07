from os.path import basename
from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)
from typeguard import typechecked


@typechecked
class ImportLandsatL2Algorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputLandsatL2Raster', 'Output raster layer'

    def displayName(self):
        return 'Import Landsat L2 product'

    def shortDescription(self):
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength information is set and data is scaled into the 0 to 1 range.' \
               'Supports Landsat 4 to 9, collection 1 and 2. '

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The *.MTL.txt metadata file associated with the product.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the metadata MTL.txt file directly from your system file browser onto '
                         'the EnMAP-Box map view area.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FILE, self._FILE, extension='txt')
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def isValidFile(self, mtlFilename: str) -> bool:
        return basename(mtlFilename).startswith('L') & \
               mtlFilename.endswith('MTL.txt')

    def defaultParameters(self, mtlFilename: str):
        return {
            self.P_FILE: mtlFilename,
            self.P_OUTPUT_RASTER: mtlFilename.replace('MTL.txt', 'SR.vrt'),
        }

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        mtlFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'LC08_L1TP_014032_20190330_20190404_01_T1_MTL.txt'
            # also note https://www.usgs.gov/media/images/landsat-collection-1-product-identifier
            message = f'not a valid Landsat L2 product: {mtlFilename}'
            if not self.isValidFile(mtlFilename):
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            collectionNumber = mtlFilename[-13:-11]

            if collectionNumber == '01':
                pattern = 'sr_band{}.tif'
                gain = 1. / 10000
                offset = None
            elif collectionNumber == '02':
                pattern = 'SR_B{}.TIF'
                gain = 0.0000275  # see https://www.usgs.gov/core-science-systems/nli/landsat/landsat-collection-2-level-2-science-products
                offset = -0.2
            else:
                raise QgsProcessingException(f'unknown collection number: {collectionNumber}')

            if basename(mtlFilename).startswith('LC') or basename(mtlFilename).startswith('LO'):
                # https://landsat.gsfc.nasa.gov/landsat-8/landsat-8-bands
                bandNumbers = [1, 2, 3, 4, 5, 6, 7]
                bandNames = ['Coastal aerosol', 'Blue', 'Green', 'Red', 'NIR', 'SWIR-1', 'SWIR-2']
                wavelength = '{443, 482, 562, 655, 865, 1610, 2200}'
            elif basename(mtlFilename).startswith('LE'):
                # https://landsat.gsfc.nasa.gov/landsat-7/landsat-7-etm-bands
                bandNumbers = [1, 2, 3, 4, 5, 7]
                bandNames = ['Blue', 'Green', 'Red', 'NIR', 'SWIR-1', 'SWIR-2']
                wavelength = '{482, 565, 659, 837, 1650, 2215}'
            elif basename(mtlFilename).startswith('LT'):
                # https://landsat.gsfc.nasa.gov/landsat-4-5/tm
                bandNumbers = [1, 2, 3, 4, 5, 7]
                bandNames = ['Blue', 'Green', 'Red', 'NIR', 'SWIR-1', 'SWIR-2']
                wavelength = '{485, 560, 659, 830, 1650, 2215}'
            else:
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            filenames = [mtlFilename.replace('MTL.txt', key)
                         for key in [pattern.format(i) for i in bandNumbers]]

            # create VRTs
            options = gdal.BuildVRTOptions(separate=True, xRes=30, yRes=30)
            ds = gdal.BuildVRT(filename, filenames, options=options)
            ds.SetMetadataItem('wavelength', wavelength, 'ENVI')
            ds.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
            wavelength = wavelength[1:-1].split(',')
            for bandNo, (name, wl) in enumerate(zip(bandNames, wavelength), 1):
                rb: gdal.Band = ds.GetRasterBand(bandNo)
                rb.SetDescription(name + f' ({wl} Nanometers)')
                if gain is not None:
                    rb.SetScale(gain)
                if offset is not None:
                    rb.SetOffset(offset)
            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
