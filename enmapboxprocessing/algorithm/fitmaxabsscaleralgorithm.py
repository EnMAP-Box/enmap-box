from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitMaxAbsScalerAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit MaxAbsScaler'

    def shortDescription(self) -> str:
        return 'Scale each feature by its maximum absolute value.\n' \
               'This estimator scales and translates each feature individually such that the maximal absolute ' \
               'value of each feature in the training set will be 1.0.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MaxAbsScaler.html' \
               '">MaxAbsScaler</a> for information on different parameters.'

    def code(cls):
        from sklearn.preprocessing import MaxAbsScaler

        transformer = MaxAbsScaler()
        return transformer
