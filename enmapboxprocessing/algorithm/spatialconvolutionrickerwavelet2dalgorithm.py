from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from typeguard import typechecked


@typechecked
class SpatialConvolutionRickerWavelet2DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial convolution Ricker Wavelet filter'

    def shortDescription(self) -> str:
        return '2D Ricker Wavelet filter kernel (sometimes known as a Mexican Hat kernel).\n' \
               'The Ricker Wavelet, or inverted Gaussian-Laplace filter, is a bandpass filter. ' \
               'It smooths the data and removes slowly varying or constant structures (e.g. background). ' \
               'It is useful for peak or multi-scale detection.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.RickerWavelet2DKernel.html',
                             'RickerWavelet2DKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import RickerWavelet2DKernel
        kernel = RickerWavelet2DKernel(width=1)
        return kernel
