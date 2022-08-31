from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from typeguard import typechecked


@typechecked
class SpatialConvolutionRing2DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial convolution ring filter'

    def shortDescription(self) -> str:
        return '2D Ring filter.\n' \
               'The Ring filter kernel is the difference between two Top-Hat kernels of different width. ' \
               'This kernel is useful for, e.g., background estimation.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.Ring2DKernel.html',
                             'Ring2DKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import Ring2DKernel
        kernel = Ring2DKernel(radius_in=3, width=2)
        return kernel
