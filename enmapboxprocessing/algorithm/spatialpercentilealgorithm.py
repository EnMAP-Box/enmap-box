from enmapboxprocessing.algorithm.spatialfilterfunctionalgorithmbase import SpatialFilterFunctionAlgorithmBase
from enmapboxprocessing.enmapalgorithm import Group
from typeguard import typechecked


@typechecked
class SpatialPercentileAlgorithm(SpatialFilterFunctionAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial Percentile filter'

    def group(self):
        return Group.Test.value + Group.ConvolutionMorphologyAndFiltering.value

    def shortDescription(self) -> str:
        return 'Spatial Percentile filter.'

    def helpParameterCode(self) -> str:
        links = ', '.join([
            self.htmlLink('https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.percentile_filter.html',
                          'percentile_filter')
        ])
        return f'Python code. See {links} for information on different parameters.'

    def code(cls):
        from scipy.ndimage.filters import percentile_filter

        function = lambda array: percentile_filter(array, percentile=50, size=3)
        return function
