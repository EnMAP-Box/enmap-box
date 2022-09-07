from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from typeguard import typechecked


@typechecked
class FitRandomForestClassifierAlgorithm(FitClassifierAlgorithmBase):

    def flags(self):
        return super().flags() | self.Flag.FlagHideFromModeler

    def displayName(self) -> str:
        return 'Fit RandomForestClassifier'

    def shortDescription(self) -> str:
        return 'A random forest classifier.' \
               '\nA random forest is a meta estimator that fits a number of decision tree classifiers on various ' \
               'sub-samples of the dataset and uses averaging to improve the predictive accuracy and control ' \
               'over-fitting. The sub-sample size is controlled with the max_samples parameter if bootstrap=True ' \
               '(default), otherwise the whole dataset is used to build each tree.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html' \
               '">RandomForestClassifier</a> for information on different parameters.'

    def code(cls):
        from sklearn.ensemble import RandomForestClassifier
        classifier = RandomForestClassifier(n_estimators=100, oob_score=True)
        return classifier


class FitRandomForestClassifierAlgorithm4Modeler(FitRandomForestClassifierAlgorithm):

    def flags(self):
        return self.Flag.FlagHideFromToolbox | self.Flag.FlagNotAvailableInStandaloneTool

    def name(self) -> str:
        return super().name() + '4Modeler'
