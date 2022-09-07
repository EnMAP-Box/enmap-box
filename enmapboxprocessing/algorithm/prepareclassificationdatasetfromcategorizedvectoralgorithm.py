from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedrasteralgorithm import \
    PrepareClassificationDatasetFromCategorizedRasterAlgorithm
from enmapboxprocessing.algorithm.rasterizecategorizedvectoralgorithm import RasterizeCategorizedVectorAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsProcessingParameterField,
                       QgsCategorizedSymbolRenderer, QgsProcessingException)
from typeguard import typechecked


@typechecked
class PrepareClassificationDatasetFromCategorizedVectorAlgorithm(EnMAPProcessingAlgorithm):
    P_CATEGORIZED_VECTOR, _CATEGORIZED_VECTOR = 'categorizedVector', 'Categorized vector layer'
    P_FEATURE_RASTER, _FEATURE_RASTER = 'featureRaster', 'Raster layer with features'
    P_CATEGORY_FIELD, _CATEGORY_FIELD = 'categoryField', 'Field with class values'
    P_COVERAGE, _COVERAGE = 'coverage', 'Minimum pixel coverage'
    P_MAJORITY_VOTING, _MAJORITY_VOTING = 'majorityVoting', 'Majority voting'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputClassificationDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create classification dataset (from categorized vector layer and feature raster)'

    def shortDescription(self) -> str:
        return 'Create a classification dataset by sampling data for pixels that match the given categories ' \
               'and store the result as a pickle file.\n' \
               'If the layer is not categorized, or the field with class values is selected manually, ' \
               'categories are derived from the sampled target data y. ' \
               'To be more precise: ' \
               'i) category values are derived from unique attribute values (after excluding no data or zero data values), ' \
               'ii) category names are set equal to the category values, ' \
               'and iii) category colors are picked randomly.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CATEGORIZED_VECTOR,
             'Categorized vector layer specifying sample locations and target data y. '
             'If required, the layer is reprojected and rasterized internally to match the feature raster grid.'),
            (self._FEATURE_RASTER, 'Raster layer used for sampling feature data X.'),
            (self._CATEGORY_FIELD, 'Field with class values used as target data y. '
                                   'If not selected, the field defined by the renderer is used. '
                                   'If that is also not specified, an error is raised.'),
            (self._COVERAGE, 'Exclude all pixel where (polygon) coverage is smaller than given threshold.'),
            (self._MAJORITY_VOTING, 'Whether to use majority voting. '
                                    'Turn off to use simple nearest neighbour resampling, which is much faster, '
                                    'but may result in highly inaccurate class decisions.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_CATEGORIZED_VECTOR, self._CATEGORIZED_VECTOR)
        self.addParameterRasterLayer(self.P_FEATURE_RASTER, self._FEATURE_RASTER)
        self.addParameterField(
            self.P_CATEGORY_FIELD, self._CATEGORY_FIELD, None, self.P_CATEGORIZED_VECTOR,
            QgsProcessingParameterField.Any, False, True, False, True
        )
        self.addParameterInt(self.P_COVERAGE, self._COVERAGE, 50, False, 0, 100, advanced=True)
        self.addParameterBoolean(self.P_MAJORITY_VOTING, self._MAJORITY_VOTING, True, False, True)
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        classification = self.parameterAsVectorLayer(parameters, self.P_CATEGORIZED_VECTOR, context)
        raster = self.parameterAsRasterLayer(parameters, self.P_FEATURE_RASTER, context)
        classField = self.parameterAsField(parameters, self.P_CATEGORY_FIELD, context)
        minCoverage = self.parameterAsInt(parameters, self.P_COVERAGE, context)
        majorityVoting = self.parameterAsBoolean(parameters, self.P_MAJORITY_VOTING, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # derive classification scheme
            renderer = classification.renderer()
            if classField is None:
                if isinstance(renderer, QgsCategorizedSymbolRenderer):
                    categories = Utils.categoriesFromCategorizedSymbolRenderer(renderer)
                    classField = renderer.classAttribute()
                    feedback.pushInfo(f'Use categories from style: {categories}')
                else:
                    message = 'Select either a categorited vector layer, or a field with class values.'
                    feedback.reportError(message, fatalError=True)
                    raise QgsProcessingException(message)
            else:
                categories = Utils.categoriesFromVectorField(classification, classField)
                feedback.pushInfo(f'Derive categories from selected field: {categories}')

            # set derived renderer
            classification = classification.clone()  # make a copy to not overwrite the current renderer
            renderer = Utils.categorizedSymbolRendererFromCategories(classField, categories)
            classification.setRenderer(renderer)

            feedback.pushInfo('Rasterize categorized vector layer')
            alg = RasterizeCategorizedVectorAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_CATEGORIZED_VECTOR: classification,
                alg.P_GRID: raster,
                alg.P_COVERAGE: minCoverage,
                alg.P_MAJORITY_VOTING: majorityVoting,
                alg.P_OUTPUT_CATEGORIZED_RASTER: Utils.tmpFilename(filename, 'classification.tif')
            }
            result = self.runAlg(alg, parameters, None, feedback2, context, True)
            classification = QgsRasterLayer(result[alg.P_OUTPUT_CATEGORIZED_RASTER])
            categories = Utils.categoriesFromPalettedRasterRenderer(classification.renderer())
            feedback.pushInfo('Sample data')
            X, y = PrepareClassificationDatasetFromCategorizedRasterAlgorithm.sampleData(
                raster, classification, 1, categories, feedback2
            )

            features = [RasterReader(raster).bandName(i + 1) for i in range(raster.bandCount())]
            feedback.pushInfo(f'Sampled data: X=array{list(X.shape)} y=array{list(y.shape)}')

            dump = ClassifierDump(categories=categories, features=features, X=X, y=y)
            dumpDict = dump.__dict__

            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result

    # @classmethod
    # def sampleData(
    #         cls, raster: QgsRasterLayer, classification: QgsRasterLayer, classBandNo: int, categories: Categories,
    #         feedback: QgsProcessingFeedback = None
    # ) -> Tuple[SampleX, SampleY]:
    #     assert raster.crs() == classification.crs()
    #     assert raster.extent() == classification.extent()
    #     assert (raster.width(), raster.height()) == (classification.width(), classification.height())
    #
    #     maximumMemoryUsage = gdal.GetCacheMax()
    #     rasterReader = RasterReader(raster)
    #     classificationReader = RasterReader(classification)
    #     lineMemoryUsage = rasterReader.lineMemoryUsage(1)
    #     lineMemoryUsage += classificationReader.width() * classificationReader.dataTypeSize()
    #     blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
    #     blockSizeX = raster.width()
    #
    #     X = list()
    #     y = list()
    #     for block in rasterReader.walkGrid(blockSizeX, blockSizeY, feedback):
    #         blockClassification = classificationReader.arrayFromBlock(block, [classBandNo])[0]
    #         labeled = np.full_like(blockClassification, False, bool)
    #         for c in categories:
    #             np.logical_or(labeled, blockClassification == c.value, out=labeled)
    #         blockY = blockClassification[labeled]
    #         blockX = list()
    #         for bandNo in range(1, rasterReader.bandCount() + 1):
    #             blockBand = rasterReader.arrayFromBlock(block, [bandNo])[0]
    #             blockX.append(blockBand[labeled])
    #         X.append(blockX)
    #         y.append(blockY)
    #     X = np.concatenate(X, axis=1).T
    #     y = np.expand_dims(np.concatenate(y), 1)
    #     checkSampleShape(X, y)
    #     return X, y
