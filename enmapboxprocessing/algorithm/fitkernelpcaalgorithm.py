from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from typeguard import typechecked


@typechecked
class FitKernelPcaAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit KernelPCA'

    def shortDescription(self) -> str:
        return 'Kernel Principal component analysis (KPCA).\n' \
               'Non-linear dimensionality reduction through the use of kernels'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.KernelPCA.html' \
               '">PCA</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import KernelPCA

        kernelPCA = KernelPCA(n_components=3, fit_inverse_transform=True)
        transformer = make_pipeline(StandardScaler(), kernelPCA)
        return transformer
