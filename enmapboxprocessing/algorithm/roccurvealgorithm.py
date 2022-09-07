import webbrowser
from collections import OrderedDict
from dataclasses import dataclass
from math import isnan
from os import makedirs
from os.path import exists, dirname
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.algorithm.rasterizecategorizedvectoralgorithm import RasterizeCategorizedVectorAlgorithm
from enmapboxprocessing.algorithm.translatecategorizedrasteralgorithm import TranslateCategorizedRasterAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.reportwriter import MultiReportWriter, HtmlReportWriter, CsvReportWriter
from enmapboxprocessing.typing import Categories
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsVectorLayer, \
    QgsProcessingException
from typeguard import typechecked


@typechecked
class RocCurveAlgorithm(EnMAPProcessingAlgorithm):
    P_PROBABILITY, _PROBABILITY = 'regression', 'Class probability layer'
    P_REFERENCE, _REFERENCE = 'reference', 'Observed categorized layer'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outRocCurve', 'Output report'

    @classmethod
    def displayName(cls) -> str:
        return 'Receiver operating characteristic (ROC) and detection error tradeoff (DET) curves'

    def shortDescription(self) -> str:
        return 'Compute receiver operating characteristic (ROC) and detection error tradeoff (DET) curves.\n' \
               'For more details see the Scikit-Learn user guide: ' \
               '<a href="https://scikit-learn.org/stable/modules/model_evaluation.html#receiver-operating-characteristic-roc">' \
               'Receiver operating characteristic (ROC)</a> and ' \
               '<a href="https://scikit-learn.org/stable/modules/model_evaluation.html#detection-error-tradeoff-det">' \
               'Detection error tradeoff (DET)</a>.\n' \
               'Note that observed classes and predicted class probabilities are matched by name.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._PROBABILITY, 'A class probability layer that is to be assessed.'),
            (self._REFERENCE, 'A categorized layer representing a (ground truth) observation sample.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Regression.value

    def checkTargets(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        prediction = self.parameterAsRasterLayer(parameters, self.P_PROBABILITY, context)
        reference = self.parameterAsLayer(parameters, self.P_REFERENCE, context)
        targetsPrediction = Utils.targetsFromLayer(prediction)
        categoriesReference = Utils.categoriesFromRenderer(reference.renderer())
        for tR in categoriesReference:
            for tP in targetsPrediction:
                if tR.name == tP.name:
                    return True, ''  # good, we found the reference class
            return False, f'Observed class "{tR.name}" not found in predicted class probabilities.'
        for tP in targetsPrediction:
            for tR in categoriesReference:
                if tR.name == tP.name:
                    return True, ''  # good, we found the map class
            return False, f'Predicted class probability "{tP.name}" not found in observed classes.'
        return False, 'Empty class list.'

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        checks = [
            self.checkParameterRasterRegression(parameters, self.P_PROBABILITY, context),
            self.checkParameterMapClassification(parameters, self.P_REFERENCE, context),
        ]
        for valid, message in checks:
            if not valid:
                return valid, message

        valid, message = self.checkTargets(parameters, context)
        if not valid:
            return valid, message

        return True, ''

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_PROBABILITY, self._PROBABILITY)
        self.addParameterMapLayer(self.P_REFERENCE, self._REFERENCE)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        probability = self.parameterAsRasterLayer(parameters, self.P_PROBABILITY, context)
        reference = self.parameterAsLayer(parameters, self.P_REFERENCE, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            categoriesReference = Utils.categoriesFromRenderer(reference.renderer())
            targetsPrediction = Utils.targetsFromLayer(probability)

            # resample reference
            if isinstance(reference, QgsVectorLayer):
                feedback.pushInfo('Rasterize observed category layer')
                alg = RasterizeCategorizedVectorAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_CATEGORIZED_VECTOR: reference,
                    alg.P_GRID: probability,
                    alg.P_MAJORITY_VOTING: False,  # simple NN resampling
                    alg.P_OUTPUT_CATEGORIZED_RASTER: Utils.tmpFilename(filename, 'observation.tif')
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
                reference = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])
                categoriesReference = Utils.categoriesFromRenderer(reference.renderer())
            elif isinstance(reference, QgsRasterLayer):
                alg = TranslateCategorizedRasterAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_CATEGORIZED_RASTER: reference,
                    alg.P_GRID: probability,
                    alg.P_MAJORITY_VOTING: False,
                    alg.P_OUTPUT_CATEGORIZED_RASTER: Utils.tmpFilename(filename, 'observation.vrt')
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
                reference = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])

            # prepare prediction (reorder bands)
            targetNames = [t.name for t in categoriesReference]
            bandNames = [t.name for t in targetsPrediction]
            bandList = [bandNames.index(targetName) + 1 for targetName in targetNames]
            alg = TranslateRasterAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_RASTER: probability,
                alg.P_BAND_LIST: bandList,
                alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'probability.vrt')
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)
            probability = QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER])

            # read data and create ROC curves
            feedback.pushInfo('Read data and create ROC curves')
            # Note that we can be sure that:
            #   - all pixel grids match
            #   - target bands match
            readerObserved = RasterReader(reference)
            readerPredicted = RasterReader(probability)
            rocCurves = OrderedDict()
            detCurves = OrderedDict()
            arrayObserved = readerObserved.array(bandList=[1])
            maskArrayObserved = np.full_like(arrayObserved, False, bool)
            for c in categoriesReference:
                np.logical_or(maskArrayObserved, np.equal(arrayObserved, c.value), out=maskArrayObserved)
            yObserved = arrayObserved[0][maskArrayObserved[0]]
            for bandNo, category in enumerate(categoriesReference, 1):
                arrayPredicted = readerPredicted.array(bandList=[bandNo])
                maskArrayPredicted = readerPredicted.maskArray(arrayPredicted, bandList=[bandNo])
                ok = maskArrayPredicted[0][maskArrayObserved[0]].all()
                if not ok:
                    raise QgsProcessingException('Observed missing pixel predictions.')
                yPredicted = arrayPredicted[0][maskArrayObserved[0]].astype(np.float32)
                yObservedBinary = np.equal(yObserved, category.value)
                rocCurves[category.name] = rocCurve(yObservedBinary, yPredicted)
                detCurves[category.name] = detCurve(yObservedBinary, yPredicted)

            Utils.jsonDump(rocCurves, filename + '.json')
            feedback.pushInfo('Create report')
            self.writeReport(filename, rocCurves, detCurves, categoriesReference)
            result = {self.P_OUTPUT_REPORT: filename}

            if openReport:
                webbrowser.open_new_tab(filename)

            self.toc(feedback, result)

        return result

    @classmethod
    def writeReport(cls, filename: str, rocCurves: Dict[str, 'RocCurveResult'], detCurves: Dict[str, 'DetCurveResult'],
                    categories: Categories):

        def smartRound(obj, ndigits):
            if isinstance(obj, list):
                return [smartRound(item, ndigits) for item in obj]
            else:
                obj = round(obj, ndigits)
                if isnan(obj):
                    return obj
                if obj == int(obj):
                    obj = int(obj)
                return obj

        if not exists(dirname(filename)):
            makedirs(dirname(filename))

        with open(filename, 'w') as fileHtml, open(filename + '.csv', 'w') as fileCsv:
            report = MultiReportWriter([HtmlReportWriter(fileHtml), CsvReportWriter(fileCsv)])
            report.writeHeader(
                'Receiver Operating Characteristic (ROC) and  and Detection Error Tradeoff (DET) curves report'
            )

            report.writeParagraph(f'Sample size: {list(rocCurves.values())[0].n} px')

            report.writeSubHeader('Probability metrics')

            keys = ['rocAucScore']
            rowHeaders = ['Area under the ROC curve (AUC)']
            values = [[smartRound(getattr(rocCurve, key), 4) for rocCurve in rocCurves.values()] for key in keys]
            report.writeTable(values, None, list(rocCurves), rowHeaders)

            report.writeSubHeader('Receiver Operating Characteristic (ROC) curves')

            from matplotlib import pyplot

            fig, ax = pyplot.subplots(facecolor='white', figsize=(9, 6))
            for category in categories:
                rocCurve = rocCurves[category.name]
                pyplot.plot(rocCurve.fpr, rocCurve.tpr, label=category.name, color=category.color)
            ax.set_xlabel('False Positive Rate')
            ax.set_ylabel('True Positive Rate')
            pyplot.plot([0, 1], [0, 1], 'k--')
            pyplot.legend(loc="lower right")
            fig.tight_layout()
            filenameFig = filename + '.roc_curves.png'
            fig.savefig(filenameFig, format='png')
            pyplot.close()
            report.writeImage(filenameFig)

            report.writeSubHeader('Detection Error Tradeoff (DET) curves')

            fig, ax = pyplot.subplots(facecolor='white', figsize=(9, 6))
            for category in categories:
                detCurve = detCurves[category.name]
                pyplot.plot(detCurve.fpr, detCurve.tpr, label=category.name, color=category.color)
            ax.set_xlabel('False Positive Rate')
            ax.set_ylabel('False Negative Rate')
            pyplot.legend(loc="upper right")
            fig.tight_layout()
            filenameFig = filename + '.det_curves.png'
            fig.savefig(filenameFig, format='png')
            pyplot.close()
            report.writeImage(filenameFig)


