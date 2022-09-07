from enmapboxprocessing.algorithm.spatialfilterfunctionalgorithmbase import SpatialFilterFunctionAlgorithmBase
from enmapboxprocessing.enmapalgorithm import Group
from typeguard import typechecked


@typechecked
class SpatialGaussianGradientMagnitudeAlgorithm(SpatialFilterFunctionAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial Gaussian Gradient Magnitude filter'

    def group(self):
        return Group.Test.value + Group.ConvolutionMorphologyAndFiltering.value

    def shortDescription(self) -> str:
        return 'Spatial Gaussian Gradient Magnitude filter.'

    def helpParameterCode(self) -> str:
        links = ', '.join([
            self.htmlLink(
                'https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_gradient_magnitude.html',
                'gaussian_gradient_magnitude')])
        return f'Python code. See {links} for information on different parameters.'

    def code(cls):
        from scipy.ndimage.filters import gaussian_gradient_magnitude

        function = lambda array: gaussian_gradient_magnitude(array, sigma=1)
        return function
