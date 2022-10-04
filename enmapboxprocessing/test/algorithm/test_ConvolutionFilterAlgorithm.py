from enmapbox.exampledata import hires
from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from enmapboxprocessing.algorithm.spatialconvolutionairydisk2dalgorithm import SpatialConvolutionAiryDisk2DAlgorithm
from enmapboxprocessing.algorithm.spatialconvolutionbox2dalgorithm import SpatialConvolutionBox2DAlgorithm
from enmapboxprocessing.algorithm.spatialconvolutioncustom2dalgorithm import SpatialConvolutionCustom2DAlgorithm
from enmapboxprocessing.algorithm.spatialconvolutiongaussian2dalgorithm import SpatialConvolutionGaussian2DAlgorithm
from enmapboxprocessing.algorithm.spatialconvolutionmoffat2dalgorithm import SpatialConvolutionMoffat2DAlgorithm
from enmapboxprocessing.algorithm.spatialconvolutionrickerwavelet2dalgorithm import \
    SpatialConvolutionRickerWavelet2DAlgorithm
from enmapboxprocessing.algorithm.spatialconvolutionring2dalgorithm import SpatialConvolutionRing2DAlgorithm
from enmapboxprocessing.algorithm.spatialconvolutionsavitskygolay2dalgorithm import \
    SpatialConvolutionSavitskyGolay2DAlgorithm
from enmapboxprocessing.algorithm.spatialconvolutiontophat2dalgorithm import SpatialConvolutionTophat2DAlgorithm
from enmapboxprocessing.algorithm.spatialconvolutiontrapezoiddisk2dalgorithm import \
    SpatialConvolutionTrapezoidDisk2DAlgorithm
from enmapboxprocessing.algorithm.spectralconvolutionbox1dalgorithm import SpectralConvolutionBox1DAlgorithm
from enmapboxprocessing.algorithm.spectralconvolutiongaussian1dalgorithm import SpectralConvolutionGaussian1DAlgorithm
from enmapboxprocessing.algorithm.spectralconvolutionrickerwavelet1dalgorithm import \
    SpectralConvolutionRickerWavelet1DAlgorithm
from enmapboxprocessing.algorithm.spectralconvolutionsavitskygolay1dalgorithm import \
    SpectralConvolutionSavitskyGolay1DAlgorithm
from enmapboxprocessing.algorithm.spectralconvolutiontrapezoid1dalgorithm import SpectralConvolutionTrapezoid1DAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase


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


class TestConvolutionFilterAlgorithm(TestCase):

    def test(self):
        alg = ConvolutionFilterAlgorithm()
        parameters = {
            alg.P_RASTER: hires,
            alg.P_KERNEL: alg.defaultCodeAsString(),
            alg.P_OUTPUT_RASTER: self.filename('filteredBox2D.tif')
        }
        self.runalg(alg, parameters)

    def test_filters(self):
        algs = [
            SpatialConvolutionAiryDisk2DAlgorithm(),
            SpatialConvolutionBox2DAlgorithm(),
            SpatialConvolutionCustom2DAlgorithm(),
            SpatialConvolutionGaussian2DAlgorithm(),
            SpatialConvolutionRing2DAlgorithm(),
            SpatialConvolutionSavitskyGolay2DAlgorithm(),
            SpatialConvolutionTophat2DAlgorithm(),
            SpatialConvolutionTrapezoidDisk2DAlgorithm(),
            SpectralConvolutionBox1DAlgorithm(),
            SpectralConvolutionGaussian1DAlgorithm(),
            SpectralConvolutionSavitskyGolay1DAlgorithm(),
            SpectralConvolutionTrapezoid1DAlgorithm(),
        ]
        for alg in algs:
            print(alg.displayName())
            alg.initAlgorithm()
            alg.shortHelpString()
            parameters = {
                alg.P_RASTER: hires,
                alg.P_KERNEL: alg.defaultCodeAsString(),
                alg.P_OUTPUT_RASTER: self.filename('filtered.tif')
            }
            self.runalg(alg, parameters)

            algs = [
                SpatialConvolutionMoffat2DAlgorithm(),
                SpatialConvolutionRickerWavelet2DAlgorithm(),
                SpectralConvolutionRickerWavelet1DAlgorithm()
            ]
            for alg in algs:
                print(alg.displayName())
            alg.initAlgorithm()
            alg.shortHelpString()
            parameters = {
                alg.P_RASTER: hires,
                alg.P_KERNEL: alg.defaultCodeAsString(),
                alg.P_INTERPOLATE: False,
                alg.P_OUTPUT_RASTER: self.filename('filtered.tif')
            }
            self.runalg(alg, parameters)

    def _test_debug_issue_1319(self):
        alg = SpatialConvolutionGaussian2DAlgorithm()
        parameters = {
            alg.P_RASTER: r'D:\data\issues\bitbucket\1319\01_11_water_binary_2020.tif',
            alg.P_KERNEL: alg.defaultCodeAsString(),
            alg.P_OUTPUT_RASTER: self.filename('filtered.tif')
        }

        if self.fileExists(parameters[alg.P_RASTER]):
            self.runalg(alg, parameters)
