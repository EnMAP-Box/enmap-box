from enmapboxprocessing.algorithm.fitclustereralgorithmbase import FitClustererAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitAffinityPropagationAlgorithm(FitClustererAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit AffinityPropagation'

    def shortDescription(self) -> str:
        return 'Perform Affinity Propagation Clustering.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AffinityPropagation.html' \
               '">AffinityPropagation</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import AffinityPropagation

        affinityPropagation = AffinityPropagation()
        clusterer = make_pipeline(StandardScaler(), affinityPropagation)
        return clusterer
