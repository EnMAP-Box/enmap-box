from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitQuantileTransformerAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit QuantileTransformer'

    def shortDescription(self) -> str:
        return 'Transform features using quantiles information.\n' \
               'This method transforms the features to follow a uniform or a normal distribution. ' \
               'Therefore, for a given feature, this transformation tends to spread out the most frequent values. ' \
               'It also reduces the impact of (marginal) outliers: this is therefore a robust preprocessing scheme.\n' \
               'The transformation is applied on each feature independently. First an estimate of the cumulative ' \
               'distribution function of a feature is used to map the original values to a uniform distribution. ' \
               'The obtained values are then mapped to the desired output distribution using the associated quantile ' \
               'function. Features values of new/unseen data that fall below or above the fitted range will be ' \
               'mapped to the bounds of the output distribution. Note that this transform is non-linear. ' \
               'It may distort linear correlations between variables measured at the same scale but renders ' \
               'variables measured at different scales more directly comparable.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.QuantileTransformer.html' \
               '">QuantileTransformer</a> for information on different parameters.'

    def code(cls):
        from sklearn.preprocessing import QuantileTransformer

        transformer = QuantileTransformer()
        return transformer
