from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from typeguard import typechecked


@typechecked
class SpectralConvolutionBox1DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spectral convolution Box filter'

    def shortDescription(self) -> str:
        return '1D Box filter.\n' \
               'The Box filter or running mean is a smoothing filter. ' \
               'It is not isotropic and can produce artifacts, when applied repeatedly to the same data.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.Box1DKernel.html',
                             'Box1DKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import Box1DKernel
        kernel = Box1DKernel(width=5)
        return kernel
