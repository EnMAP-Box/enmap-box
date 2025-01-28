from math import isnan

import numpy as np

from enmapboxprocessing.algorithm.classificationperformancesimplealgorithm import \
    ClassificationPerformanceSimpleAlgorithm, accuracyAssessment
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import landcover_map_l3
from qgis.core import QgsRasterLayer, QgsMapLayer, QgsProcessingException


class TestClassificationPerformanceSimpleAlgorithm(TestCase):

    def test_accuracyAssessment(self):
        confusionMatrix = [[50, 2, 3], [1, 45, 4], [2, 3, 40]]
        observed = list()
        predicted = list()
        classValues = [0, 1, 2]
        for p in classValues:
            for o in classValues:
                predicted.extend([p] * confusionMatrix[p][o])
                observed.extend([o] * confusionMatrix[p][o])

        classNames = ['Forest', 'Water', 'Urban']

        result = accuracyAssessment(np.array(observed), np.array(predicted), classNames, classValues)
        tol = 1e-4
        self.assertTrue(np.allclose([0.9090, 0.9000, 0.8889], result.usersAccuracy, tol, tol))
        self.assertTrue(np.allclose([0.9433, 0.9000, 0.8511], result.producersAccuracy, tol, tol))
        self.assertTrue(np.allclose([0.9259, 0.9000, 0.8695], result.f1, tol, tol))
        self.assertTrue(np.allclose([0.0388, 0.0424, 0.0469], result.usersAccuracySe, tol, tol))
        self.assertTrue(np.allclose([0.0317, 0.0424, 0.0519], result.producersAccuracySe, tol, tol))
        self.assertTrue(np.allclose([0.0253, 0.0299, 0.0352], result.f1Se, tol, tol))

    def test(self):
        categories = [
            Category(1, 'c1', '#000000'), Category(2, 'c2', '#000000'),
            Category(3, 'c3', '#000000')
        ]
        writer1 = self.rasterFromArray([[[1, 1, 1, 2, 2, 2, 3, 3, 3]]], 'observation.tif')
        writer1.close()
        raster1 = QgsRasterLayer(writer1.source())
        renderer = Utils().palettedRasterRendererFromCategories(raster1.dataProvider(), 1, categories)
        raster1.setRenderer(renderer.clone())
        raster1.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

        writer2 = self.rasterFromArray([[[1, 1, 3, 2, 2, 2, 3, 3, 1]]], 'prediction.tif')
        writer2.close()
        raster2 = QgsRasterLayer(writer2.source())
        renderer = Utils().palettedRasterRendererFromCategories(raster2.dataProvider(), 1, categories)
        raster2.setRenderer(renderer.clone())
        raster2.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: writer2.source(),
            alg.P_REFERENCE: writer1.source(),
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)

    def test_perfectMap(self):
        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: landcover_map_l3,
            alg.P_REFERENCE: landcover_map_l3,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_perfectMap.html'),
        }
        result = self.runalg(alg, parameters)
        stats = Utils.jsonLoad(result[alg.P_OUTPUT_REPORT] + '.json')
        for v in stats['producersAccuracySe'] + stats['usersAccuracySe']:
            self.assertFalse(isnan(v))  # previously we had NaN values, so better check this

    def test_nonMatchingCategoryNames(self):
        reader = RasterReader(landcover_map_l3)
        writer = Driver(self.filename('copy')).createFromArray(reader.array(), reader.extent(), reader.crs())
        writer.close()

        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: self.filename('copy'),
            alg.P_REFERENCE: landcover_map_l3,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        result = self.runalg(alg, parameters)

    def test_twoClass(self):
        Forest = 1
        Water = 2
        PredictedValues = [Forest, Forest, Forest, Forest, Forest, Forest, Water, Water, Water]
        TrueValues = [Forest, Forest, Forest, Forest, Forest, Forest, Water, Forest, Forest]

        categories = [Category(1, 'c1', '#000000'), Category(2, 'c2', '#000000')]
        writer1 = self.rasterFromArray([[TrueValues]], 'observation.tif')
        writer1.close()
        raster1 = QgsRasterLayer(writer1.source())
        renderer = Utils().palettedRasterRendererFromCategories(raster1.dataProvider(), 1, categories)
        raster1.setRenderer(renderer.clone())
        raster1.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

        writer2 = self.rasterFromArray([[PredictedValues]], 'prediction.tif')
        writer2.close()
        raster2 = QgsRasterLayer(writer2.source())
        renderer = Utils().palettedRasterRendererFromCategories(raster2.dataProvider(), 1, categories)
        raster2.setRenderer(renderer.clone())
        raster2.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: writer2.source(),
            alg.P_REFERENCE: writer1.source(),
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        result = self.runalg(alg, parameters)

        stats = Utils.jsonLoad(result[alg.P_OUTPUT_REPORT] + '.json')
        self.assertEqual(77, int(stats['overallAccuracy'] * 100))
        self.assertListEqual([100, 33], [int(v * 100) for v in stats['usersAccuracy']])
        self.assertListEqual([75, 100], [int(v * 100) for v in stats['producersAccuracy']])

    def test_issue1070(self):
        # handle unclassified data
        categories = [Category(1, 'c1', '#000000'), Category(2, 'c2', '#000000')]
        writer1 = self.rasterFromArray([[[1, 2]]], 'observation.tif')
        writer1.close()
        raster1 = QgsRasterLayer(writer1.source())
        renderer = Utils().palettedRasterRendererFromCategories(raster1.dataProvider(), 1, categories)
        raster1.setRenderer(renderer.clone())
        raster1.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

        writer2 = self.rasterFromArray([[[0, 2]]], 'prediction.tif')  # introduce unclassified data
        writer2.close()
        raster2 = QgsRasterLayer(writer2.source())
        renderer = Utils().palettedRasterRendererFromCategories(raster2.dataProvider(), 1, categories)
        raster2.setRenderer(renderer.clone())
        raster2.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: writer2.source(),
            alg.P_REFERENCE: writer1.source(),
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            assert str(error) == 'Predicted values not matching reference classes.'
