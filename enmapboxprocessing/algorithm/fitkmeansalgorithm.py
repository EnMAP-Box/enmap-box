from enmapboxprocessing.algorithm.fitclustereralgorithmbase import FitClustererAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class FitKMeansAlgorithm(FitClustererAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit KMeans'

    def shortDescription(self) -> str:
        return 'K-Means clustering.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html' \
               '">KMeans</a> for information on different parameters.'

    def code(cls):
        from sklearn.cluster import KMeans

        clusterer = KMeans(n_clusters=8)
        return clusterer
