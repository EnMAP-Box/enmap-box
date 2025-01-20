import json
import webbrowser
from dataclasses import dataclass
from math import isnan
from os import makedirs
from os.path import exists, dirname
from typing import Dict, Any, List, Tuple

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.rasterizecategorizedvectoralgorithm import RasterizeCategorizedVectorAlgorithm
from enmapboxprocessing.algorithm.translatecategorizedrasteralgorithm import TranslateCategorizedRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.reportwriter import MultiReportWriter, HtmlReportWriter, CsvReportWriter
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsVectorLayer, \
    QgsProcessingException


@typechecked
class ClassificationPerformanceSimpleAlgorithm(EnMAPProcessingAlgorithm):
    P_CLASSIFICATION, _CLASSIFICATION = 'classification', 'Predicted classification layer'
    P_REFERENCE, _REFERENCE = 'reference', 'Observed categorized layer'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outClassificationPerformance', 'Output report'

    @classmethod
    def displayName(cls) -> str:
        return 'Classification layer accuracy report'

    def shortDescription(self) -> str:
        return 'Estimates map accuracy.\n' \
               'Observed and predicted categories are matched by name, if possible. ' \
               'Otherwise, categories are matched by order (in this case, a warning message is logged).'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CLASSIFICATION, 'A classification layer that is to be assessed.'),
            (self._REFERENCE, 'A categorized layer representing a (ground truth) observation sample.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def group(self):
        return Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_CLASSIFICATION, self._CLASSIFICATION)
        self.addParameterMapLayer(self.P_REFERENCE, self._REFERENCE)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        classification = self.parameterAsRasterLayer(parameters, self.P_CLASSIFICATION, context)
        reference = self.parameterAsLayer(parameters, self.P_REFERENCE, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # resample reference
            if isinstance(reference, QgsVectorLayer):
                feedback.pushInfo('Rasterize observed category layer')
                alg = RasterizeCategorizedVectorAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_CATEGORIZED_VECTOR: reference,
                    alg.P_GRID: classification,
                    alg.P_MAJORITY_VOTING: False,  # simple NN resampling
                    alg.P_OUTPUT_CATEGORIZED_RASTER: Utils.tmpFilename(filename, 'observation.tif')
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
                reference = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])
            elif isinstance(reference, QgsRasterLayer):
                alg = TranslateCategorizedRasterAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_CATEGORIZED_RASTER: reference,
                    alg.P_GRID: classification,
                    alg.P_MAJORITY_VOTING: False,
                    alg.P_OUTPUT_CATEGORIZED_RASTER: Utils.tmpFilename(filename, 'observation.vrt')
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
                reference = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])

            feedback.pushInfo('Read data')
            # Note that we can be sure that all pixel grids match!
            arrayReference = RasterReader(reference).array()[0]
            categoriesReference = Utils.categoriesFromPalettedRasterRenderer(reference.renderer())
            arrayPrediction = RasterReader(classification).array()[0]
            categoriesPrediction = Utils().categoriesFromRenderer(classification.renderer(), classification)
            # - get valid reference location
            valid = np.full_like(arrayReference, False, bool)
            for c in categoriesReference:
                np.logical_or(valid, arrayReference == c.value, out=valid)
            yReference = arrayReference[valid].astype(np.float32)
            yMap = arrayPrediction[valid].astype(np.float32)
            # - remap class ids by name
            yMapRemapped = yMap.copy()  # this initial state is correct for matching by order (see #845)
            classNamesMatching = list()
            for i, cP in enumerate(categoriesPrediction):
                found = False
                for cR in categoriesReference:
                    if cR.name == cP.name:
                        yMapRemapped[yMap == cP.value] = cR.value
                        found = True
                        classNamesMatching.append([cP.name, cR.name])
                if not found:
                    feedback.pushWarning(
                        f'predicted class "{categoriesPrediction[i].name}" not found in reference classes. '
                        f'class will be matched by order: '
                        f'"{cP.name}" -> "{categoriesReference[i].name}".'
                    )
                    classNamesMatching.append([cP.name, categoriesReference[i].name])

            yMap = yMapRemapped

            feedback.pushInfo('Estimate statistics and create report')
            classValues = [c.value for c in categoriesReference]
            classNames = [c.name for c in categoriesReference]
            if not np.isin(yMap, classValues).all():
                raise QgsProcessingException('Predicted values not matching reference classes.')
            stats = accuracyAssessment(yReference, yMap, classNames, classValues)

            self.writeReport(filename, stats, classNamesMatching)
            # dump json
            with open(filename + '.json', 'w') as file:
                file.write(json.dumps(stats.__dict__, indent=4))
            result = {self.P_OUTPUT_REPORT: filename}

            if openReport:
                webbrowser.open_new_tab(filename)

            self.toc(feedback, result)

        return result

    @classmethod
    def writeReport(
            cls, filename: str, stats: 'AccuracyAssessmentResult', classNamesMatching: list = None
    ):

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

        def confidenceIntervall(mean, se):
            alpha = 0.05
            return mean - 1.959963984540054 * alpha / 2. * se, mean + 1.959963984540054 * alpha / 2. * se

        if not exists(dirname(filename)):
            makedirs(dirname(filename))
        with open(filename, 'w') as fileHtml, open(filename + '.csv', 'w') as fileCsv:
            report = MultiReportWriter([HtmlReportWriter(fileHtml), CsvReportWriter(fileCsv)])
            report.writeHeader('Classification layer accuracy')

            report.writeParagraph(f'Sample size: {stats.sampleSize}')

            if classNamesMatching is not None:
                report.writeTable(classNamesMatching, 'Class matching', ['predicted', 'observed'])

            values = smartRound(stats.confusionMatrix, 2)
            report.writeTable(
                np.transpose(values).tolist(), 'Confusion matrix counts:',
                [f'({i + 1})' for i in range(len(stats.classNames))],
                [f'predicted {name} ({i + 1})' for i, name in enumerate(stats.classNames)]
            )

            values = smartRound([
                [stats.overallAccuracy, *confidenceIntervall(stats.overallAccuracy, stats.overallAccuracySe)]
            ], 4)
            report.writeTable(
                values, 'Overall accuracies',
                None,
                ['Overall accuracy'],
                [('Estimate', 1), ('95 % confidence interval', 2)]
            )

            values = list()
            for i in range(len(stats.classNames)):
                values.append(
                    [stats.usersAccuracy[i],
                     *confidenceIntervall(stats.usersAccuracy[i], stats.usersAccuracySe[i]),
                     stats.producersAccuracy[i],
                     *confidenceIntervall(stats.producersAccuracy[i], stats.producersAccuracySe[i]),
                     stats.f1[i],
                     *confidenceIntervall(stats.f1[i], stats.f1Se[i])]
                )
            values = smartRound(values, 4)
            report.writeTable(
                values, 'Class-wise accuracies',
                None,
                stats.classNames,
                [("User's accuracy", 1), ('95 % confidence interval', 2),
                 ("Producer's accuracy", 1), ('95 % confidence interval', 2),
                 ("F1-score", 1), ('95 % confidence interval', 2)]
            )


