from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis, QgsProcessingException)
from typeguard import typechecked

raise NotImplementedError()  # todo

@typechecked
class TemporalProfileFittingRbfEnsembleAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Temporal raster layer'
    P_FWHM, _FWHM = 'rbfFwhm', 'RBF kernel full width at half maximum (FWHM) values'
    P_WEIGHTS, _WEIGHTS = 'rbfWeights', 'RBF kernel weights'
    P_CUTOFF, _CUTOFF = 'cutoffValue', 'RBF kernel cutoff value'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def displayName(self) -> str:
        return 'Temporal profile RBF Ensemble fitting'

    def shortDescription(self) -> str:
        return 'Temporal profile fitting approach using ensembles of Radial Basis Function (RBF) convolution filters (see https://doi.org/10.1016/j.jag.2016.06.019).'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A temporal raster layer to be fitted.'),
            (self._FWHM, 'The full width at half maximum (FWHM) of the RBF kernel function in days. '
                         'For each date, the RBF kernel is convolved with the observations. '
                         'A kernel with larger FWHM has a stronger smoothing effect is stronger and the chance of '
                         'having no data values is lower. '
                         'Smaller kernels will follow the observations more closely, but the chance of having no data '
                         'values is larger.\n'
                         'Multiple kernels can be combined to take advantage of both small and large kernel sizes. '
                         'The kernels are weighted according to the data density within each kernel.'),
            (self._WEIGHTS, 'Specify kernel weights to further adjust the kernel weighting.'),
            (self._CUTOFF, 'Observations at the tails of the the RBF kernel have coefficients near 0 and thus very '
                           'little influence, and can/should be excluded from the computatiuon. '
                           'E.g. use a value of 0.5 to only concider observations inside the FWHM range.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Regression.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterString(self.P_FWHM, self._FWHM, '30, 60, 120', False, True)
        self.addParameterString(self.P_WEIGHTS, self._WEIGHTS, '3, 2, 1', False, True)
        self.addParameterPickleFile(self.P_FWHM, self._FWHM)

        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        dump = self.parameterAsRegressorDump(parameters, self.P_REGRESSOR, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_REGRESSION, context)
        maximumMemoryUsage = Utils.maximumMemoryUsage()

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            rasterReader = RasterReader(raster)
            bandNames = [rasterReader.bandName(i + 1) for i in range(rasterReader.bandCount())]

            # match regressor features with raster band names
            try:  # try to find matching bands ...
                bandList = [bandNames.index(feature) + 1 for feature in dump.features]
            except ValueError:
                bandList = None

            # ... if not possible, use original bands, if overall number of bands and features do match
            if bandList is None and len(bandNames) != len(dump.features):
                message = f'classifier features ({dump.features}) not matching raster bands ({bandNames})'
                feedback.reportError(message, fatalError=True)
                raise QgsProcessingException(message)

            if (bandList is not None) and (len(bandList) != raster.bandCount()):
                usedBandNames = [rasterReader.bandName(bandNo) for bandNo in bandList]
                feedback.pushInfo(f'Bands used as features: {", ".join(usedBandNames)}')

            nBands = len(dump.targets)
            writer = Driver(filename, feedback=feedback).createLike(rasterReader, Qgis.DataType.Float32, nBands)
            noDataValue = Utils.defaultNoDataValue(np.float32)
            lineMemoryUsage = rasterReader.lineMemoryUsage() + rasterReader.lineMemoryUsage(nBands, 4)
            blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in rasterReader.walkGrid(blockSizeX, blockSizeY, feedback):
                arrayX = rasterReader.arrayFromBlock(block, bandList)
                valid = np.all(rasterReader.maskArray(arrayX, bandList), axis=0)
                X = list()
                for a in arrayX:
                    X.append(a[valid])
                y = dump.regressor.predict(np.transpose(X))
                if y.ndim == 1:
                    y = y.reshape((-1, 1))
                arrayY = np.full((nBands, *valid.shape), noDataValue, np.float32)
                for i, aY in enumerate(arrayY):
                    aY[valid] = y[:, i]
                    writer.writeArray2d(aY, i + 1, xOffset=block.xOffset, yOffset=block.yOffset)

            for bandNo, t in enumerate(dump.targets, 1):
                writer.setBandName(t.name, bandNo)
                if t.color is not None:
                    writer.setBandColor(QColor(t.color), bandNo)
            writer.setNoDataValue(noDataValue)

            result = {self.P_OUTPUT_REGRESSION: filename}
            self.toc(feedback, result)

        return result
