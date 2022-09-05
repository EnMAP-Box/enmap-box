from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.vrtbandmathalgorithm import VrtBandMathAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestVrtBandMathAlgorithm(TestCase):

    def test_simple(self):
        alg = VrtBandMathAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_DATA_TYPE: alg.Float32,
            alg.P_NODATA: -9999,
            alg.P_BAND_NAME: 'NDVI',
            alg.P_BAND_LIST: [38, 64],
            alg.P_CODE: 'import numpy as np\n'
                        'def ufunc(in_ar, out_ar, xoff, yoff, xsize, ysize, raster_xsize, raster_ysize, buf_radius, gt):\n'
                        '    red, nir = in_ar\n'
                        '    ndvi = (nir - red) / (nir + red)\n'
                        '    ndvi = (nir - red) / (nir + red)\n'
                        '    ndvi[nir == -99] = -9999\n'
                        '    ndvi[red == -99] = -9999\n'
                        '    out_ar[:] = ndvi\n',
            alg.P_OUTPUT_VRT: self.filename('raster.vrt')
        }
        result = self.runalg(alg, parameters)
        # self.assertEqual(14908457369, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(), dtype=float))
        # self.assertEqual(self.filename('enmap.tif'), RasterReader(result[alg.P_OUTPUT_RASTER]).source())

    def test_multiple_crs(self):
        pass  # todo

    def test_overlap(self):
        pass  # todo
