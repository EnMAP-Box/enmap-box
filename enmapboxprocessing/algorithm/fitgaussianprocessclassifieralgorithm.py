from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitGaussianProcessClassifierAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit GaussianProcessClassifier'

    def shortDescription(self) -> str:
        return 'Gaussian process classification (GPC) based on Laplace approximation.' \
               '\nThe implementation is based on Algorithm 3.1, 3.2, and 5.1 of Gaussian Processes for ' \
               'Machine Learning (GPML) by Rasmussen and Williams. ' \
               '\nInternally, the Laplace approximation is used for approximating the non-Gaussian posterior by a ' \
               'Gaussian. ' \
               'Currently, the implementation is restricted to using the logistic link function. ' \
               'For multi-class classification, several binary one-versus rest classifiers are fitted. ' \
               'Note that this class thus does not implement a true multi-class Laplace approximation.' \
               '\nSee <a href="' \
               'http://scikit-learn.org/stable/modules/gaussian_process.html' \
               '">Gaussian Processes</a> for further information.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'http://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.GaussianProcessClassifier.html' \
               '">GaussianProcessClassifier</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.gaussian_process import GaussianProcessClassifier
        from sklearn.gaussian_process.kernels import RBF

        gpc = GaussianProcessClassifier(RBF(), max_iter_predict=1)
        classifier = make_pipeline(StandardScaler(), gpc)
        return classifier
