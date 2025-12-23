from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitFactorAnalysisAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit FactorAnalysis'

    def shortDescription(self) -> str:
        return 'Factor Analysis.\n' \
               'A simple linear generative model with Gaussian latent variables.\n' \
               'The observations are assumed to be caused by a linear transformation of lower dimensional latent ' \
               'factors and added Gaussian noise. Without loss of generality the factors are distributed according ' \
               'to a Gaussian with zero mean and unit covariance. The noise is also zero mean and has an arbitrary ' \
               'diagonal covariance matrix.\n' \
               'If we would restrict the model further, by assuming that the Gaussian noise is even isotropic ' \
               '(all diagonal entries are the same) we would obtain ProbabilisticPCA.\n' \
               'FactorAnalysis performs a maximum likelihood estimate of the so-called loading matrix, ' \
               'the transformation of the latent variables to the observed ones, using SVD based approach.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FactorAnalysis.html' \
               '">FactorAnalysis</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import FactorAnalysis

        factorAnalysis = FactorAnalysis(n_components=3)
        transformer = make_pipeline(StandardScaler(), factorAnalysis)
        return transformer
