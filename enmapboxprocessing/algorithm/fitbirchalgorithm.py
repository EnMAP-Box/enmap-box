from enmapboxprocessing.algorithm.fitclustereralgorithmbase import FitClustererAlgorithmBase
from typeguard import typechecked


@typechecked
class FitBirchAlgorithm(FitClustererAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit Birch'

    def shortDescription(self) -> str:
        return 'Implements the BIRCH clustering algorithm.\n' \
               'It is a memory-efficient, online-learning algorithm provided as an alternative to MiniBatchKMeans. ' \
               'It constructs a tree data structure with the cluster centroids being read off the leaf. ' \
               'These can be either the final cluster centroids or can be provided as input to another clustering ' \
               'algorithm such as AgglomerativeClustering.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.cluster.Birch.html' \
               '">Birch</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import Birch

        birch = Birch(n_clusters=3)
        clusterer = make_pipeline(StandardScaler(), birch)
        return clusterer
