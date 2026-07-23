from enmapboxprocessing.algorithm.spatialfilterfunctionalgorithmbase import SpatialFilterFunctionAlgorithmBase
from enmapboxprocessing.enmapalgorithm import Group
from enmapbox.typeguard import typechecked


@typechecked
class SpatialPrewittAlgorithm(SpatialFilterFunctionAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial Prewitt filter'

    def group(self):
        return Group.ConvolutionMorphologyAndFiltering.value

    def shortDescription(self) -> str:
        link = self.htmlLink('https://en.wikipedia.org/wiki/Prewitt_operator', 'Wikipedia')
        return f'Spatial Prewitt filter. See {link} for general information.'

    def helpParameterCode(self) -> str:
        links = ', '.join([
            self.htmlLink('https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.prewitt.html',
                          'prewitt')
        ])
        return f'Python code. See {links} for information on different parameters.'

    def code(cls):
        from scipy.ndimage.filters import prewitt

        function = lambda array: prewitt(array, axis=0)
        return function
