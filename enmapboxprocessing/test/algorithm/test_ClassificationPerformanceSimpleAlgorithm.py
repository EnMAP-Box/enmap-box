from math import isnan

import numpy as np

from enmapbox.exampledata import landcover_polygon, enmap
from enmapboxprocessing.algorithm.classificationperformancesimplealgorithm import \
    ClassificationPerformanceSimpleAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import landcover_map_l3
from qgis.core import QgsProcessingException, QgsRasterLayer

writeToDisk = True


class TestClassificationPerformanceSimpleAlgorithm(TestCase):

    def test(self):
        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: landcover_map_l3,
            alg.P_REFERENCE: landcover_polygon,
            alg.P_OPEN_REPORT: True,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)

    def test_perfectMap(self):
        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: landcover_map_l3,
            alg.P_REFERENCE: landcover_map_l3,
            alg.P_OPEN_REPORT: False,
            alg.P_OUTPUT_REPORT: self.filename('report_perfectMap.html'),
        }
        result = self.runalg(alg, parameters)
        stats = Utils.jsonLoad(result[alg.P_OUTPUT_REPORT] + '.json')
        for v in stats['producers_accuracy_se'] + stats['users_accuracy_se']:
            self.assertFalse(isnan(v))  # previously we had NaN values, so better check this

    def test_error_messages(self):
        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: enmap,
            alg.P_REFERENCE: landcover_map_l3,
            alg.P_OPEN_REPORT: False,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual(
                str(error),
                'Unable to execute algorithm\nInvalid categorized raster layer, requires paletted/unique values renderer (Predicted classification layer)'
            )
        parameters = {
            alg.P_CLASSIFICATION: landcover_map_l3,
            alg.P_REFERENCE: enmap,
            alg.P_OPEN_REPORT: False,
            alg.P_OUTPUT_REPORT: self.filename('report2.html'),
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual(
                str(error),
                'Unable to execute algorithm\nInvalid categorized raster layer, requires paletted/unique values renderer (Observed categorized layer)'
            )

    def test_debug(self):
        alg = ClassificationPerformanceSimpleAlgorithm()

        categories = [Category(1, 'A', '#ff0000'), Category(2, 'B', '#ff0000'), Category(3, 'C', '#ff0000')]
        Driver(self.filename('observed.tif')).createFromArray(np.array([[[1, 2, 3]]]))
        Driver(self.filename('predicted.tif')).createFromArray(np.array([[[1, 1, 1]]]))

        predicted = QgsRasterLayer(self.filename('predicted.tif'))
        observed = QgsRasterLayer(self.filename('observed.tif'))

        renderer = Utils.palettedRasterRendererFromCategories(predicted.dataProvider(), 1, categories)
        predicted.setRenderer(renderer)

        renderer = Utils.palettedRasterRendererFromCategories(observed.dataProvider(), 1, categories)
        observed.setRenderer(renderer)

        parameters = {
            alg.P_CLASSIFICATION: predicted,
            alg.P_REFERENCE: observed,
            alg.P_OPEN_REPORT: True,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)

    def _test_debug(self):
        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: r'C:\Users\Andreas\Downloads\accass\2015-2020 Reclassification',
            alg.P_REFERENCE: r'C:\Users\Andreas\Downloads\accass\2015-2020 reclassified Validierung.shp',
            alg.P_OPEN_REPORT: True,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)
