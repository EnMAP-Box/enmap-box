from enmapbox.exampledata import enmap, landcover_polygons
from enmapboxprocessing.algorithm.samplerastervaluesalgorithm import SampleRasterValuesAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from qgis.core import (QgsRasterLayer, QgsVectorLayer)
from testdata import landcover_points_singlepart_epsg3035, enmap_uncompressed


class TestSampleRasterValuesAlgorithm(TestCase):

    def test_sampleFromVectorPoints(self):
        global c
        alg = SampleRasterValuesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_VECTOR: landcover_points_singlepart_epsg3035,
            alg.P_OUTPUT_POINTS: self.filename('sample_vectorPoint.gpkg')
        }
        result = self.runalg(alg, parameters)

    def test_sampleFromVectorPolygons(self):
        global c
        alg = SampleRasterValuesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(enmap_uncompressed),
            alg.P_VECTOR: QgsVectorLayer(landcover_polygons),
            alg.P_OUTPUT_POINTS: self.filename('sample_vectorPolygons.gpkg')

        }
        result = self.runalg(alg, parameters)

    def test_coverageRange(self):
        alg = SampleRasterValuesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap_uncompressed,
            alg.P_VECTOR: landcover_polygons,
            alg.P_COVERAGE_RANGE: [70, 100],
            alg.P_OUTPUT_POINTS: self.filename('sample_70p_pure.gpkg')

        }
        result = self.runalg(alg, parameters)
        points = QgsVectorLayer(result[alg.P_OUTPUT_POINTS])
        self.assertEqual(404, points.featureCount())
        self.assertListEqual(
            ['fid', 'COVER', 'level_1_id', 'level_1', 'level_2_id', 'level_2', 'level_3_id', 'level_3'],
            points.fields().names()[:8]
        )
