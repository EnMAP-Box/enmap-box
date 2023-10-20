from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitPcaAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit PCA'

    def shortDescription(self) -> str:
        return 'Principal component analysis (PCA).\n' \
               'Linear dimensionality reduction using Singular Value Decomposition of the data to project it to a ' \
               'lower dimensional space. The input data is centered but not scaled for each feature before applying ' \
               'the SVD.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html' \
               '">PCA</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA

        pca = PCA(n_components=0.95)
        transformer = make_pipeline(StandardScaler(), pca)
        return transformer

    def summary(self, transformer):
        return {'explained_variance_ratio_': transformer.steps[1][1].explained_variance_ratio_.tolist()}
