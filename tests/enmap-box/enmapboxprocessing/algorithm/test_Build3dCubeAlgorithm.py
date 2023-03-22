from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.build3dcubealgorithm import Build3dCubeAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase


class TestBuild3dCubeAlgorithm(TestCase):

    def test_lower_right(self):
        alg = Build3dCubeAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DX: 1,
            alg.P_DY: 1,
            alg.P_OUTPUT_FACE: self.filename('3dCubeFace1.vrt'),
            alg.P_OUTPUT_SIDE: self.filename('3dCubeSide1.tif')
        }
        self.runalg(alg, parameters)

    def test_lower_left(self):  # ENVI Classic Style
        alg = Build3dCubeAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DX: -1,
            alg.P_DY: 1,
            alg.P_OUTPUT_FACE: self.filename('3dCubeFace2.vrt'),
            alg.P_OUTPUT_SIDE: self.filename('3dCubeSide2.tif')
        }
        self.runalg(alg, parameters)

    def test_upper_right(self):
        alg = Build3dCubeAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DX: 1,
            alg.P_DY: -1,
            alg.P_OUTPUT_FACE: self.filename('3dCubeFace3.vrt'),
            alg.P_OUTPUT_SIDE: self.filename('3dCubeSide3.tif')
        }
        self.runalg(alg, parameters)

    def test_upper_left(self):
        alg = Build3dCubeAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DX: -1,
            alg.P_DY: -1,
            alg.P_OUTPUT_FACE: self.filename('3dCubeFace4.vrt'),
            alg.P_OUTPUT_SIDE: self.filename('3dCubeSide4.tif')
        }
        self.runalg(alg, parameters)
