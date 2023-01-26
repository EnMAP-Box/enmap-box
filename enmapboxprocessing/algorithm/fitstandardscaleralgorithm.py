from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitStandardScalerAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit StandardScaler'

    def shortDescription(self) -> str:
        return 'Standardize features by removing the mean and scaling to unit variance.\n' \
               'The standard score of a sample x is calculated as:\n' \
               'z = (x - u) / s\n' \
               'where u is the mean of the training samples or zero if with_mean=False, and s is the standard ' \
               'deviation of the training samples or one if with_std=False.\n' \
               'Centering and scaling happen independently on each feature by computing the relevant statistics ' \
               'on the samples in the training set. Mean and standard deviation are then stored to be used on later ' \
               'data using transform.\n' \
               'Standardization of a dataset is a common requirement for many machine learning estimators: ' \
               'they might behave badly if the individual features do not more or less look like standard normally ' \
               'distributed data (e.g. Gaussian with 0 mean and unit variance).\n' \
               'For instance many elements used in the objective function of a learning algorithm ' \
               '(such as the RBF kernel of Support Vector Machines or the L1 and L2 regularizers of linear models) ' \
               'assume that all features are centered around 0 and have variance in the same order. ' \
               'If a feature has a variance that is orders of magnitude larger that others, it might dominate the ' \
               'objective function and make the estimator unable to learn from other features correctly as expected.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html' \
               '">StandardScaler</a> for information on different parameters.'

    def code(cls):
        from sklearn.preprocessing import StandardScaler

        transformer = StandardScaler()
        return transformer
