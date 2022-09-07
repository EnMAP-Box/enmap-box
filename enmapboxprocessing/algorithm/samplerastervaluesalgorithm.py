from typing import Dict, Any, List, Tuple

import processing
from enmapboxprocessing.algorithm.creategridalgorithm import CreateGridAlgorithm
from enmapboxprocessing.algorithm.rasterizevectoralgorithm import RasterizeVectorAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group, AlgorithmCanceledException
from enmapboxprocessing.processingfeedback import ProcessingFeedback
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsVectorLayer, QgsRasterLayer,
                       QgsFeature, QgsField, QgsProcessingFeatureSourceDefinition, QgsApplication,
                       QgsVectorDataProvider, QgsRasterDataProvider, QgsPoint)
from qgis.core.additions.edit import edit
from typeguard import typechecked


@typechecked
class SampleRasterValuesAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_VECTOR, _VECTOR = 'vector', 'Vector layer'
    P_COVERAGE_RANGE, _COVERAGE_RANGE = 'coverageRange', 'Pixel coverage (%)'
    P_OUTPUT_POINTS, _OUTPUT_POINTS = 'outputPointsData', 'Output point layer'

    def displayName(self) -> str:
        return 'Sample raster layer values'

    def shortDescription(self) -> str:
        return 'Creates a new point layer with the same attributes of the input layer and the ' \
               'raster values corresponding to the pixels covered by polygons or point location. ' \
               '\nThe resulting point vector contains ' \
               '1) all input attributes from the Locations vector,  ' \
               '2) attributes SAMPLE_{i}, one for each input raster band, ' \
               '3) two attributes PIXEL_X, PIXEL_Y for storing the raster pixel locations (zero-based),' \
               'and 4), in case of polygon locations, an attribute COVER for storing the pixel coverage (%).\n' \
               'Note that we assume non-overlapping feature geometries! ' \
               'In case of overlapping geometries, split the Locations layer into non-overlapping subsets, ' \
               'perform the sampling for each subset individually, and finally concatenate the results.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A raster layer to sample data from.'),
            (self._VECTOR, 'A vector layer defining the locations to sample.'),
            (self._COVERAGE_RANGE, 'Samples with polygon pixel coverage outside the given range are excluded. '
                                   'This parameter has no effect in case of point locations.'),
            (self._OUTPUT_POINTS, self.VectorFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.RasterAnalysis.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterVectorLayer(self.P_VECTOR, self._VECTOR)
        self.addParameterIntRange(self.P_COVERAGE_RANGE, self._COVERAGE_RANGE, [50, 100], True, True)
        self.addParameterVectorDestination(self.P_OUTPUT_POINTS, self._OUTPUT_POINTS)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        vector = self.parameterAsVectorLayer(parameters, self.P_VECTOR, context)
        coverageMin, coverageMax = self.parameterAsRange(parameters, self.P_COVERAGE_RANGE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_POINTS, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)
            selectedFeaturesOnly = False
            if Utils.isPointGeometry(vector.geometryType()):
                self.samplePoints(filename, raster, vector, selectedFeaturesOnly, feedback, feedback2, context)
            else:
                self.samplePolygons(
                    filename, raster, vector, selectedFeaturesOnly, coverageMin, coverageMax, feedback, feedback2,
                    context
                )
            result = {self.P_OUTPUT_POINTS: filename}
            self.toc(feedback, result)

        return result

    @classmethod
    def samplePoints(
            cls, filename: str, raster: QgsRasterLayer, vector: QgsVectorLayer, selectedFeaturesOnly: bool,
            feedback: QgsProcessingFeedback, feedback2: QgsProcessingFeedback, context: QgsProcessingContext
    ):
        assert Utils.isPointGeometry(vector.geometryType())
        alg = 'qgis:rastersampling'
        parameters = {
            'COLUMN_PREFIX': 'SAMPLE_',
            'INPUT': QgsProcessingFeatureSourceDefinition(vector.source(), selectedFeaturesOnly),
            'OUTPUT': filename,
            'RASTERCOPY': raster
        }
        processing.run(alg, parameters, None, feedback2, context, True)
        sample = QgsVectorLayer(filename)

        # add image X, Y coordinates
        rasterProvider = raster.dataProvider()
        vectorProvider: QgsVectorDataProvider = sample.dataProvider()
        fields = [QgsField('PIXEL_X', QVariant.LongLong), QgsField('PIXEL_Y', QVariant.LongLong)]
        vectorProvider.addAttributes(fields)
        sample.updateFields()
        with edit(sample):
            feature: QgsFeature
            for feature in sample.getFeatures():
                point = QgsPoint(feature.geometry().asPoint())
                assert isinstance(point, QgsPoint)
                imagePoint: QgsPoint = rasterProvider.transformCoordinates(
                    point, QgsRasterDataProvider.TransformLayerToImage
                )
                feature.setAttribute('PIXEL_X', imagePoint.x())
                feature.setAttribute('PIXEL_Y', imagePoint.y())
                sample.updateFeature(feature)

        return sample

    @classmethod
    def samplePolygons(
            cls, filename: str, raster: QgsRasterLayer, vector: QgsVectorLayer, selectedFeaturesOnly: bool,
            coverageMin: int, coverageMax: int,
            feedback: ProcessingFeedback, feedback2: ProcessingFeedback, context: QgsProcessingContext
    ):
        assert Utils.isPolygonGeometry(vector.geometryType())

        # create oversampling grid
        alg = CreateGridAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CRS: raster.crs(),
            alg.P_EXTENT: raster.extent(),
            alg.P_UNIT: alg.PixelUnits,
            alg.P_WIDTH: raster.width() * 10,
            alg.P_HEIGHT: raster.height() * 10,
            alg.P_OUTPUT_GRID: Utils.tmpFilename(filename, 'grid.x10.vrt')
        }
        result = processing.run(alg, parameters, None, feedback2, context, True)
        x10Grid = QgsRasterLayer(result[alg.P_OUTPUT_GRID])

        if feedback.isCanceled():
            raise AlgorithmCanceledException()

        feedback.pushInfo('Rasterize polygon IDs at x10 finer resolution')
        alg = RasterizeVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_VECTOR: vector,
            alg.P_GRID: x10Grid,
            alg.P_BURN_FID: True,
            alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'fid.x10.tif'),
        }
        result = processing.run(alg, parameters, None, feedback2, context, True)
        x10FidArray = RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0]

        sampleVectors = list()
        polygonFeature: QgsFeature
        refs = list()  # don't loose your C refs!
        n = vector.featureCount()
        for i, polygonFeature in enumerate(vector.getFeatures()):

            if feedback.isCanceled():
                raise AlgorithmCanceledException()

            feedback.pushInfo(f'Sample polygon [{i + 1}/{n}]')

            fid = polygonFeature.id()
            # calculate coverage
            x10MaskArray = x10FidArray == fid
            percentArray = x10MaskArray.reshape((raster.height(), 10, raster.width(), 10)).sum(axis=3).sum(axis=1)
            # mask coverage outside valid range
            if coverageMin != 0:
                percentArray[percentArray < coverageMin] = 0
            if coverageMax != 100:
                percentArray[percentArray > coverageMax] = 0

            driver = Driver(Utils.tmpFilename(filename, f'cover{fid}.tif'), feedback=feedback2)
            coverRaster = driver.createFromArray([percentArray], raster.extent(), raster.crs())
            coverRaster.setNoDataValue(0)
            coverRaster.close()

            if feedback.isCanceled():
                raise AlgorithmCanceledException()

            # create sample locations with cover > 0%
            alg = QgsApplication.processingRegistry().createAlgorithmById('native:pixelstopoints')
            parameters = {
                'FIELD_NAME': 'COVER',
                'INPUT_RASTER': coverRaster.source(),
                'OUTPUT': Utils.tmpFilename(filename, f'locations{fid}.gpkg'),
                'RASTER_BAND': 1
            }
            result = processing.run(alg, parameters, None, feedback2, context, True)
            locationVector = QgsVectorLayer(result['OUTPUT'])
            refs.append(locationVector)
            nFields = locationVector.fields().count()

            if feedback.isCanceled():
                raise AlgorithmCanceledException()

            # add polygon attributes to each point (extremly redundant, but we want all data in one table)
            provider: QgsVectorDataProvider = locationVector.dataProvider()
            fields = [QgsField(field) for field in vector.fields()
                      if field.name() not in ['fid', 'temp_fid']]
            refs.append(fields)
            provider.addAttributes(fields)
            locationVector.updateFields()

            polygonFeatureAttributes = [value for field, value in zip(vector.fields(), polygonFeature.attributes())
                                        if field.name() not in ['fid', 'temp_fid']]
            with edit(locationVector):
                pointFeature: QgsFeature
                for pointFeature in locationVector.getFeatures():
                    values = [pointFeature.attribute(i) for i in range(nFields)] + polygonFeatureAttributes
                    pointFeature.setAttributes(values)
                    locationVector.updateFeature(pointFeature)

            if feedback.isCanceled():
                raise AlgorithmCanceledException()

            sampleVector = cls.samplePoints(
                Utils.tmpFilename(filename, f'sample{fid}.gpkg'), raster, locationVector, selectedFeaturesOnly,
                feedback, feedback2, context
            )
            sampleVectors.append(sampleVector)

        if feedback.isCanceled():
            raise AlgorithmCanceledException()

        # merge all samples
        alg = QgsApplication.processingRegistry().createAlgorithmById('native:mergevectorlayers')
        parameters = {
            'LAYERS': sampleVectors,
            'CRS': vector.crs(),
            'OUTPUT': filename
        }
        processing.run(alg, parameters, None, feedback, context, True)
