from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.translatecategorizedrasteralgorithm import TranslateCategorizedRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import SampleX, SampleY, Categories, checkSampleShape, ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsPalettedRasterRenderer,
                       QgsMapLayer)


@typechecked
class PrepareClassificationDatasetFromCategorizedRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_CATEGORIZED_RASTER, _CATEGORIZED_RASTER = 'categorizedRaster', 'Categorized raster layer'
    P_FEATURE_RASTER, _FEATURE_RASTER = 'featureRaster', 'Raster layer with features'
    P_EXCLUDE_BAD_BANDS, _EXCLUDE_BAD_BANDS, = 'excludeBadBands', 'Exclude bad bands'
    P_CATEGORY_BAND, _CATEGORY_BAND = 'categoryBand', 'Band with class values'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputClassificationDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create classification dataset (from categorized raster layer and feature raster)'

    def shortDescription(self) -> str:
        return 'Create a classification dataset by sampling data for pixels that match the given categories ' \
               'and store the result as a pickle file. \n' \
               'If the layer is not categorized, or the band with class values is selected manually, ' \
               'categories are derived from sampled data itself. ' \
               'To be more precise: ' \
               'i) category values are derived from unique raster band values (after excluding no data or zero data pixel), ' \
               'ii) category names are set equal to the category values, ' \
               'and iii) category colors are picked randomly.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CATEGORIZED_RASTER,
             'Categorized raster layer specifying sample locations and target data y. '
             'If required, the layer is reprojected and resampled internally to match the feature raster grid.\n'),
            (self._FEATURE_RASTER, 'Raster layer used for sampling feature data X.'),
            (self._EXCLUDE_BAD_BANDS, 'Whether to exclude bands, that are marked as bad bands, '
                                      'or contain no data, inf or nan values in all samples.'),
            (self._CATEGORY_BAND, 'Band with class values. '
                                  'If not selected, the band defined by the renderer is used. '
                                  'If that is also not specified, the first band is used.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_CATEGORIZED_RASTER, self._CATEGORIZED_RASTER)
        self.addParameterRasterLayer(self.P_FEATURE_RASTER, self._FEATURE_RASTER)
        self.addParameterBoolean(self.P_EXCLUDE_BAD_BANDS, self._EXCLUDE_BAD_BANDS, True, True)
        self.addParameterBand(
            self.P_CATEGORY_BAND, self._CATEGORY_BAND, None, self.P_CATEGORIZED_RASTER, True, False, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        classification = self.parameterAsRasterLayer(parameters, self.P_CATEGORIZED_RASTER, context)
        raster = self.parameterAsRasterLayer(parameters, self.P_FEATURE_RASTER, context)
        classBandIndex = self.parameterAsInt(parameters, self.P_CATEGORY_BAND, context)
        excludeBadBands = self.parameterAsBoolean(parameters, self.P_EXCLUDE_BAD_BANDS, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # derive classification scheme
            renderer = classification.renderer()
            if classBandIndex is None:
                if isinstance(renderer, QgsPalettedRasterRenderer):
                    categories = Utils.categoriesFromPalettedRasterRenderer(renderer)
                    feedback.pushInfo(f'Use categories from style: {categories}')
                    classBandNo = renderer.band()
                else:
                    classBandNo = renderer.usesBands()[0]
                    categories = Utils.categoriesFromRasterBand(classification, classBandNo)
                    feedback.pushInfo(f'Derive categories from first renderer band: {categories}')
            else:
                classBandNo = classBandIndex + 1
                categories = Utils.categoriesFromRasterBand(classification, classBandNo)
                feedback.pushInfo(f'Derive categories from selected band: {categories}')

            # set renderer
            renderer = Utils.palettedRasterRendererFromCategories(
                classification.dataProvider(), classBandNo, categories
            )
            classification = classification.clone()  # do not alter input renderer
            classification.setRenderer(renderer)

            # resample classification and set renderer
            alg = TranslateCategorizedRasterAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_CATEGORIZED_RASTER: classification,
                alg.P_GRID: raster,
                alg.P_OUTPUT_CATEGORIZED_RASTER: Utils.tmpFilename(filename, 'classification.tif')
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)
            classification = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])
            renderer = Utils.palettedRasterRendererFromCategories(classification.dataProvider(), 1, categories)
            classification.setRenderer(renderer)
            classification.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            X, y, goodBandNumbers, locations = self.sampleData(
                raster, classification, classBandNo, categories, excludeBadBands, feedback
            )
            reader = RasterReader(raster)
            features = [reader.bandName(bandNo) for bandNo in goodBandNumbers]
            feedback.pushInfo(f'Sampled data: X=array{list(X.shape)} y=array{list(y.shape)}')

            dump = ClassifierDump(
                categories=categories, features=features, X=X, y=y, locations=locations,
                crs=classification.crs().toWkt()
            )
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result

    @classmethod
    def sampleData(
            cls, raster: QgsRasterLayer, classification: QgsRasterLayer, classBandNo: int, categories: Categories,
            excludeBadBands: bool, feedback: QgsProcessingFeedback = None
    ) -> Tuple[SampleX, SampleY, List[int], np.ndarray]:
        # assert raster.crs() == classification.crs()
        assert raster.extent() == classification.extent()
        assert (raster.width(), raster.height()) == (classification.width(), classification.height())

        maximumMemoryUsage = Utils.maximumMemoryUsage()
        reader = RasterReader(raster)
        classificationReader = RasterReader(classification)
        lineMemoryUsage = reader.lineMemoryUsage(1)
        lineMemoryUsage += classificationReader.width() * classificationReader.dataTypeSize()
        blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
        blockSizeX = raster.width()

        X = list()
        y = list()
        locations = list()
        XMask = list()
        for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
            blockClassification = classificationReader.arrayFromBlock(block, [classBandNo])[0]
            labeled = np.full_like(blockClassification, False, bool)
            for c in categories:
                np.logical_or(labeled, blockClassification == c.value, out=labeled)
            blockY = blockClassification[labeled]
            blockX = list()
            blockXMask = list()
            for bandNo in range(1, reader.bandCount() + 1):
                blockBand = reader.arrayFromBlock(block, [bandNo])
                blockBandMask = reader.maskArray(blockBand, [bandNo])
                blockX.append(blockBand[0][labeled])
                blockXMask.append(blockBandMask[0][labeled])
            blockLocation = np.array([block.xMap()[labeled], block.yMap()[labeled]]).T
            X.append(blockX)
            y.append(blockY)
            locations.append(blockLocation)
            XMask.append(blockXMask)
        X = np.concatenate(X, axis=1).T
        XMask = np.concatenate(XMask, axis=1).T
        y = np.expand_dims(np.concatenate(y), 1)
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
        valid2 = np.all(np.isfinite(X), axis=1)  # resolves issue #495
        valid = np.logical_and(valid1, valid2)
        X = X[valid]
        y = y[valid]
        locations = locations[valid]
        checkSampleShape(X, y)
        return X, y, goodBandNumbers, locations
