from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from typeguard import typechecked


@typechecked
class SpatialConvolutionBox2DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial convolution Box filter'

    def shortDescription(self) -> str:
        return '2D Box filter.\n' \
               'The Box filter or running mean is a smoothing filter. It is not isotropic and can produce artifact, ' \
               'when applied repeatedly to the same data.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.Box2DKernel.html',
                             'Box2DKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import Box2DKernel
        kernel = Box2DKernel(width=5)
        return kernel
