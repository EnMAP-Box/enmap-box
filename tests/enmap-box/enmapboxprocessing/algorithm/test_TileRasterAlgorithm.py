from os.path import exists

from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.algorithm.tilerasteralgorithm import TileRasterAlgorithm


class TestTileRasterAlgorithm(TestCase):
    rasterSpectral1 = r'D:\data\EnFireMap\data\nc_230302_01\ENMAP01-____L2A-DT0000009825_20230302T192610Z_001_V010111_20230303T231444Z-SPECTRAL_IMAGE.TIF'
    rasterSpectral2 = r'D:\data\EnFireMap\data\nc_230302_02\ENMAP01-____L2A-DT0000009825_20230302T192615Z_002_V010111_20230303T231444Z-SPECTRAL_IMAGE.TIF'
    rasterCloud1 = r'D:\data\EnFireMap\data\nc_230302_01\ENMAP01-____L2A-DT0000009825_20230302T192610Z_001_V010111_20230303T231444Z-QL_QUALITY_CLOUD.TIF'
    rasterCloud2 = r'D:\data\EnFireMap\data\nc_230302_02\ENMAP01-____L2A-DT0000009825_20230302T192615Z_002_V010111_20230303T231444Z-QL_QUALITY_CLOUD.TIF'
    tilingScheme = r'D:\data\EnFireMap\cube\shp\grid_california.gpkg'
    dataAvailable = exists(rasterSpectral1)

    def test(self):

        if not self.dataAvailable:
            return

        alg = TileRasterAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: self.rasterSpectral1,
            alg.P_TILING_SCHEME: self.tilingScheme,
            alg.P_TILE_NAMES: 'Tile_ID',
            alg.P_RESOLUTION: 300,
            alg.P_OUTPUT_BASENAME: 'test',
            alg.P_OUTPUT_FOLDER: self.filename('cube3')
        }
        self.runalg(alg, parameters)

    def test_noDataValue(self):

        if not self.dataAvailable:
            return

        alg = TileRasterAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: self.rasterCloud1,
            alg.P_NO_DATA_VALUE: 0,
            alg.P_TILING_SCHEME: self.tilingScheme,
            alg.P_TILE_NAMES: 'Tile_ID',
            alg.P_OUTPUT_FOLDER: self.filename('cube')
        }
        self.runalg(alg, parameters)

    def test_mosaicking(self):

        if not self.dataAvailable:
            return

        alg = TileRasterAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: self.rasterCloud1,
            alg.P_TILING_SCHEME: self.tilingScheme,
            alg.P_TILE_NAMES: 'Tile_ID',
            alg.P_NO_DATA_VALUE: 0,
            alg.P_OUTPUT_BASENAME: 'raster',
            alg.P_OUTPUT_FOLDER: self.filename('cube')
        }
        self.runalg(alg, parameters)

        alg = TileRasterAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: self.rasterCloud2,
            alg.P_TILING_SCHEME: self.tilingScheme,
            alg.P_TILE_NAMES: 'Tile_ID',
            alg.P_NO_DATA_VALUE: 0,
            alg.P_OUTPUT_BASENAME: 'raster',
            alg.P_OUTPUT_FOLDER: self.filename('cube')
        }
        self.runalg(alg, parameters)
