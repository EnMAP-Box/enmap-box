from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class SpatialConvolutionMoffat2DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial convolution Moffat filter'

    def shortDescription(self) -> str:
        return '2D Moffat filter.\n' \
               'This kernel is a typical model for a seeing limited PSF.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.Moffat2DKernel.html',
                             'Moffat2DKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import Moffat2DKernel
        kernel = Moffat2DKernel(gamma=2, alpha=2)
        return kernel
