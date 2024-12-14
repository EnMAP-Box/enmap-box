import subprocess
import os
import unittest

from enmapboxprocessing.algorithm.rasterboundingpolygonalgorithm import RasterBoundingPolygonAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import enmap_potsdam
from qgis.core import QgsVectorLayer

# see https://github.com/conda-forge/qgis-feedstock/issues/487
SKIP_POLYGONIZE_TEST = False
if os.name == 'nt':
    try:
        process = subprocess.run(['where', 'gdal_polygonize'],
                                 check=True,
                                 shell=True,
                                 text=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        output = str(process.stdout)
        SKIP_POLYGONIZE_TEST = 'gdal_polygonize.bat' not in output
    except subprocess.CalledProcessError as ex:
        pass


class TestRasterBoundingPolygonAlgorithm(TestCase):

    @unittest.skipIf(SKIP_POLYGONIZE_TEST,
                     'Skipped because https://github.com/conda-forge/qgis-feedstock/issues/487')
    def test_RasterBoundingPolygonAlgorithm(self):
        alg = RasterBoundingPolygonAlgorithm()
        parameters = {
            alg.P_RASTER: enmap_potsdam,
            alg.P_BAND: 1,
            alg.P_OUTPUT_VECTOR: self.filename('polygon.gpkg')
        }
        self.runalg(alg, parameters)
        layer = QgsVectorLayer(parameters[alg.P_OUTPUT_VECTOR])
        for feature in layer.getFeatures():
            self.assertEqual(58455900, round(feature.geometry().area()))
