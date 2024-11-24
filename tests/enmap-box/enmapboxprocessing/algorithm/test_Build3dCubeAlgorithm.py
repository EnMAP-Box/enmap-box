from enmapboxprocessing.algorithm.build3dcubealgorithm import Build3dCubeAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import enmap


class TestBuild3dCubeAlgorithm(TestCase):

    def test_lower_right(self):
        alg = Build3dCubeAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DX: 1,
            alg.P_DY: 1,
            alg.P_OUTPUT_FACE: self.filename('3dCubeFace.vrt'),
            alg.P_OUTPUT_SIDE: self.filename('3dCubeSide.tif')
        }
        self.runalg(alg, parameters)

    def test_lower_left(self):  # ENVI Classic Style
        alg = Build3dCubeAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DX: -1,
            alg.P_DY: 1,
            alg.P_OUTPUT_FACE: self.filename('3dCubeFace.vrt'),
            alg.P_OUTPUT_SIDE: self.filename('3dCubeSide.tif')
        }
        self.runalg(alg, parameters)

    def test_upper_right(self):
        alg = Build3dCubeAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DX: 1,
            alg.P_DY: -1,
            alg.P_OUTPUT_FACE: self.filename('3dCubeFace.vrt'),
            alg.P_OUTPUT_SIDE: self.filename('3dCubeSide.tif')
        }
        self.runalg(alg, parameters)

    def test_upper_left(self):
        alg = Build3dCubeAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DX: -1,
            alg.P_DY: -1,
            alg.P_OUTPUT_FACE: self.filename('3dCubeFace.vrt'),
            alg.P_OUTPUT_SIDE: self.filename('3dCubeSide.tif')
        }
        self.runalg(alg, parameters)

    def test_saveAsTif(self):
        alg = Build3dCubeAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DX: -1,
            alg.P_DY: -1,
            alg.P_OUTPUT_FACE: self.filename('3dCubeFace.tif'),
            alg.P_OUTPUT_SIDE: self.filename('3dCubeSide.tif')
        }
        self.runalg(alg, parameters)
