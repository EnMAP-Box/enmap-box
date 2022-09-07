from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from typeguard import typechecked


@typechecked
class FitSamAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit SpectralAngleMapper'

    def shortDescription(self) -> str:
        return 'Spectral Angle Mapper (SAM).\n' \
               'Samples are first normalizes to the unit sphere and then classified using nearest neighbour.\n' \
               'See ' \
               '<a href="' \
               'https://www.l3harrisgeospatial.com/docs/spectralanglemapper.html' \
               '">Docs Center > Using ENVI > Spectral Angle Mapper</a> for a more details description.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See ' \
               '<a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.Normalizer.html' \
               '">Normalizer</a>, ' \
               '<a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html' \
               '">KNeighborsClassifier</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import Normalizer
        from sklearn.neighbors import KNeighborsClassifier

        classifier = make_pipeline(Normalizer(), KNeighborsClassifier(n_neighbors=1))
        return classifier
