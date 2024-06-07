import webbrowser
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.classificationperformancesimplealgorithm import \
    ClassificationPerformanceSimpleAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsMapLayer, QgsProcessingException)


@typechecked
class ClassifierPerformanceAlgorithm(EnMAPProcessingAlgorithm):
    P_CLASSIFIER, _CLASSIFIER = 'classifier', 'Classifier'
    P_DATASET, _DATASET = 'dataset', 'Test dataset'
    P_NFOLD, _NFOLD = 'nfold', 'Number of cross-validation folds'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outputClassifierPerformance', 'Output report'

    def displayName(self) -> str:
        return 'Classifier performance report'

    def shortDescription(self) -> str:
        return 'Evaluates classifier performance.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CLASSIFIER, 'Classifier pickle file.'),
            (self._DATASET, 'Test dataset pickle file used for assessing the classifier performance.'),
            (self._NFOLD, 'The number of folds (n>=2) used for assessing cross-validation performance.\n'
                          'If not specified (default), simple test performance is assessed.\n'
                          'If set to a value of 1, out-of-bag (OOB) performance is assessed. '
                          'Note that OOB estimates are only supported by some classifiers, '
                          'e.g. the Random Forest Classifier.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def group(self):
        return Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterPickleFile(self.P_CLASSIFIER, self._CLASSIFIER)
        self.addParameterClassificationDataset(self.P_DATASET, self._DATASET)
        self.addParameterInt(self.P_NFOLD, self._NFOLD, None, True, 1, 100, True)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameClassifier = self.parameterAsFile(parameters, self.P_CLASSIFIER, context)
        filenameSample = self.parameterAsFile(parameters, self.P_DATASET, context)
        nfold = self.parameterAsInt(parameters, self.P_NFOLD, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            classifier = ClassifierDump(**Utils.pickleLoad(filenameClassifier)).classifier
            sample = ClassifierDump(**Utils.pickleLoad(filenameSample))
            feedback.pushInfo(f'Load classifier: {classifier}')
            feedback.pushInfo(f'Load sample data: X{list(sample.X.shape)} y{list(sample.y.shape)}')

            if nfold is None:
                feedback.pushInfo('Evaluate classifier test performance')
                y2 = classifier.predict(sample.X)
            elif nfold == 1:
                feedback.pushInfo('Evaluate classifier out-of-bag (OOB) performance')
                classifier.fit(sample.X, sample.y.ravel())
                assert classifier.classes_.tolist() == list(range(1, len(classifier.classes_) + 1))
                try:
                    y2 = np.argmax(classifier.oob_decision_function_, axis=1) + 1
                except Exception:
                    raise QgsProcessingException('classifier not supporting out-of-bag estimates\n' + str(classifier))
            else:
                feedback.pushInfo('Evaluate cross-validation performance')
                from sklearn.model_selection import cross_val_predict
                y2 = cross_val_predict(classifier, X=sample.X, y=sample.y.ravel(), cv=nfold)

            # prepare raster layers
            y2 = np.reshape(y2, (1, -1, 1))
            reference = Driver(Utils.tmpFilename(filename, 'reference.tif')).createFromArray([sample.y])
            prediction = Driver(Utils.tmpFilename(filename, 'prediction.tif')).createFromArray(y2)
            reference.close()
            reference = QgsRasterLayer(reference.source())
            renderer = Utils.palettedRasterRendererFromCategories(reference.dataProvider(), 1, sample.categories)
            reference.setRenderer(renderer)
            reference.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)
            prediction.close()
            prediction = QgsRasterLayer(prediction.source())
            renderer = Utils.palettedRasterRendererFromCategories(prediction.dataProvider(), 1, sample.categories)
            prediction.setRenderer(renderer)
            prediction.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)
            # eval
            alg = ClassificationPerformanceSimpleAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_CLASSIFICATION: prediction,
                alg.P_REFERENCE: reference,
                alg.P_OPEN_REPORT: False,
                alg.P_OUTPUT_REPORT: filename,
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {self.P_OUTPUT_REPORT: filename}

            if openReport:
                webbrowser.open_new_tab(filename)

            self.toc(feedback, result)

        return result
