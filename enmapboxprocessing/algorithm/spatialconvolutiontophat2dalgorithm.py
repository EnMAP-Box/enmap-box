from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from typeguard import typechecked


@typechecked
class SpatialConvolutionTophat2DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial convolution Top-Hat filter'

    def shortDescription(self) -> str:
        return '2D Top-Hat filter.\n' \
               'The Top-Hat filter is an isotropic smoothing filter. ' \
               'It can produce artifacts when applied repeatedly on the same data.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.Tophat2DKernel.html',
                             'Tophat2DKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import Tophat2DKernel
        kernel = Tophat2DKernel(radius=1)
        return kernel
