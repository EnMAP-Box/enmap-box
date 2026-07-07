import unittest

from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.algorithms import algorithms
from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import hires

MISSING_MODULE = None
try:
    import astropy  # noqa: F401
except ModuleNotFoundError as ex:
    MISSING_MODULE = str(ex)

start_app()


class ConvolutionFilterAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return ''

    def shortDescription(self) -> str:
        return ''

    def helpParameterCode(self) -> str:
        return ''

    def code(self):
        from astropy.convolution import Box2DKernel
        kernel = Box2DKernel(width=15)
        return kernel


@unittest.skipIf(MISSING_MODULE, f'Missing module: {MISSING_MODULE}')
class TestConvolutionFilterAlgorithm(TestCase):

    def test_convolutionFilterAlgorithm(self):
        alg = ConvolutionFilterAlgorithm()
        parameters = {
            alg.P_RASTER: hires,
            alg.P_KERNEL: alg.defaultCodeAsString(),
            alg.P_OUTPUT_RASTER: self.filename('filteredBox2D.tif')
        }
        self.runalg(alg, parameters)

    def test_1dFilters(self):
        for alg in algorithms():
            if isinstance(alg, ConvolutionFilterAlgorithmBase) and alg.displayName().startswith('Spectral'):
                print(alg.displayName())
            else:
                continue
            alg.initAlgorithm()
            alg.shortHelpString()
            parameters = {
                alg.P_RASTER: hires,
                alg.P_KERNEL: alg.defaultCodeAsString(),
                alg.P_OUTPUT_RASTER: self.filename('filtered.tif')
            }
            self.runalg(alg, parameters)

    def test_2dFilters(self):
        for alg in algorithms():
            if isinstance(alg, ConvolutionFilterAlgorithmBase) and alg.displayName().startswith('Spatial'):
                print(alg.displayName())
            else:
                continue
            alg.initAlgorithm()
            alg.shortHelpString()
            parameters = {
                alg.P_RASTER: hires,
                alg.P_KERNEL: alg.defaultCodeAsString(),
                alg.P_OUTPUT_RASTER: self.filename('filtered.tif')
            }
            self.runalg(alg, parameters)
