from os.path import exists

from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.algorithm.tileenmapl2aalgorithm import TileEnmapL2AAlgorithm


class TestTileEnmapL2AAlgorithm(TestCase):
    xmlFilename1 = r'D:\data\EnFireMap\data\nc_230302_01\ENMAP01-____L2A-DT0000009825_20230302T192610Z_001_V010111_20230303T231444Z-METADATA.XML'
    xmlFilename2 = r'D:\data\EnFireMap\data\nc_230302_02\ENMAP01-____L2A-DT0000009825_20230302T192615Z_002_V010111_20230303T231444Z-METADATA.XML'
    tilingScheme = r'D:\data\EnFireMap\cube\shp\grid_california.gpkg'
    dataAvailable = exists(xmlFilename1)

    def test(self):

        if not self.dataAvailable:
            return

        alg = TileEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: self.xmlFilename1,
            alg.P_TILING_SCHEME: self.tilingScheme,
            alg.P_TILE_NAMES: 'Tile_ID',
            alg.P_RESOLUTION: 300,
            alg.P_OUTPUT_FOLDER: self.filename('cube')
        }
        self.runalg(alg, parameters)

    def test2(self):

        if not self.dataAvailable:
            return

        alg = TileEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: self.xmlFilename1,
            alg.P_TILING_SCHEME: self.tilingScheme,
            alg.P_TILE_NAMES: 'Tile_ID',
            alg.P_RESOLUTION: 300,
            alg.P_OUTPUT_FOLDER: self.filename('cube')
        }
        self.runalg(alg, parameters)

        alg = TileEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: self.xmlFilename2,
            alg.P_TILING_SCHEME: self.tilingScheme,
            alg.P_TILE_NAMES: 'Tile_ID',
            alg.P_RESOLUTION: 300,
            alg.P_OUTPUT_FOLDER: self.filename('cube')
        }
        self.runalg(alg, parameters)
