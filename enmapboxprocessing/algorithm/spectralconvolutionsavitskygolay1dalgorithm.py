from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class SpectralConvolutionSavitskyGolay1DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spectral convolution Savitsky-Golay filter'

    def shortDescription(self) -> str:
        link = self.htmlLink('https://en.wikipedia.org/wiki/Savitzky%E2%80%93Golay_filter', 'wikipedia')
        return '1D Savitsky-Golay filter.\n' \
               f'See {link} for details.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink(
            'https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.savgol_coeffs.html#scipy-signal-savgol-coeffs',
            'scipy.signal.savgol_coeffs')
        return f'Python code. See {link} for information on different parameters.'

    def code(cls):
        from astropy.convolution import Kernel1D
        from scipy.signal import savgol_coeffs
        kernel = Kernel1D(array=savgol_coeffs(window_length=11, polyorder=3, deriv=0))
        return kernel
