from enmapboxprocessing.algorithm.spatialfilterfunctionalgorithmbase import SpatialFilterFunctionAlgorithmBase
from enmapboxprocessing.enmapalgorithm import Group
from typeguard import typechecked


@typechecked
class SpatialMedianAlgorithm(SpatialFilterFunctionAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial Median filter'

    def group(self):
        return Group.Test.value + Group.ConvolutionMorphologyAndFiltering.value

    def shortDescription(self) -> str:
        return 'Spatial Median filter.'

    def helpParameterCode(self) -> str:
        links = ', '.join([
            self.htmlLink('https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.median_filter.html',
                          'median_filter')
        ])
        return f'Python code. See {links} for information on different parameters.'

    def code(cls):
        from scipy.ndimage.filters import median_filter

        function = lambda array: median_filter(array, size=3)
        return function
