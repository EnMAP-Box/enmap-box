import inspect
import traceback
from operator import xor
from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromrasteralgorithm import \
    PrepareUnsupervisedDatasetFromRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException
from typeguard import typechecked


@typechecked
class FitTransformerAlgorithmBase(EnMAPProcessingAlgorithm):
    P_FEATURE_RASTER, _FEATURE_RASTER = 'featureRaster', 'Raster layer with features'
    P_SAMPLE_SIZE, _SAMPLE_SIZE = 'sampleSize', 'Sample size'
    P_DATASET, _DATASET = 'dataset', 'Training dataset'
    P_TRANSFORMER, _TRANSFORMER = 'transformer', 'Transformer'
    P_OUTPUT_TRANSFORMER, _OUTPUT_TRANSFORMER = 'outputTransformer', 'Output transformer'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._TRANSFORMER, self.helpParameterCode()),
            (self._FEATURE_RASTER, 'Raster layer with feature data X used for fitting the transformer. '
                                   'Mutually exclusive with parameter: Training dataset'),
            (self._SAMPLE_SIZE, 'Approximate number of samples drawn from raster. '
                                'If 0, whole raster will be used. '
                                'Note that this is only a hint for limiting the number of rows and columns.'),
            (self._DATASET, 'Training dataset pickle file used for fitting the transformer. '
                            'Mutually exclusive with parameter: Raster layer with features'),
            (self._OUTPUT_TRANSFORMER, self.PickleFileDestination)
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
        return Group.Test.value + Group.Transformation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterCode(self.P_TRANSFORMER, self._TRANSFORMER, self.defaultCodeAsString())
        self.addParameterRasterLayer(self.P_FEATURE_RASTER, self._FEATURE_RASTER, None, True)
        self.addParameterInt(self.P_SAMPLE_SIZE, self._SAMPLE_SIZE, 1000, True, 0, None)
        self.addParameterUnsupervisedDataset(self.P_DATASET, self._DATASET, None, True, True)
        self.addParameterFileDestination(self.P_OUTPUT_TRANSFORMER, self._OUTPUT_TRANSFORMER, self.PickleFileFilter)

    def defaultCodeAsString(self):
        try:
            lines = [line[8:] for line in inspect.getsource(self.code).split('\n')][1:-2]
        except OSError:
            lines = ['']
        lines = '\n'.join(lines)
        return lines

    def parameterAsTransformer(self, parameters: Dict[str, Any], name, context: QgsProcessingContext):
        namespace = dict()
        code = self.parameterAsString(parameters, name, context)
        exec(code, namespace)
        return namespace['transformer']

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        valid, message = super().checkParameterValues(parameters, context)
        if not valid:
            return valid, message
        # check code
        try:
            self.parameterAsTransformer(parameters, self.P_TRANSFORMER, context)
        except Exception:
            return False, traceback.format_exc()
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:

        raster = self.parameterAsRasterLayer(parameters, self.P_FEATURE_RASTER, context)
        sampleSize = self.parameterAsInt(parameters, self.P_SAMPLE_SIZE, context)
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_TRANSFORMER, context)
        transformer = self.parameterAsTransformer(parameters, self.P_TRANSFORMER, context)

        if not xor(raster is not None, filenameDataset is not None):
            raise QgsProcessingException(
                f'Mutually exclusive parameters, select either {self._FEATURE_RASTER}, or {self._DATASET}')

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            if filenameDataset is None:
                alg = PrepareUnsupervisedDatasetFromRasterAlgorithm()
                parameters = {
                    alg.P_FEATURE_RASTER: raster,
                    alg.P_SAMPLE_SIZE: sampleSize,
                    alg.P_OUTPUT_DATASET: Utils.tmpFilename(filename, 'dataset.pkl')
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
                filenameDataset = parameters[alg.P_OUTPUT_DATASET]

            dump = TransformerDump.fromDict(Utils.pickleLoad(filenameDataset))
            feedback.pushInfo(
                f'Load training dataset: X=array{list(dump.X.shape)}')
            feedback.pushInfo('Fit transformer')
            transformer.fit(dump.X)

            dump = TransformerDump(dump.features, dump.X, transformer)
            Utils.pickleDump(dump.__dict__, filename)

            result = {self.P_OUTPUT_TRANSFORMER: filename}
            self.toc(feedback, result)

        return result
