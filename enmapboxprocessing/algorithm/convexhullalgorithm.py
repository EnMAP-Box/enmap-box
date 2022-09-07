from math import ceil, isnan
from typing import Dict, Any, List, Tuple

import numpy as np
from scipy import interpolate
from scipy.spatial import ConvexHull

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis)
from typeguard import typechecked


@typechecked
class ConvexHullAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_X_UNITS, _X_UNITS = 'xUnits', 'X units'
    O_X_UNITS = ['Band numbers', 'Nanometers']
    BandNumberUnits, NanometerUnits = range(len(O_X_UNITS))
    P_OUTPUT_CONVEX_HULL, _OUTPUT_CONVEX_HULL = 'outputConvexHull', 'Output convex hull raster layer'
    P_OUTPUT_CONTINUUM_REMOVED, _OUTPUT_CONTINUUM_REMOVED = 'outputContinuumRemoved', 'Output continuum removed raster layer'

    def displayName(self) -> str:
        return 'Convex hull and continuum-removal'

    def shortDescription(self) -> str:
        return 'Calculate convex hull and continuum-removed raster layers.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Raster layer with spectral profiles.'),
            (self._X_UNITS, 'The x units used for convex hull calculations. '
                            'In case of Nanometers, only spectral bands are used.'),
            (self._OUTPUT_CONVEX_HULL, self.RasterFileDestination),
            (self._OUTPUT_CONTINUUM_REMOVED, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.RasterAnalysis.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterEnum(self.P_X_UNITS, self._X_UNITS, self.O_X_UNITS, False, 0, False)
        self.addParameterRasterDestination(self.P_OUTPUT_CONVEX_HULL, self._OUTPUT_CONVEX_HULL, None, True, True)
        self.addParameterRasterDestination(
            self.P_OUTPUT_CONTINUUM_REMOVED, self._OUTPUT_CONTINUUM_REMOVED, None, True, True
        )

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        xUnits = self.parameterAsEnum(parameters, self.P_X_UNITS, context)
        filenameConvexHull = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_CONVEX_HULL, context)
        filenameContinuumRemoved = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_CONTINUUM_REMOVED, context)

        result = dict()
        if filenameConvexHull is not None:
            result[self.P_OUTPUT_CONVEX_HULL] = filenameConvexHull
        if filenameContinuumRemoved is not None:
            result[self.P_OUTPUT_CONTINUUM_REMOVED] = filenameContinuumRemoved
        if len(result) == 0:
            return result

        filenameLog = filenameConvexHull if filenameContinuumRemoved is None else filenameConvexHull
        with open(filenameLog + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)

            bandList = list()
            xValues = list()
            for bandNo in reader.bandNumbers():
                if xUnits == self.BandNumberUnits:
                    bandList.append(bandNo)
                    xValues.append(bandNo)
                elif xUnits == self.NanometerUnits:
                    wavelength = reader.wavelength(bandNo)
                    if not isnan(wavelength):
                        bandList.append(bandNo)
                        xValues.append(wavelength)
                else:
                    raise ValueError

            if filenameConvexHull is not None:
                writerConvexHull = Driver(filenameConvexHull, feedback=feedback).createLike(reader)
            if filenameContinuumRemoved is not None:
                writerContinuumRemoved = Driver(
                    filenameContinuumRemoved, feedback=feedback
                ).createLike(reader, Qgis.Float32)

            lineMemoryUsage = reader.lineMemoryUsage(dataTypeSize=4) * 3
            blockSizeY = min(raster.height(), ceil(Utils.maximumMemoryUsage() / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
                array = np.array(reader.arrayFromBlock(block, bandList))
                valid = np.all(reader.maskArray(array, bandList), axis=0)

                noDataValueConvexHull = Utils.defaultNoDataValue(array.dtype)
                arrayConvexHull = np.full_like(array, noDataValueConvexHull, dtype=array.dtype)
                noDataValueContinuumRemoved = Utils.defaultNoDataValue(np.float32)
                arrayContinuumRemoved = np.full_like(array, noDataValueContinuumRemoved, np.float32)

                for yi in range(array.shape[1]):
                    feedback.setProgress((block.yOffset + yi) / reader.height() * 100)
                    for xi in range(array.shape[2]):
                        if valid[yi, xi]:
                            yValues = list(array[:, yi, xi])
                            continuumRemovedValues, convexHullValues = self.convexHullRemoval(yValues, xValues)
                            arrayConvexHull[:, yi, xi] = convexHullValues
                            arrayContinuumRemoved[:, yi, xi] = continuumRemovedValues

                if filenameConvexHull is not None:
                    writerConvexHull.writeArray(arrayConvexHull, xOffset=block.xOffset, yOffset=block.yOffset)
                if filenameContinuumRemoved is not None:
                    writerContinuumRemoved.writeArray(
                        arrayContinuumRemoved, xOffset=block.xOffset, yOffset=block.yOffset
                    )

            for i, bandNo in enumerate(bandList):
                bandName = reader.bandName(bandNo)
                wavelength = reader.wavelength(bandNo)
                fwhm = reader.fwhm(bandNo)
                if filenameConvexHull is not None:
                    writerConvexHull.setBandName(bandName, i + 1)
                    writerConvexHull.setWavelength(wavelength, i + 1)
                    writerConvexHull.setFwhm(fwhm, i + 1)
                if filenameContinuumRemoved is not None:
                    writerContinuumRemoved.setBandName(bandName, i + 1)
                    writerContinuumRemoved.setWavelength(wavelength, i + 1)
                    writerContinuumRemoved.setFwhm(fwhm, i + 1)

            self.toc(feedback, result)

        return result

    @staticmethod
    def convexHullRemoval(yValues, xValues):
        # Code was adopted from pysptools.spectro.hull_removal:
        #     https://pysptools.sourceforge.io/_modules/pysptools/spectro/hull_removal.html#convex_hull_removal
        # We use scipy.spatial.ConvexHull instead of _jarvis.convex_hull to avoid external dependencies.

        points = list(zip(xValues, yValues))

        # add extra points to close the polygon
        points = [(xValues[0], 0)] + points + [(xValues[-1], 0)]

        # calculate hull
        vertices = ConvexHull(points).vertices
        vertices = list(sorted(vertices - 1))[1:-1]  # remove extra points
        x_hull = [xValues[v] for v in vertices]
        y_hull = [yValues[v] for v in vertices]

        # interpolate to all bands
        tck = interpolate.splrep(x_hull, y_hull, k=1)
        convexHullValues = interpolate.splev(xValues, tck, der=0)
        continuumRemovedValues = np.true_divide(yValues, convexHullValues, dtype=np.float32)

        return continuumRemovedValues, convexHullValues
