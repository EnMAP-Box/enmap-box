from enmapboxprocessing.algorithm.spatialfilterfunctionalgorithmbase import SpatialFilterFunctionAlgorithmBase
from enmapboxprocessing.enmapalgorithm import Group
from typeguard import typechecked


@typechecked
class SpatialMorphologicalBinaryFillHolesAlgorithm(SpatialFilterFunctionAlgorithmBase):

    def displayName(self) -> str:
        return 'Spatial morphological Binary Fill Holes filter'

    def group(self):
        return Group.Test.value + Group.ConvolutionMorphologyAndFiltering.value

    def shortDescription(self) -> str:
        return 'Spatial morphological Binary Fill Holes filter.'

    def helpParameterCode(self) -> str:
        links = ', '.join([
            self.htmlLink('https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.binary_fill_holes.html',
                          'binary_closing'),
            self.htmlLink(
                'https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.generate_binary_structure.html',
                'generate_binary_structure'),
            self.htmlLink('https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.iterate_structure.html',
                          'iterate_structure')
        ])
        return f'Python code. See {links} for information on different parameters.'

    def code(cls):
        from scipy.ndimage.morphology import binary_fill_holes, generate_binary_structure, iterate_structure

        structure = generate_binary_structure(rank=2, connectivity=1)
        structure = iterate_structure(structure=structure, iterations=1)
        function = lambda array: binary_fill_holes(array, structure=structure)
        return function
