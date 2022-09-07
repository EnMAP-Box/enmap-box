from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessing)
from typeguard import typechecked


@typechecked
class StackRasterLayersAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTERS, _RASTERS = 'rasters', 'Raster layers'
    P_GRID, _GRID = 'grid', 'Grid'
    P_BAND, _BAND = 'band', 'Band'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def displayName(self):
        return 'Stack raster layers'

    def shortDescription(self):
        return 'Stack raster layers and store the result as a VRT file.' \
               'This is a slimmed down version of the more powerful/complicated GDAL "Build virtual raster" ' \
               'algorithm.\n' \
               'If you also want to delete or rearrange individually bands, just use the "Subset raster layer bands" ' \
               'algorithm afterwards.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTERS, 'Source raster layers.'),
            (self._GRID, 'Reference grid specifying the destination extent, pixel size and projection. '
                         'If not defined, gdal.BuildVrt defaults are used.'),
            (self._BAND, 'Specify a band number used for stacking, instead of using all bands.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.RasterMiscellaneous.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterMultipleLayers(self.P_RASTERS, self._RASTERS, QgsProcessing.TypeRaster)
        self.addParameterRasterLayer(self.P_GRID, self._GRID, None, True, True)
        self.addParameterInt(self.P_BAND, self._BAND, None, True, 1, None, advanced=True)
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        rasters = self.parameterAsLayerList(parameters, self.P_RASTERS, context)
        grid = self.parameterAsRasterLayer(parameters, self.P_GRID, context)
        band = self.parameterAsInt(parameters, self.P_BAND, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # translate into grid and split into individual bands (required for gdal.BuildVrt)
            filenames = list()
            bandNames = list()
            bandNo = 1
            for raster in rasters:
                reader = RasterReader(raster)

                if band is None:
                    bandNumbers = reader.bandNumbers()
                else:
                    bandNumbers = [band]

                for ibandNo in bandNumbers:
                    alg = TranslateRasterAlgorithm()
                    parameters = {
                        alg.P_RASTER: raster,
                        alg.P_GRID: grid,
                        alg.P_BAND_LIST: [ibandNo],
                        alg.P_CREATION_PROFILE: self.DefaultVrtCreationProfile,
                        alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, f'band {bandNo}.vrt')
                    }
                    self.runAlg(alg, parameters, None, feedback2, context, True)
                    filenames.append(parameters[alg.P_OUTPUT_RASTER])
                    bandNames.append(reader.bandName(ibandNo))
                    bandNo += 1

            # stack bands
            options = gdal.BuildVRTOptions(separate=True)
            ds: gdal.Dataset = gdal.BuildVRT(filename, filenames, options=options)
            writer = RasterWriter(ds)
            for bandNo, bandName in enumerate(bandNames, 1):
                writer.setBandName(bandName, bandNo)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
