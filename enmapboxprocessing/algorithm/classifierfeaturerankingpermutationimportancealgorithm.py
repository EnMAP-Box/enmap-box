import webbrowser
from os.path import basename
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.reportwriter import MultiReportWriter, HtmlReportWriter, CsvReportWriter
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class ClassifierFeatureRankingPermutationImportanceAlgorithm(EnMAPProcessingAlgorithm):
    P_CLASSIFIER, _CLASSIFIER = 'classifier', 'Classifier'
    P_TRAIN_DATASET, _TRAIN_DATASET = 'trainDataset', 'Training dataset'
    P_TEST_DATASET, _TEST_DATASET = 'testDataset', 'Test dataset'
    P_EVALUATION_METRIC, _EVALUATION_METRIC = 'evaluationMetric', 'Evaluation metric'
    O_EVALUATION_METRIC = [
        'accuracy', 'balanced_accuracy', 'top_k_accuracy', 'average_precision', 'neg_brier_score', 'f1', 'f1_micro',
        'f1_macro', 'f1_weighted', 'f1_samples', 'neg_log_loss', 'precision', 'recall', 'jaccard', 'roc_auc',
        'roc_auc_ovr', 'roc_auc_ovo', 'roc_auc_ovr_weighted', 'roc_auc_ovo_weighted'
    ]
    P_REPEATS, _REPEATS = 'repeats', 'Number of repetitions'
    P_SEED, _SEED = 'seed', 'Random seed'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outputPermutationImportanceRanking', 'Output report'

    def displayName(self) -> str:
        return 'Classifier feature ranking (permutation importance)'

    def shortDescription(self) -> str:
        return 'Permutation feature importance is a model inspection technique that is especially useful for non-linear or opaque estimators. ' \
               'The permutation feature importance is defined to be the decrease in a model score when a single feature value is randomly shuffled. ' \
               'This procedure breaks the relationship between the feature and the target, thus the drop in the model score is indicative of how much the model depends on the feature. ' \
               'This technique benefits from being model agnostic and can be calculated many times with different permutations of the feature.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CLASSIFIER, 'Classifier pickle file. '
                               'In case of an unfitted classifier, also specify a training dataset.'),
            (self._TRAIN_DATASET, 'Training dataset pickle file used for (re-)fitting the classifier. '
                                  'Can be skipped in case of a fitted classifier.'),
            (self._TEST_DATASET, 'Test dataset pickle file used for performance evaluation. '
                                 'If skipped, the training dataset is used.'),
            (self._EVALUATION_METRIC,
             'An evaluation metric to use. '
             'See Metrics and scoring: quantifying the quality of predictions for further information.'),
            (self._REPEATS, 'Number of times to permute a feature.'),
            (self._SEED, 'The seed for the random generator can be provided.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def helpLinks(self) -> List[Tuple[str, str]]:
        return [
            ('Metrics and scoring: quantifying the quality of predictions',
             'https://scikit-learn.org/stable/modules/model_evaluation.html#scoring-parameter'),
            ('Permutation feature importance',
             'https://scikit-learn.org/stable/modules/permutation_importance.html#permutation-importance')
        ]

    def group(self):
        return Group.Test.value + Group.FeatureSelection.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_CLASSIFIER, self._CLASSIFIER, extension='pkl')
        self.addParameterFile(
            self.P_TRAIN_DATASET, self._TRAIN_DATASET, extension=self.PickleFileExtension, optional=True, advanced=True
        )
        self.addParameterFile(
            self.P_TEST_DATASET, self._TEST_DATASET, extension=self.PickleFileExtension, optional=True, advanced=True
        )
        self.addParameterEnum(
            self.P_EVALUATION_METRIC, self._EVALUATION_METRIC, self.O_EVALUATION_METRIC, False,
            self.O_EVALUATION_METRIC.index('f1_macro'), False, True
        )
        self.addParameterInt(self.P_REPEATS, self._REPEATS, 10, False, 1, None, True)
        self.addParameterInt(self.P_SEED, self._SEED, None, True, 1, None, True)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:

        import matplotlib.pyplot as plt

        filenameClassifier = self.parameterAsFile(parameters, self.P_CLASSIFIER, context)
        filenameTrainSample = self.parameterAsFile(parameters, self.P_TRAIN_DATASET, context)
        filenameTestSample = self.parameterAsFile(parameters, self.P_TEST_DATASET, context)
        scoring = self.O_EVALUATION_METRIC[self.parameterAsInt(parameters, self.P_EVALUATION_METRIC, context)]
        repeats = self.parameterAsInt(parameters, self.P_REPEATS, context)
        seed = self.parameterAsInt(parameters, self.P_SEED, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            if filenameTrainSample is None:
                filenameTrainSample = filenameClassifier
            if filenameTestSample is None:
                filenameTestSample = filenameTrainSample
            refit = filenameTrainSample != filenameClassifier

            classifier = ClassifierDump(**Utils.pickleLoad(filenameClassifier)).classifier
            feedback.pushInfo(f'Load classifier: {classifier}')

            if refit:
                dump = ClassifierDump(**Utils.pickleLoad(filenameTrainSample))
                X, y, features = dump.X, dump.y, dump.features
                feedback.pushInfo(f'Load training dataset: X=array{list(X.shape)} y=array{list(dump.y.shape)}')
                feedback.pushInfo('Fit classifier')
                classifier.fit(X, y)

            # load test sample
            dump = ClassifierDump(**Utils.pickleLoad(filenameTestSample))
            X, y, features = dump.X, dump.y, dump.features
            feedback.pushInfo(f'Load test dataset: X=array{list(X.shape)} y=array{list(dump.y.shape)}')

            feedback.pushInfo('Evaluate permutation feature importance')
            from sklearn.inspection import permutation_importance
            r = permutation_importance(
                estimator=classifier, X=X, y=y.ravel(), scoring=scoring, n_repeats=repeats, random_state=seed
            )
            ordered = r.importances_mean.argsort()  # [::-1]

            # create plot
            figsizeX = 10
            figsizeY = len(features) * 0.15 + 1
            fig, ax = plt.subplots(figsize=(figsizeX, figsizeY))
            plt.xlabel(f'decrease in {scoring} score')
            ax.boxplot(r.importances[ordered].T,
                       vert=False, labels=np.array(features)[ordered]
                       )
            ax.set_title("Permutation Importances")
            fig.tight_layout()
            filenameFig = filename + '.fig.png'
            fig.savefig(filenameFig, format='png')

            ordered = ordered[::-1]
            values = np.array([r.importances_mean[ordered], r.importances_std[ordered]]).T.round(4).tolist()

            with \
                    open(filename, 'w') as fileHtml, \
                    open(filename + '.csv', 'w') as fileCsv:
                report = MultiReportWriter([HtmlReportWriter(fileHtml), CsvReportWriter(fileCsv)])
                report.writeHeader('Permutation importances')
                report.writeParagraph('Scoring function:', scoring)
                report.writeParagraph('Number of repetitions:', repeats)
                report.writeImage(basename(filenameFig))
                report.writeTable(
                    values,
                    'Permutation feature importance',
                    ['mean', 'standard deviation'],
                    np.array(features)[ordered].tolist(),
                )
                report.writeParagraph(
                    f'See {self.htmlLink("https://scikit-learn.org/stable/modules/permutation_importance.html#permutation-importance", "Permutation feature importance")} for further information.'
                )

            result = {self.P_OUTPUT_REPORT: filename}

            if openReport:
                webbrowser.open_new_tab(filename)

            self.toc(feedback, result)

            feature_subset_hierarchy = list()
            subset = list()
            for index in ordered:
                subset.append(int(index))
                feature_subset_hierarchy.append(subset.copy())

            dumpJson = {'features': features, 'feature_subset_hierarchy': feature_subset_hierarchy}
            Utils.jsonDump(dumpJson, filename + '.json')

        return result
