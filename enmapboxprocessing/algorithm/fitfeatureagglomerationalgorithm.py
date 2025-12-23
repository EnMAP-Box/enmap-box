from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitFeatureAgglomerationAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit FeatureAgglomeration'

    def shortDescription(self) -> str:
        return 'Agglomerate features.\n' \
               'Recursively merges pair of clusters of features.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.cluster.FeatureAgglomeration.html' \
               '">FeatureAgglomeration</a> for information on different parameters.'

    def code(cls):
        from sklearn.cluster import FeatureAgglomeration

        transformer = FeatureAgglomeration(n_clusters=3)

        return transformer
