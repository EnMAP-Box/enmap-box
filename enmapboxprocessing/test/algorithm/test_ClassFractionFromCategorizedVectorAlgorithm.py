import numpy as np

from enmapbox.exampledata import enmap, landcover_polygon
from enmapboxprocessing.algorithm.classfractionfromcategorizedvectoralgorithm import \
    ClassFractionFromCategorizedVectorAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxtestdata import landcover_polygon_3classes_id
from qgis.core import QgsRasterLayer, QgsVectorLayer


class TestClassFractionFromCategorizedVectorAlgorithm(TestCase):

    def test_numberClassAttribute(self):
        alg = ClassFractionFromCategorizedVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: landcover_polygon_3classes_id,
            alg.P_GRID: enmap,
            alg.P_OUTPUT_FRACTION_RASTER: self.filename('fractions_polygons.tif')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_FRACTION_RASTER])
        self.assertListEqual(['roof', 'tree', 'water'], [reader.bandName(bandNo) for bandNo in reader.bandNumbers()])
        self.assertAlmostEqual(248.142, np.mean(reader.array()), 3)

    def test_stringClassAttribute(self):
        alg = ClassFractionFromCategorizedVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: QgsVectorLayer(landcover_polygon),
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_OUTPUT_FRACTION_RASTER: self.filename('fractions_polygons.tif')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_FRACTION_RASTER])
        self.assertListEqual(
            ['roof', 'pavement', 'low vegetation', 'tree', 'soil', 'water'],
            [reader.bandName(bandNo) for bandNo in reader.bandNumbers()]
        )
        self.assertAlmostEqual(247.589, np.mean(reader.array()), 3)

    def test_band(self):
        alg = ClassFractionFromCategorizedVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: QgsVectorLayer(landcover_polygon),
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_OUTPUT_FRACTION_RASTER: self.filename('fractions_polygons.tif')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_FRACTION_RASTER])
        self.assertListEqual(
            ['roof', 'pavement', 'low vegetation', 'tree', 'soil', 'water'],
            [reader.bandName(bandNo) for bandNo in reader.bandNumbers()]
        )
        self.assertAlmostEqual(247.589, np.mean(reader.array()), 3)
