import inspect
import traceback
from io import StringIO
from typing import Dict, Any, List, Tuple

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromjsonalgorithm import \
    PrepareClassificationDatasetFromJsonAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback


@typechecked
class FitClassifierAlgorithmBase(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Training dataset'
    P_CLASSIFIER, _CLASSIFIER = 'classifier', 'Classifier'
    P_OUTPUT_CLASSIFIER, _OUTPUT_CLASSIFIER = 'outputClassifier', 'Output classifier'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'Training dataset pickle file used for fitting the classifier. '
                            'If not specified, an unfitted classifier is created.'),
            (self._CLASSIFIER, self.helpParameterCode()),
            (self._OUTPUT_CLASSIFIER, self.PickleFileDestination)
        ]

    def displayName(self) -> str:
        raise NotImplementedError()

    def shortDescription(self) -> str:
        raise NotImplementedError()

    def code(self):
        raise NotImplementedError()

    def helpParameterCode(self) -> str:
        raise NotImplementedError()

    def group(self):
        return Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterCode(self.P_CLASSIFIER, self._CLASSIFIER, self.defaultCodeAsString())
        self.addParameterClassificationDataset(self.P_DATASET, self._DATASET, None, True)
        self.addParameterFileDestination(self.P_OUTPUT_CLASSIFIER, self._OUTPUT_CLASSIFIER, self.PickleFileFilter)

    def defaultCodeAsString(self):
        try:
            lines = [line[8:] for line in inspect.getsource(self.code).split('\n')][1:-2]
        except OSError:
            lines = ['']
        lines = '\n'.join(lines)
        return lines

    def parameterAsClassifier(self, parameters: Dict[str, Any], name, context: QgsProcessingContext):
        namespace = dict()
        code = self.parameterAsString(parameters, name, context)
        exec(code, namespace)
        return namespace['classifier']

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        valid, message = super().checkParameterValues(parameters, context)
        if not valid:
            return valid, message
        # check code
        try:
            self.parameterAsClassifier(parameters, self.P_CLASSIFIER, context)
        except Exception:
            return False, traceback.format_exc()
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_CLASSIFIER, context)
        classifier = self.parameterAsClassifier(parameters, self.P_CLASSIFIER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            if filenameDataset is not None:
                if filenameDataset.endswith('.json'):
                    alg = PrepareClassificationDatasetFromJsonAlgorithm()
                    parameters = {
                        alg.P_JSON_FILE: filenameDataset,
                        alg.P_OUTPUT_DATASET: Utils.tmpFilename(filename, 'dataset.pkl')
                    }
                    self.runAlg(alg, parameters, None, feedback2, context, True)
                    dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
                else:
                    dump = ClassifierDump(**Utils.pickleLoad(filenameDataset))
                feedback.pushInfo(
                    f'Load training dataset: X=array{list(dump.X.shape)} y=array{list(dump.y.shape)} categories={[c.name for c in dump.categories]}')
                feedback.pushInfo('Fit classifier')

                try:
                    classifier.fit(dump.X, dump.y.ravel(), log_cout=StringIO(), log_cerr=StringIO())  # fixes issue #790
                except TypeError:
                    classifier.fit(dump.X, dump.y.ravel())

            else:

                feedback.pushInfo('Store unfitted classifier')
                dump = ClassifierDump(None, None, None, None, classifier)

            dump = ClassifierDump(dump.categories, dump.features, dump.X, dump.y, classifier)
            Utils.pickleDump(dump.__dict__, filename)

            result = {self.P_OUTPUT_CLASSIFIER: filename}
            self.toc(feedback, result)

        return result
