from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from typeguard import typechecked


@typechecked
class SpectralConvolutionGaussian1DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spectral convolution Gaussian filter'

    def shortDescription(self) -> str:
        return '1D Gaussian filter.\n' \
               'The Gaussian filter is a filter with great smoothing properties. ' \
               'It is isotropic and does not produce artifacts.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.Gaussian1DKernel.html',
                             'Gaussian1DKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import Gaussian1DKernel
        kernel = Gaussian1DKernel(stddev=1)
        return kernel
