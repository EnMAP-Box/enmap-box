from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class FitRobustScalerAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit RobustScaler'

    def shortDescription(self) -> str:
        return 'Scale features using statistics that are robust to outliers.\n' \
               'This Scaler removes the median and scales the data according to the quantile range ' \
               '(defaults to IQR: Interquartile Range). The IQR is the range between the 1st quartile (25th quantile)' \
               ' and the 3rd quartile (75th quantile).\n' \
               'Centering and scaling happen independently on each feature by computing the relevant statistics on ' \
               'the samples in the training set. Median and interquartile range are then stored to be used on later ' \
               'data using the transform method.\n' \
               'Standardization of a dataset is a common requirement for many machine learning estimators. ' \
               'Typically this is done by removing the mean and scaling to unit variance. However, outliers can ' \
               'often influence the sample mean / variance in a negative way. In such cases, the median and the ' \
               'interquartile range often give better results.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html' \
               '">RobustScaler</a> for information on different parameters.'

    def code(cls):
        from sklearn.preprocessing import RobustScaler

        transformer = RobustScaler(quantile_range=(25, 75))
        return transformer
