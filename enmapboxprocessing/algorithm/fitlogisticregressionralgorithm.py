from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitLogisticRegressionAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit LogisticRegression'

    def shortDescription(self) -> str:
        return 'Logistic Regression (aka logit, MaxEnt) classifier.' \
               '\nIn the multiclass case, the training algorithm uses the one-vs-rest (OvR) scheme if the ' \
               "'multi_class' option is set to 'ovr', and uses the cross-entropy loss if the 'multi_class' option " \
               "is set to 'multinomial'."

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html' \
               '">LogisticRegression</a> for information on different parameters.'

    def code(cls):
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline
        logisticRegression = LogisticRegression()
        classifier = make_pipeline(StandardScaler(), logisticRegression)
        return classifier
