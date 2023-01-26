from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitFastIcaAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit FastICA'

    def shortDescription(self) -> str:
        return 'FastICA: a fast algorithm for Independent Component Analysis.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FastICA.html' \
               '">FastICA</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import FastICA

        fastICA = FastICA(n_components=3)
        transformer = make_pipeline(StandardScaler(), fastICA)
        return transformer
