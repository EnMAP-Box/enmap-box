from enmapboxprocessing.algorithm.fitclustereralgorithmbase import FitClustererAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitMeanShiftAlgorithm(FitClustererAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit MeanShift'

    def shortDescription(self) -> str:
        return 'Mean shift clustering using a flat kernel.\n' \
               'Mean shift clustering aims to discover “blobs” in a smooth density of samples. ' \
               'It is a centroid-based algorithm, which works by updating candidates for centroids to be the mean ' \
               'of the points within a given region. These candidates are then filtered in a post-processing stage ' \
               'to eliminate near-duplicates to form the final set of centroids.\n' \
               'Seeding is performed using a binning technique for scalability.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.cluster.MeanShift.html' \
               '">MeanShift</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import MeanShift

        meanShift = MeanShift()
        clusterer = make_pipeline(StandardScaler(), meanShift)

        return clusterer
