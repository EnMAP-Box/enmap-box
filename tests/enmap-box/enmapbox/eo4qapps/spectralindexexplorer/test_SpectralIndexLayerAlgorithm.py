from qgis.core import QgsRasterLayer

from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap
from spectralindexexplorerapp.spectralindexlayeralgorithm import SpectralIndexLayerAlgorithm


class TestSpectralIndexLayerAlgorithm(TestCase):

    def test_asiFormulaToRasterCalcFormula_predefIndex(self):
        layer = QgsRasterLayer(enmap, 'R')
        expression = SpectralIndexLayerAlgorithm.asiFormulaToRasterCalcFormula('NDVI', layer, {'N': 71, 'R': 48})
        self.assertEqual('("R@71" - "R@48")/("R@71" + "R@48")', expression)

    def test_asiFormulaToRasterCalcFormula_constant(self):
        layer = QgsRasterLayer(enmap, 'R')
        expression = SpectralIndexLayerAlgorithm.asiFormulaToRasterCalcFormula('C1', layer, {'C1': 42})
        self.assertEqual('42', expression)

    def test_predefIndex(self):
        alg = SpectralIndexLayerAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_FORMULA: 'NDVI',
            alg.P_LAYER_NAME: 'MyLayerName'
        }
        result = self.runalg(alg, parameters)
        layer: QgsRasterLayer = result[alg.P_OUTPUT_RASTER]
        self.assertTrue(layer.isValid())

    def test_predefIndex_ARI(self):
        alg = SpectralIndexLayerAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_FORMULA: 'ARVI',
            alg.P_LAYER_NAME: 'MyLayerName'
        }
        result = self.runalg(alg, parameters)
        layer: QgsRasterLayer = result[alg.P_OUTPUT_RASTER]
        self.assertTrue(layer.isValid())

    def test_constant(self):
        alg = SpectralIndexLayerAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_FORMULA: 'C1 + R*0',
            alg.P_LAYER_NAME: 'MyLayerName',
            alg.P_BAND_MAPPING: ['C1', '42', 'R', '1']
        }
        result = self.runalg(alg, parameters)
        layer: QgsRasterLayer = result[alg.P_OUTPUT_RASTER]
        self.assertTrue(layer.isValid())
        array = RasterReader(layer, openWithGdal=False).array(boundingBox=layer.extent())[0]
        self.assertEqual(array[100, 100], 42)

    def test_r123_style(self):
        alg = SpectralIndexLayerAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_FORMULA: 'r833',
            alg.P_LAYER_NAME: 'MyLayerName',
        }
        result = self.runalg(alg, parameters)
        layer: QgsRasterLayer = result[alg.P_OUTPUT_RASTER]
        self.assertTrue(layer.isValid())

    def test_rAt_style(self):
        alg = SpectralIndexLayerAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_FORMULA: 'r@42',
            alg.P_LAYER_NAME: 'MyLayerName'
        }
        result = self.runalg(alg, parameters)
        layer: QgsRasterLayer = result[alg.P_OUTPUT_RASTER]
        self.assertTrue(layer.isValid())

    def _test_all_indices(self):  # for debugging only
        for name in SpectralIndexLayerAlgorithm.Indices:
            print(name)
            alg = SpectralIndexLayerAlgorithm()
            parameters = {
                alg.P_RASTER: enmap,
                alg.P_FORMULA: name,
                alg.P_BAND_MAPPING: [
                    'A', '1', 'T', '1', 'T1', '1', 'lambdaG', '1', 'lambdaN', '1', 'lambdaR', '1', 'lambdaS1', '1',
                    'PAR', '1'
                ],
                alg.P_LAYER_NAME: 'MyLayerName'
            }
            result = self.runalg(alg, parameters)
            layer: QgsRasterLayer = result[alg.P_OUTPUT_RASTER]
            self.assertTrue(layer.isValid())
