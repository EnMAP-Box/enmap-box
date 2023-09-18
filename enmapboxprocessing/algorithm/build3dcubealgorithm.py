from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

import processing
from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRectangle


@typechecked
class Build3dCubeAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer with features'
    P_SPECTRAL_SCALE, _SPECTRAL_SCALE = 'spectralScale', 'Spectral Scale'
    P_DX, _DX = 'dx', 'Delta x (pixel)'
    P_DY, _DY = 'dy', 'Delta y (pixel)'
    P_OUTPUT_FACE, _OUTPUT_FACE = 'outputCubeFace', 'Output cube face'
    P_OUTPUT_SIDE, _OUTPUT_SIDE = 'outputCubeSide', 'Output cube side'

    def displayName(self) -> str:
        return 'Build 3D Cube'

    def shortDescription(self) -> str:
        return 'Build an 3D Cube visualization of a (spectral) raster layer, ' \
               'consisting of two individually stylable cube face and cube side layers. '

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'The raster layer to be visualized.'),
            (self._SPECTRAL_SCALE, 'todo'),
            (self._DX, 'The delta in x direction for creating the isometric perspective. '
                       'The 3d cube is tilted to the left for negative values, and to the right for positive values.'),
            (self._DY, 'The delta in y direction for creating the isometric perspective. '
                       'The 3d cube is tilted to the downwards for negative values, and upward for positive values.'),
            (self._OUTPUT_SIDE, self.RasterFileDestination),
            (self._OUTPUT_FACE, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Auxilliary.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterFloat(self.P_SPECTRAL_SCALE, self._SPECTRAL_SCALE, 1, True, 0, None, True)
        self.addParameterInt(self.P_DX, self._DX, 1, True, None, None, True)
        self.addParameterInt(self.P_DY, self._DY, 1, True, None, None, True)
        self.addParameterVrtDestination(self.P_OUTPUT_FACE, self._OUTPUT_FACE)
        self.addParameterRasterDestination(self.P_OUTPUT_SIDE, self._OUTPUT_SIDE)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        spectralScale = self.parameterAsFloat(parameters, self.P_SPECTRAL_SCALE, context)
        dx = self.parameterAsInt(parameters, self.P_DX, context)
        dy = self.parameterAsInt(parameters, self.P_DY, context)
        filename1 = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_FACE, context)
        filename2 = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_SIDE, context)

        with open(filename1 + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)
            extent0 = reader.extent()
            xsize0 = reader.width()
            ysize0 = reader.height()
            xres = reader.rasterUnitsPerPixelX()
            yres = reader.rasterUnitsPerPixelY()
            crs = reader.crs()
            bandCount = reader.bandCount()

            # build face
            alg = TranslateRasterAlgorithm()
            processing.run(alg, {alg.P_RASTER: raster, alg.P_OUTPUT_RASTER: filename1, alg.P_COPY_METADATA: True})
            ds = gdal.Open(filename1)
            gdalGeoTransform = (
                extent0.xMinimum() + xres * (bandCount - 1) * dx, xres, -0.,
                extent0.yMaximum() - yres * (bandCount - 1) * dy, -0., -yres
            )
            ds.SetGeoTransform(gdalGeoTransform)
            ds.SetProjection(crs.toWkt())

            # build sides
            noDataValue = Utils.defaultNoDataValue(np.float32)
            xsize = xsize0 + abs(dx) * (bandCount - 1)
            ysize = ysize0 + abs(dy) * (bandCount - 1)
            array = np.full((1, ysize, xsize), noDataValue, np.float32)

            for bandNo in reader.bandNumbers():
                arr = reader.array(bandList=[bandNo])[0]
                valid = arr != reader.noDataValue(bandNo)

                if dx >= 0 and dy >= 0:
                    xoff = (bandNo - 1) * dx
                    yoff = (bandNo - 1) * dy
                    extent = QgsRectangle(
                        extent0.xMinimum(),
                        extent0.yMinimum() - yres * (reader.bandCount() - 1) * dy,
                        extent0.xMaximum() + xres * (reader.bandCount() - 1) * dx,
                        extent0.yMaximum()
                    )
                elif dx >= 0 and dy < 0:
                    xoff = (bandNo - 1) * dx
                    yoff = (bandCount - 1) * abs(dy) - (bandNo - 1) * abs(dy)
                    extent = QgsRectangle(
                        extent0.xMinimum(),
                        extent0.yMinimum(),
                        extent0.xMaximum() + xres * (reader.bandCount() - 1) * dx,
                        extent0.yMaximum() - yres * (reader.bandCount() - 1) * dy
                    )
                elif dx < 0 and dy >= 0:
                    xoff = (bandCount - 1) * abs(dx) - (bandNo - 1) * abs(dx)
                    yoff = (bandNo - 1) * dy
                    extent = QgsRectangle(
                        extent0.xMinimum() - xres * (reader.bandCount() - 1) * abs(dx),
                        extent0.yMinimum() - yres * (reader.bandCount() - 1) * dy,
                        extent0.xMaximum(),
                        extent0.yMaximum()
                    )
                elif dx < 0 and dy < 0:
                    xoff = (bandCount - 1) * abs(dx) - (bandNo - 1) * abs(dx)
                    yoff = (bandCount - 1) * abs(dy) - (bandNo - 1) * abs(dy)
                    extent = QgsRectangle(
                        extent0.xMinimum() - xres * (reader.bandCount() - 1) * abs(dx),
                        extent0.yMinimum(),
                        extent0.xMaximum(),
                        extent0.yMaximum() - yres * (reader.bandCount() - 1) * dy
                    )
                else:
                    raise ValueError()
                subarray = array[0, yoff: yoff + ysize0, xoff: xoff + xsize0]
                subarray[valid] = arr[valid]

            writer = Driver(filename2, feedback=feedback).createFromArray(array, extent, crs)
            writer.setNoDataValue(noDataValue)
            writer.setBandName('3D Cube Side', 1)

            result = {self.P_OUTPUT_FACE: filename1, self.P_OUTPUT_SIDE: filename2}
            self.toc(feedback, result)

        return result
