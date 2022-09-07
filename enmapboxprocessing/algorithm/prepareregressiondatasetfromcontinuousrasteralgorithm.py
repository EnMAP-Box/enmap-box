from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import SampleX, SampleY, checkSampleShape, RegressorDump, \
    Target
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer)
from typeguard import typechecked


@typechecked
class PrepareRegressionDatasetFromContinuousRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_CONTINUOUS_RASTER, _CONTINUOUS_RASTER = 'continuousRaster', 'Continuous-valued raster layer'
    P_FEATURE_RASTER, _FEATURE_RASTER = 'featureRaster', 'Raster layer with features'
    P_TARGETS, _TARGETS = 'targets', 'Targets'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputRegressionDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create regression dataset (from continuous-valued raster layer and feature raster)'

    def shortDescription(self) -> str:
        return 'Create a regression dataset by sampling data for labeled pixels and store the result as a pickle file.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CONTINUOUS_RASTER,
             'Continuous-valued raster layer specifying sample locations and target data Y.'
             'If required, the layer is reprojected and resampled internally to match the feature raster grid.\n'),
            (self._FEATURE_RASTER, 'Raster layer used for sampling feature data X.'),
            (self._TARGETS, 'Bands with continuous-valued variables used as targets. '
                            'An empty selection defaults to all bands in native order.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_CONTINUOUS_RASTER, self._CONTINUOUS_RASTER)
        self.addParameterRasterLayer(self.P_FEATURE_RASTER, self._FEATURE_RASTER)
        self.addParameterBandList(
            self.P_TARGETS, self._TARGETS, None, self.P_CONTINUOUS_RASTER, True, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        regression = self.parameterAsRasterLayer(parameters, self.P_CONTINUOUS_RASTER, context)
        raster = self.parameterAsRasterLayer(parameters, self.P_FEATURE_RASTER, context)
        targets = self.parameterAsInts(parameters, self.P_TARGETS, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # resample regression
            alg = TranslateRasterAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_RASTER: regression,
                alg.P_GRID: raster,
                alg.P_BAND_LIST: targets,
                alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'regression.vrt')
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)
            regression = QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER])

            X, y = self.sampleData(raster, regression, feedback2)
            reader = RasterReader(regression)
            targets = list()
            for i in range(regression.bandCount()):
                color = reader.bandColor(i + 1)
                if color is None:
                    hexcolor = None
                else:
                    hexcolor = color.name()
                targets.append(Target(reader.bandName(i + 1), hexcolor))

            features = [RasterReader(raster).bandName(i + 1) for i in range(raster.bandCount())]
            feedback.pushInfo(f'Sampled data: X=array{list(X.shape)} y=array{list(y.shape)}')

            dump = RegressorDump(targets=targets, features=features, X=X, y=y)
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result

    @classmethod
    def sampleData(
            cls, raster: QgsRasterLayer, regression: QgsRasterLayer, feedback: QgsProcessingFeedback = None
    ) -> Tuple[SampleX, SampleY]:
        assert raster.extent() == regression.extent()
        assert (raster.width(), raster.height()) == (regression.width(), regression.height())

        maximumMemoryUsage = Utils.maximumMemoryUsage()
        reader = RasterReader(raster)
        regressionReader = RasterReader(regression)
        lineMemoryUsage = reader.lineMemoryUsage(1)
        lineMemoryUsage += regressionReader.lineMemoryUsage()
        blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
        blockSizeX = raster.width()

        X = list()
        Y = list()
        for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
            arrayRegression = regressionReader.arrayFromBlock(block)
            labeled = np.all(regressionReader.maskArray(arrayRegression), axis=0)
            blockY = list()
            for a in arrayRegression:
                blockY.append(a[labeled])
            blockX = list()
            for bandNo in range(1, reader.bandCount() + 1):
                arrayBand = reader.arrayFromBlock(block, [bandNo])[0]
                blockX.append(arrayBand[labeled])
            X.append(blockX)
            Y.append(blockY)
        X = np.concatenate(X, axis=1).T
        Y = np.concatenate(Y, axis=1).T

        # skip samples that contain a no data value
        noDataValues = np.array([reader.noDataValue(bandNo) for bandNo in reader.bandNumbers()])
        valid = np.all(np.not_equal(X, noDataValues.T), axis=1)
        X = X[valid]
        Y = Y[valid]

        checkSampleShape(X, Y)
        return X, Y
