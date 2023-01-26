from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class SpatialConvolutionAiryDisk2DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial convolution Airy Disk filter'

    def shortDescription(self) -> str:
        return '2D Airy Disk filter.\n' \
               'This kernel models the diffraction pattern of a circular aperture. ' \
               'This kernel is normalized to a peak value of 1'

    def helpParameterCode(self) -> str:
        link = self.htmlLink('http://docs.astropy.org/en/stable/api/astropy.convolution.AiryDisk2DKernel.html',
                             'AiryDisk2DKernel')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import AiryDisk2DKernel
        kernel = AiryDisk2DKernel(radius=1)
        return kernel
