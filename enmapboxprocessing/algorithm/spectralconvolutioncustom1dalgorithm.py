from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class SpectralConvolutionCustom1DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spectral convolution custom filter'

    def shortDescription(self) -> str:
        return 'Create a spectral 1D filter kernel from list or array.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.CustomKernel.html',
                             'CustomKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import CustomKernel
        array = [1, 1, 1]
        kernel = CustomKernel(array)
        return kernel
