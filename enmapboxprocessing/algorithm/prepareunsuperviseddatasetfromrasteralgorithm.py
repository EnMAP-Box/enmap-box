from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.algorithm.rasterizevectoralgorithm import RasterizeVectorAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsVectorLayer)
from typeguard import typechecked


@typechecked
class PrepareUnsupervisedDatasetFromRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_FEATURE_RASTER, _FEATURE_RASTER = 'featureRaster', 'Raster layer with features'
    P_MASK, _MASK = 'mask', 'Mask layer'
    P_SAMPLE_SIZE, _SAMPLE_SIZE = 'sampleSize', 'Sample size'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputUnsupervisedDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create unsupervised dataset (from feature raster)'

    def shortDescription(self) -> str:
        return 'Create an unsupervised dataset by sampling data from valid pixels ' \
               'and store the result as a pickle file.\n' \
               'A pixel is concidered valid, if the pixel profile is free of no data values, ' \
               'and not excluded by the (optionally) selected mask layer.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FEATURE_RASTER, 'Raster layer used for sampling feature data X.'),
            (self._MASK, 'A mask layer for limitting sample locations.'),
            (self._SAMPLE_SIZE, 'Approximate number of samples drawn from raster. '
                                'If 0, whole raster will be used. '
                                'Note that this is only a hint for limiting the number of rows and columns.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_FEATURE_RASTER, self._FEATURE_RASTER)
        self.addParameterMapLayer(self.P_MASK, self._MASK, None, True)
        self.addParameterInt(self.P_SAMPLE_SIZE, self._SAMPLE_SIZE, 0, True, 0)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_FEATURE_RASTER, context)
        mask = self.parameterAsLayer(parameters, self.P_MASK, context)
        sampleSize = self.parameterAsInt(parameters, self.P_SAMPLE_SIZE, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # prepare mask layer
            if mask is not None:
                if isinstance(mask, QgsRasterLayer):
                    alg = TranslateRasterAlgorithm()
                    alg.initAlgorithm()
                    parameters = {
                        alg.P_RASTER: mask,
                        alg.P_GRID: raster,
                        alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'mask.vrt')
                    }
                    self.runAlg(alg, parameters, None, feedback2, context, True)
                    mask = QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER])
                elif isinstance(mask, QgsVectorLayer):
                    alg = RasterizeVectorAlgorithm()
                    alg.initAlgorithm()
                    parameters = {
                        alg.P_VECTOR: mask,
                        alg.P_GRID: raster,
                        alg.P_INIT_VALUE: 0,
                        alg.P_BURN_VALUE: 1,
                        alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'mask.tif')
                    }
                    self.runAlg(alg, parameters, None, feedback2, context, True)
                    mask = QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER])
                else:
                    raise ValueError()

            # sample data
            reader = RasterReader(raster)
            if mask is not None:
                isinstance(mask, QgsRasterLayer)
                readerMask = RasterReader(mask)

            if sampleSize == 0:
                lineMemoryUsage = reader.lineMemoryUsage() * 2  # x2, becaused we may extract all data
                if mask is not None:
                    lineMemoryUsage += readerMask.lineMemoryUsage()
                blockSizeY = min(raster.height(), ceil(Utils.maximumMemoryUsage() / lineMemoryUsage))
            else:
                blockSizeY = raster.height()

            blockSizeX = raster.width()
            X = list()
            for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):

                if sampleSize == 0:
                    array = reader.arrayFromBlock(block)
                else:
                    width, height = reader.samplingWidthAndHeight(1, block.extent, sampleSize)
                    array = reader.arrayFromBoundingBoxAndSize(block.extent, width, height)

                maskArray = np.all(reader.maskArray(array), axis=0)
                if mask is not None:
                    array2 = readerMask.arrayFromBlock(block)
                    maskArray2 = np.all(readerMask.maskArray(array2, defaultNoDataValue=0), axis=0)
                    maskArray = np.logical_and(maskArray, maskArray2)

                blockX = list()
                for a in array:
                    blockX.append(a[maskArray])
                X.append(blockX)
            X = np.concatenate(X, axis=1).T

            features = [RasterReader(raster).bandName(i + 1) for i in range(raster.bandCount())]
            feedback.pushInfo(f'Sampled data: X=array{list(X.shape)}')

            dump = TransformerDump(features=features, X=X)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
