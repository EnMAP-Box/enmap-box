from enmapboxprocessing.algorithm.importplanetscopealgorithm import ImportPlanetScopeAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import SensorProducts, sensorProductsRoot


class TestImportPlanetScopeAlgorithm(TestCase):

    def test_L1B(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportPlanetScopeAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Planet.L1B,
            alg.P_OUTPUT_RASTER_SR: self.filename('planetL1B_SR.vrt'),
            alg.P_OUTPUT_RASTER_QA: self.filename('planetL1B_QA.vrt')
        }

        self.runalg(alg, parameters)
        self.assertEqual(31, RasterReader(parameters[alg.P_OUTPUT_RASTER_SR]).checksum(None, 5000, 5000, 1, 1))
        self.assertEqual(4, RasterReader(parameters[alg.P_OUTPUT_RASTER_QA]).checksum(None, 5000, 5000, 1, 1))

    def test_L3A(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportPlanetScopeAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Planet.L3A,
            alg.P_OUTPUT_RASTER_SR: self.filename('planetL3A_SR.vrt'),
            alg.P_OUTPUT_RASTER_QA: self.filename('planetL3A_QA.vrt')
        }

        self.runalg(alg, parameters)
        self.assertEqual(22, RasterReader(parameters[alg.P_OUTPUT_RASTER_SR]).checksum(None, 5000, 5000, 1, 1))
        self.assertEqual(3, RasterReader(parameters[alg.P_OUTPUT_RASTER_QA]).checksum(None, 5000, 5000, 1, 1))

    def test_L3B(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportPlanetScopeAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Planet.L3B,
            alg.P_OUTPUT_RASTER_SR: self.filename('planetL3B_SR.vrt'),
            alg.P_OUTPUT_RASTER_QA: self.filename('planetL3B_QA.vrt')
        }
        self.runalg(alg, parameters)
        self.assertEqual(18, RasterReader(parameters[alg.P_OUTPUT_RASTER_SR]).checksum(None, 5000, 5000, 1, 1))
        self.assertEqual(1, RasterReader(parameters[alg.P_OUTPUT_RASTER_QA]).checksum(None, 5000, 5000, 1, 1))

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportPlanetScopeAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Planet.L3B,
            alg.P_OUTPUT_RASTER_SR: self.filename('planetL3B_SR.tif'),
            alg.P_OUTPUT_RASTER_QA: self.filename('planetL3B_QA.tif')
        }
        self.runalg(alg, parameters)
