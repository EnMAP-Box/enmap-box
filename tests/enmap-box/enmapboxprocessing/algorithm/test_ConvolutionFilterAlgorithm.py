import unittest

from enmapboxprocessing.algorithm.algorithms import algorithms
from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import hires

try:
    import astropy.convolution

    assert astropy.convolution is not None
    has_astropy = True
except ModuleNotFoundError:
    has_astropy = False


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


@unittest.skipIf(not has_astropy, 'astropy is not installed')
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
