from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from typeguard import typechecked


@typechecked
class FitNormalizerAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit Normalizer'

    def shortDescription(self) -> str:
        return 'Normalize samples individually to unit norm.\n' \
               'Each sample (i.e. each row of the data matrix) with at least one non zero component is rescaled ' \
               'independently of other samples so that its norm (l1, l2 or inf) equals one.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.Normalizer.html' \
               '">Normalizer</a> for information on different parameters.'

    def code(cls):
        from sklearn.preprocessing import Normalizer

        transformer = Normalizer()
        return transformer
