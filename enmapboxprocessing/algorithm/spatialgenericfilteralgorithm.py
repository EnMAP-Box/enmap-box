from enmapboxprocessing.algorithm.spatialfilterfunctionalgorithmbase import SpatialFilterFunctionAlgorithmBase
from enmapboxprocessing.enmapalgorithm import Group
from typeguard import typechecked


@typechecked
class SpatialGenericAlgorithm(SpatialFilterFunctionAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial generic filter'

    def group(self):
        return Group.Test.value + Group.ConvolutionMorphologyAndFiltering.value

    def shortDescription(self) -> str:
        return 'Spatial generic (user-defined) filter.'

    def helpParameterCode(self) -> str:
        links = ', '.join([
            self.htmlLink('https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.generic_filter.html',
                          'generic_filter')
        ])
        return f'Python code. See {links} for information on different parameters.'

    def code(cls):
        from scipy.ndimage.filters import generic_filter
        import numpy as np

        def filter_function(invalues):
            # do whatever you want to create the output value, e.g. np.nansum
            outvalue = np.nansum(invalues)  # replace this line with your code!
            return outvalue

        function = lambda array: generic_filter(array, function=filter_function, size=3)
        return function
