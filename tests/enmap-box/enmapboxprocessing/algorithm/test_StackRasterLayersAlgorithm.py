from enmapbox.exampledata import enmap, hires
from enmapboxprocessing.algorithm.stackrasterlayersalgorithm import StackRasterLayersAlgorithm

from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.algorithm.testcase import TestCase


class TestSubsetRasterBandsAlgorithm(TestCase):

    def test_default(self):
        alg = StackRasterLayersAlgorithm()
        parameters = {
            alg.P_RASTERS: [hires, hires],
            alg.P_OUTPUT_RASTER: self.filename('stack.vrt')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertListEqual(
            ['Red (665 nanometers)', 'Green (560 nanometers)', 'Blue (490 nanometers)', 'Red (665 nanometers)',
             'Green (560 nanometers)', 'Blue (490 nanometers)'],
            [reader.bandName(bandNo) for bandNo in reader.bandNumbers()])

    def test_singleBand(self):
        alg = StackRasterLayersAlgorithm()
        parameters = {
            alg.P_RASTERS: [hires, hires],
            alg.P_BAND: 1,
            alg.P_OUTPUT_RASTER: self.filename('stack.vrt')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertListEqual(
            ['Red (665 nanometers)', 'Red (665 nanometers)'],
            [reader.bandName(bandNo) for bandNo in reader.bandNumbers()])

    def test_grid(self):
        alg = StackRasterLayersAlgorithm()
        parameters = {
            alg.P_RASTERS: [enmap, hires],
            alg.P_BAND: 1,
            alg.P_GRID: hires,
            alg.P_OUTPUT_RASTER: self.filename('stack.vrt')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(RasterReader(hires).extent(), reader.extent())
