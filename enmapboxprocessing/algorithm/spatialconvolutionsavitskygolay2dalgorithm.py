import numpy as np

from enmapboxprocessing.algorithm.convolutionfilteralgorithmbase import ConvolutionFilterAlgorithmBase
from typeguard import typechecked


@typechecked
class SpatialConvolutionSavitskyGolay2DAlgorithm(ConvolutionFilterAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial convolution Savitsky-Golay filter'

    def shortDescription(self) -> str:
        link = self.htmlLink(
            'https://en.wikipedia.org/wiki/Savitzky%E2%80%93Golay_filter#Two-dimensional_convolution_coefficients',
            'wikipedia'
        )
        return '2D Savitsky-Golay filter.\n' \
               f'See {link} for details.'

    def helpParameterCode(self) -> str:
        link = self.htmlLink(
            'https://scipy-cookbook.readthedocs.io/items/SavitzkyGolay.html#Two-dimensional-data-smoothing-and-least-square-gradient-estimate',
            'sgolay2d')
        return f'Python code. See {link} from the SciPy cookbook for information on different parameters.'

    def code(cls):
        from astropy.convolution import Kernel2D
        from enmapboxprocessing.algorithm.spatialconvolutionsavitskygolay2dalgorithm import sgolay2d
        kernel = Kernel2D(array=sgolay2d(window_size=11, order=3, derivative=None))
        return kernel


def sgolay2d(window_size, order, derivative=None):
    """
    """
    # number of terms in the polynomial expression
    n_terms = (order + 1) * (order + 2) / 2.0

    if window_size % 2 == 0:
        raise ValueError('window_size must be odd')

    if window_size ** 2 < n_terms:
        raise ValueError('order is too high for the window size')

    half_size = window_size // 2

    # exponents of the polynomial.
    # p(x,y) = a0 + a1*x + a2*y + a3*x^2 + a4*y^2 + a5*x*y + ...
    # this line gives a list of two item tuple. Each tuple contains
    # the exponents of the k-th term. First element of tuple is for x
    # second element for y.
    # Ex. exps = [(0,0), (1,0), (0,1), (2,0), (1,1), (0,2), ...]
    exps = [(k - n, n) for k in range(order + 1) for n in range(k + 1)]

    # coordinates of points
    ind = np.arange(-half_size, half_size + 1, dtype=np.float64)
    dx = np.repeat(ind, window_size)
    dy = np.tile(ind, [window_size, 1]).reshape(window_size ** 2, )

    # build matrix of system of equation
    A = np.empty((window_size ** 2, len(exps)))
    for i, exp in enumerate(exps):
        A[:, i] = (dx ** exp[0]) * (dy ** exp[1])

    # solve system
    if derivative is None:
        m = np.linalg.pinv(A)[0].reshape((window_size, -1))
    elif derivative == 'col':
        c = np.linalg.pinv(A)[1].reshape((window_size, -1))
        m = -c
    elif derivative == 'row':
        r = np.linalg.pinv(A)[2].reshape((window_size, -1))
        m = -r
    elif derivative == 'both':
        c = np.linalg.pinv(A)[1].reshape((window_size, -1))
        r = np.linalg.pinv(A)[2].reshape((window_size, -1))
        m = -c * -r  # not sure if that is really useful!
    else:
        raise ValueError('wrong value for derivative')

    return m
