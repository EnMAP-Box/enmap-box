from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class FitMinMaxScalerAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit MinMaxScaler'

    def shortDescription(self) -> str:
        return 'Transform features by scaling each feature to a given range.\n' \
               'This estimator scales and translates each feature individually such that it is in the given range ' \
               'on the training set, e.g. between zero and one.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html' \
               '">MinMaxScaler</a> for information on different parameters.'

    def code(cls):
        from sklearn.preprocessing import MinMaxScaler

        transformer = MinMaxScaler(feature_range=(0, 1), clip=False)
        return transformer
