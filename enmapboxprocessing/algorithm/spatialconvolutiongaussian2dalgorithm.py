from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class SpatialConvolutionGaussian2DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial convolution Gaussian filter'

    def shortDescription(self) -> str:
        return '2D Gaussian filter.\n' \
               'The Gaussian filter is a filter with great smoothing properties. ' \
               'It is isotropic and does not produce artifacts.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.Gaussian2DKernel.html',
                             'Gaussian2DKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import Gaussian2DKernel
        kernel = Gaussian2DKernel(x_stddev=1, y_stddev=1)
        return kernel