@typechecked()
@dataclass
class AccuracyAssessmentResult(object):
    sampleSize: int
    classNames: List[str]
    confusionMatrix: List[List[float]]
    overallAccuracy: float
    overallAccuracySe: float
    usersAccuracy: List[float]
    usersAccuracySe: List[float]
    producersAccuracy: List[float]
    producersAccuracySe: List[float]
    f1: List[float]
    f1Se: List[float]


@typechecked
def accuracyAssessment(
        observed: np.ndarray, predicted: np.ndarray, classNames: List[str], classValues: List[Any]
) -> AccuracyAssessmentResult:
    assert observed.ndim == 1
    assert predicted.ndim == 1
    assert observed.shape == predicted.shape

    sampleSize = observed.shape[0]
    report = classification_report(
        observed, predicted, labels=classValues, target_names=classNames, output_dict=True, zero_division=np.nan
    )
    confusionMatrix = confusion_matrix(observed, predicted, labels=classValues).tolist()
    nPredicted = np.sum(confusionMatrix, 0).tolist()
    nObserved = np.sum(confusionMatrix, 1).tolist()
    overallAccuracy = report['accuracy']
    usersAccuracy = [report[className]['precision'] for className in classNames]
    producersAccuracy = [report[className]['recall'] for className in classNames]
    f1Score = [report[className]['f1-score'] for className in classNames]

    def standardError(a, n):
        return np.sqrt(np.divide(a * (1 - a), n))

    overallAccuracySe = standardError(overallAccuracy, sampleSize)
    usersAccuracySe = [standardError(report[className]['precision'], n)
                       for className, n in zip(classNames, nPredicted)]
    producersAccuracySe = [standardError(report[className]['recall'], n)
                           for className, n in zip(classNames, nObserved)]

    def standardErrorF1(P, R, PSE, RSE):
        A = 2 * R ** 2 / np.add(P, R) ** 2
        B = 2 * P ** 2 / np.add(P, R) ** 2
        f1Var = A ** 2 * PSE ** 2 + B ** 2 * RSE ** 2
        return np.sqrt(f1Var)

    f1ScoreSe = [standardErrorF1(P, R, PSE, RSE)
                 for P, R, PSE, RSE in zip(usersAccuracy, producersAccuracy, usersAccuracySe, producersAccuracySe)]

    result = AccuracyAssessmentResult(
        sampleSize, classNames, confusionMatrix, overallAccuracy, overallAccuracySe, usersAccuracy, usersAccuracySe,
        producersAccuracy, producersAccuracySe, f1Score, f1ScoreSe
    )
    return result
