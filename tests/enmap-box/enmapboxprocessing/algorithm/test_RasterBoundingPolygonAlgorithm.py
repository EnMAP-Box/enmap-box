from enmapboxprocessing.algorithm.rasterboundingpolygonalgorithm import RasterBoundingPolygonAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import enmap_potsdam
from qgis.core import QgsVectorLayer


class TestRasterBoundingPolygonAlgorithm(TestCase):

    def test(self):
        alg = RasterBoundingPolygonAlgorithm()
        parameters = {
            alg.P_RASTER: enmap_potsdam,
            alg.P_OUTPUT_VECTOR: self.filename('polygon.gpkg')
        }
        self.runalg(alg, parameters)
        layer = QgsVectorLayer(parameters[alg.P_OUTPUT_VECTOR])
        for feature in layer.getFeatures():
            self.assertEqual(58455900, round(feature.geometry().area()))
