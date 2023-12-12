from enmapboxprocessing.algorithm.spatialfilterfunctionalgorithmbase import SpatialFilterFunctionAlgorithmBase
from enmapboxprocessing.enmapalgorithm import Group
from enmapbox.typeguard import typechecked


@typechecked
class SpatialMorphologicalGreyOpeningAlgorithm(SpatialFilterFunctionAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial morphological Grey Opening filter'

    def group(self):
        return Group.ConvolutionMorphologyAndFiltering.value

    def shortDescription(self) -> str:
        link = self.htmlLink('https://en.wikipedia.org/wiki/Opening_(morphology)', 'Wikipedia')
        return f'Spatial morphological Grey Opening filter. See {link} for general information.'

    def helpParameterCode(self) -> str:
        links = ', '.join([
            self.htmlLink('https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.grey_opening.html',
                          'grey_opening'),
            self.htmlLink(
                'https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.generate_binary_structure.html',
                'generate_binary_structure'),
            self.htmlLink('https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.iterate_structure.html',
                          'iterate_structure')
        ])
        return f'Python code. See {links} for information on different parameters.'

    def code(cls):
        from scipy.ndimage import grey_opening, generate_binary_structure, iterate_structure

        structure = generate_binary_structure(rank=2, connectivity=1)
        structure = iterate_structure(structure=structure, iterations=1)
        function = lambda array: grey_opening(array, structure=structure)
        return function
