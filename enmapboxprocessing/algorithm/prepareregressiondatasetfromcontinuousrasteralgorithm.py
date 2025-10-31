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
from enmapbox.typeguard import typechecked


@typechecked
class PrepareRegressionDatasetFromContinuousRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_CONTINUOUS_RASTER, _CONTINUOUS_RASTER = 'continuousRaster', 'Continuous-valued raster layer'
    P_FEATURE_RASTER, _FEATURE_RASTER = 'featureRaster', 'Raster layer with features'
    P_TARGETS, _TARGETS = 'targets', 'Targets'
    P_EXCLUDE_BAD_BANDS, _EXCLUDE_BAD_BANDS, = 'excludeBadBands', 'Exclude bad bands'
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
            (self._EXCLUDE_BAD_BANDS, 'Whether to exclude bands, that are marked as bad bands, '
                                      'or contain no data, inf or nan values in all samples.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_CONTINUOUS_RASTER, self._CONTINUOUS_RASTER)
        self.addParameterRasterLayer(self.P_FEATURE_RASTER, self._FEATURE_RASTER)
        self.addParameterBandList(
            self.P_TARGETS, self._TARGETS, None, self.P_CONTINUOUS_RASTER, True, True
        )
        self.addParameterBoolean(self.P_EXCLUDE_BAD_BANDS, self._EXCLUDE_BAD_BANDS, True, True)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        regression = self.parameterAsRasterLayer(parameters, self.P_CONTINUOUS_RASTER, context)
        raster = self.parameterAsRasterLayer(parameters, self.P_FEATURE_RASTER, context)
        targets = self.parameterAsInts(parameters, self.P_TARGETS, context)
        excludeBadBands = self.parameterAsBoolean(parameters, self.P_EXCLUDE_BAD_BANDS, context)
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

            X, y, goodBandNumbers, locations = self.sampleData(raster, regression, excludeBadBands, feedback2)
            reader = RasterReader(regression)
            targets = list()
            for i in range(regression.bandCount()):
                color = reader.bandColor(i + 1)
                if color is None:
                    hexcolor = None
                else:
                    hexcolor = color.name()
                targets.append(Target(reader.bandName(i + 1), hexcolor))
            reader = RasterReader(raster)
            features = [reader.bandName(bandNo) for bandNo in goodBandNumbers]
            feedback.pushInfo(f'Sampled data: X=array{list(X.shape)} y=array{list(y.shape)}')

            dump = RegressorDump(
                targets=targets, features=features, X=X, y=y, locations=locations, crs=regression.crs().toWkt()
            )
            dump.write(filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result

    @classmethod
    def sampleData(
            cls, raster: QgsRasterLayer, regression: QgsRasterLayer, excludeBadBands: bool,
            feedback: QgsProcessingFeedback = None
    ) -> Tuple[SampleX, SampleY, List[int], np.ndarray]:
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
        locations = list()
        XMask = list()
        for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
            arrayRegression = regressionReader.arrayFromBlock(block)
            labeled = np.all(regressionReader.maskArray(arrayRegression), axis=0)
            blockY = list()
            for a in arrayRegression:
                blockY.append(a[labeled])
            blockX = list()
            blockXMask = list()
            for bandNo in range(1, reader.bandCount() + 1):
                blockBand = reader.arrayFromBlock(block, [bandNo])
                blockBandMask = reader.maskArray(blockBand, [bandNo])
                blockX.append(blockBand[0][labeled])
                blockXMask.append(blockBandMask[0][labeled])
            blockLocation = np.array([block.xMap()[labeled], block.yMap()[labeled]]).T
            X.append(blockX)
            Y.append(blockY)
            locations.append(blockLocation)
            XMask.append(blockXMask)
        X = np.concatenate(X, axis=1).T
        XMask = np.concatenate(XMask, axis=1).T
        Y = np.concatenate(Y, axis=1).T
        locations = np.concatenate(locations, axis=1)

        # skip bad bands (see issue #560)
        if excludeBadBands:
            goodBands = np.any(XMask, 0)
            goodBandNumbers = list(map(int, np.where(goodBands)[0] + 1))
            badBandNumbers = list(map(str, np.where(~goodBands)[0] + 1))
            if len(badBandNumbers) > 0:
                feedback.pushInfo(f'Removed bad bands: {", ".join(badBandNumbers)}')
            X = X[:, goodBands]
        else:
            goodBandNumbers = list(reader.bandNumbers())

        # skip samples that contain a no data value
        noDataValues = np.array([reader.noDataValue(bandNo) for bandNo in goodBandNumbers])
        valid1 = np.all(np.not_equal(X, noDataValues.T), axis=1)
        valid2 = np.all(np.isfinite(X), axis=1)
        valid = np.logical_and(valid1, valid2)
        X = X[valid]
        Y = Y[valid]
        locations = locations[valid]
        checkSampleShape(X, Y)
        return X, Y, goodBandNumbers, locations