@typechecked
@dataclass
class RocCurveResult(object):
    n: int
    fpr: np.ndarray
    tpr: np.ndarray
    thresholds: np.ndarray
    rocAucScore: float


@typechecked
@dataclass
class DetCurveResult(object):
    n: int
    fpr: np.ndarray
    tpr: np.ndarray
    thresholds: np.ndarray


@typechecked
def rocCurve(yObserved: np.ndarray, yPredicted: np.ndarray):
    from sklearn.metrics import roc_curve, roc_auc_score
    assert yObserved.ndim == 1
    assert yPredicted.ndim == 1
    assert len(yObserved) == len(yPredicted)

    n = len(yObserved)
    fpr, tpr, thresholds = roc_curve(yObserved, yPredicted)
    rocAucScore = roc_auc_score(yObserved, yPredicted)
    return RocCurveResult(n, fpr, tpr, thresholds, float(rocAucScore))


@typechecked
def detCurve(yObserved: np.ndarray, yPredicted: np.ndarray):
    from sklearn.metrics import det_curve
    assert yObserved.ndim == 1
    assert yPredicted.ndim == 1
    assert len(yObserved) == len(yPredicted)

    n = len(yObserved)
    fpr, tpr, thresholds = det_curve(yObserved, yPredicted)
    return DetCurveResult(n, fpr, tpr, thresholds)
