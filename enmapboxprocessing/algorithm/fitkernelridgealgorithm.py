from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitKernelRidgeAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit KernelRidge'

    def shortDescription(self) -> str:
        return 'Kernel ridge regression.\n' \
               'Kernel ridge regression (KRR) combines ridge regression (linear least squares with l2-norm ' \
               'regularization) with the kernel trick. It thus learns a linear function in the space induced by the ' \
               'respective kernel and the data. For non-linear kernels, this corresponds to a non-linear function ' \
               'in the original space.\n' \
               'The form of the model learned by KRR is identical to support vector regression (SVR). However, ' \
               'different loss functions are used: KRR uses squared error loss while support vector regression ' \
               'uses epsilon-insensitive loss, both combined with l2 regularization. In contrast to SVR, fitting ' \
               'a KRR model can be done in closed-form and is typically faster for medium-sized datasets. On the ' \
               'other hand, the learned model is non-sparse and thus slower than SVR, which learns a sparse model ' \
               'for epsilon > 0, at prediction-time.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.kernel_ridge.KernelRidge.html' \
               '">KernelRidge</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.model_selection import GridSearchCV
        from sklearn.preprocessing import StandardScaler
        from sklearn.kernel_ridge import KernelRidge

        krr = KernelRidge()
        param_grid = {'kernel': ['rbf'],
                      'gamma': [0.001, 0.01, 0.1, 1, 10, 100, 1000],
                      'alpha': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}
        tunedKRR = GridSearchCV(cv=3, estimator=krr, scoring='neg_mean_absolute_error', param_grid=param_grid)
        regressor = make_pipeline(StandardScaler(), tunedKRR)
        return regressor
