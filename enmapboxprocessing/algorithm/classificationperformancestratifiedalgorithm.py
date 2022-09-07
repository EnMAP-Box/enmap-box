import json
import webbrowser
from collections import defaultdict
from dataclasses import dataclass
from math import isnan
from os import makedirs
from os.path import exists, dirname
from typing import Dict, Any, List, Tuple, Iterable

import numpy as np

from enmapboxprocessing.algorithm.rasterizecategorizedvectoralgorithm import RasterizeCategorizedVectorAlgorithm
from enmapboxprocessing.algorithm.translatecategorizedrasteralgorithm import TranslateCategorizedRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.reportwriter import HtmlReportWriter, CsvReportWriter, MultiReportWriter
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsVectorLayer, QgsRasterLayer, QgsUnitTypes)
from typeguard import typechecked


@typechecked
class ClassificationPerformanceStratifiedAlgorithm(EnMAPProcessingAlgorithm):
    P_CLASSIFICATION, _CLASSIFICATION = 'classification', 'Predicted classification layer'
    P_REFERENCE, _REFERENCE = 'reference', 'Observed categorized layer'
    P_STRATIFICATION, _STRATIFICATION = 'stratification', 'Stratification layer'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outClassificationPerformance', 'Output report'

    @classmethod
    def displayName(cls) -> str:
        return 'Classification layer accuracy and area report (for stratified random sampling)'

    def shortDescription(self) -> str:
        return 'Estimates map accuracy and area proportions for stratified random sampling as described in ' \
               'Stehman (2014): https://doi.org/10.1080/01431161.2014.930207. \n' \
               'Observed and predicted categories are matched by name.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CLASSIFICATION, 'A classification layer that is to be assessed.'),
            (self._REFERENCE, 'A categorized layer representing a (ground truth) observation sample, '
                              'that was aquired using a stratified random sampling approach.'),
            (self._STRATIFICATION, 'A stratification layer that was used for drawing the observation sample. '
                                   'If not defined, the classification layer is used as stratification layer.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Classification.value

    def checkCategories(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        classification = self.parameterAsRasterLayer(parameters, self.P_CLASSIFICATION, context)
        reference = self.parameterAsLayer(parameters, self.P_REFERENCE, context)
        if isinstance(reference, QgsVectorLayer):
            categoriesReference = Utils.categoriesFromCategorizedSymbolRenderer(reference.renderer())
        elif isinstance(reference, QgsRasterLayer):
            categoriesReference = Utils.categoriesFromPalettedRasterRenderer(reference.renderer())
        else:
            assert 0
        categoriesPrediction = Utils.categoriesFromPalettedRasterRenderer(classification.renderer())
        for cR in categoriesReference:
            for cP in categoriesPrediction:
                if cR.name == cP.name:
                    return True, ''  # good, we found the reference class
            return False, f'Observed category "{cR.name}" not found in predicted categories.'
        for cP in categoriesPrediction:
            for cR in categoriesReference:
                if cR.name == cP.name:
                    return True, ''  # good, we found the map class
            return False, f'Predicted category "{cP.name}" not found in observed categories.'
        return False, 'Empty category list.'

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        checks = [
            self.checkParameterRasterClassification(parameters, self.P_CLASSIFICATION, context),
            self.checkParameterMapClassification(parameters, self.P_REFERENCE, context),
            self.checkParameterRasterClassification(parameters, self.P_STRATIFICATION, context),
        ]
        for valid, message in checks:
            if not valid:
                return valid, message

        valid, message = self.checkCategories(parameters, context)
        if not valid:
            return valid, message

        return True, ''

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_CLASSIFICATION, self._CLASSIFICATION)
        self.addParameterMapLayer(self.P_REFERENCE, self._REFERENCE)
        self.addParameterMapLayer(self.P_STRATIFICATION, self._STRATIFICATION, optional=True)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        classification = self.parameterAsRasterLayer(parameters, self.P_CLASSIFICATION, context)
        reference = self.parameterAsLayer(parameters, self.P_REFERENCE, context)
        stratification = self.parameterAsRasterLayer(parameters, self.P_STRATIFICATION, context)
        if stratification is None:
            stratification = classification
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

            # resample stratification
            alg = TranslateCategorizedRasterAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_CATEGORIZED_RASTER: stratification,
                alg.P_GRID: classification,
                alg.P_MAJORITY_VOTING: False,
                alg.P_OUTPUT_CATEGORIZED_RASTER: Utils.tmpFilename(filename, 'stratification.tif')
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)
            stratification = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])

            feedback.pushInfo('Read data')
            # Note that we can be sure that all pixel grids match!
            arrayReference = RasterReader(reference).array()[0]
            categoriesReference = Utils.categoriesFromPalettedRasterRenderer(reference.renderer())
            arrayPrediction = RasterReader(classification).array()[0]
            categoriesPrediction = Utils.categoriesFromPalettedRasterRenderer(classification.renderer())
            arrayStratification = RasterReader(stratification).array()[0]
            categoriesStratification = Utils.categoriesFromPalettedRasterRenderer(stratification.renderer())
            # - get valid reference location
            valid = np.full_like(arrayReference, False, bool)
            for c in categoriesReference:
                np.logical_or(valid, arrayReference == c.value, out=valid)
            yReference = arrayReference[valid].astype(np.float32)
            yMap = arrayPrediction[valid].astype(np.float32)
            # - remap class ids by name
            yMapRemapped = np.zeros_like(yMap)
            for cP in categoriesPrediction:
                for cR in categoriesReference:
                    if cR.name == cP.name:
                        yMapRemapped[yMap == cP.value] = cR.value
            yMap = yMapRemapped
            # - prepare strata
            stratum = arrayStratification[valid]
            h_all, N_h_all = np.unique(arrayStratification, return_counts=True)
            h = list()
            N_h = list()
            for i, category in enumerate(categoriesStratification):
                if category.value not in h_all:
                    continue
                h.append(category.value)
                N_h.append(N_h_all[i])

            feedback.pushInfo('Estimate statistics and create report')
            classValues = [c.value for c in categoriesReference]
            classNames = [c.name for c in categoriesReference]
            stats = stratifiedAccuracyAssessment(stratum, yReference, yMap, h, N_h, classValues, classNames)
            pixelUnits = QgsUnitTypes.toString(classification.crs().mapUnits())
            pixelArea = classification.rasterUnitsPerPixelX() * classification.rasterUnitsPerPixelY()
            self.writeReport(filename, stats, pixelUnits=pixelUnits, pixelArea=pixelArea)
            # dump json
            with open(filename + '.json', 'w') as file:
                file.write(json.dumps(stats.__dict__, indent=4))
            result = {self.P_OUTPUT_REPORT: filename}

            if openReport:
                webbrowser.open_new_tab(filename)

            self.toc(feedback, result)

        return result

    @classmethod
    def writeReport(cls, filename: str, stats: 'StratifiedAccuracyAssessmentResult', pixelUnits='pixel', pixelArea=1.):

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

        if pixelUnits == 'degrees':
            pixelUnits = 'pixel'
        if pixelUnits != 'pixel':
            pixelUnits = 'square ' + pixelUnits

        def confidenceIntervall(mean, se):
            alpha = 0.05
            return mean - 1.959963984540054 * alpha / 2. * se, mean + 1.959963984540054 * alpha / 2. * se

        if not exists(dirname(filename)):
            makedirs(dirname(filename))
        with open(filename, 'w') as fileHtml, open(filename + '.csv', 'w') as fileCsv:
            report = MultiReportWriter([HtmlReportWriter(fileHtml), CsvReportWriter(fileCsv)])
            report.writeHeader('Classification layer accuracy and area report')

            report.writeParagraph(f'Sample size: {stats.n} px')
            report.writeParagraph(f'Area size: {smartRound(stats.N, 2)} {pixelUnits}')

            values = smartRound(stats.confusion_matrix_counts, 2)
            report.writeTable(
                values, 'Adjusted confusion matrix counts: predicted (rows) vs. observed (columns)',
                [f'({i + 1})' for i in range(len(stats.class_names))],
                [f'{name} ({i + 1})' for i, name in enumerate(stats.class_names)]
            )

            values = smartRound(stats.confusion_matrix_proportions, 4)
            report.writeTable(
                values, 'Adjusted confusion matrix area proportions: predicted (rows) vs. observed (columns)',
                [f'({i + 1})' for i in range(len(stats.class_names))],
                stats.class_names
            )

            values = smartRound([
                [stats.overall_accuracy, *confidenceIntervall(stats.overall_accuracy, stats.overall_accuracy_se)]
            ], 4)
            report.writeTable(
                values, 'Overall accuracies',
                None,
                ['Overall accuracy'],
                [('Estimate', 1), ('95 % confidence interval', 2)]
            )

            values = list()
            for i in range(len(stats.class_names)):
                values.append(
                    [stats.users_accuracy[i],
                     *confidenceIntervall(stats.users_accuracy[i], stats.users_accuracy_se[i]),
                     stats.producers_accuracy[i],
                     *confidenceIntervall(stats.producers_accuracy[i], stats.producers_accuracy_se[i]),
                     stats.f1[i],
                     *confidenceIntervall(stats.f1[i], stats.f1_se[i])]
                )
            values = smartRound(values, 4)
            report.writeTable(
                values, 'Class-wise accuracies',
                None,
                stats.class_names,
                [("User's accuracy", 1), ('95 % confidence interval', 2),
                 ("Producer's accuracy", 1), ('95 % confidence interval', 2),
                 ("F1-score", 1), ('95 % confidence interval', 2)]
            )

            values = list()
            for i in range(len(stats.class_names)):
                values.append(
                    [stats.area_proportion[i],
                     *confidenceIntervall(stats.area_proportion[i], stats.area_proportion_se[i]),
                     stats.area_proportion[i] * stats.N * pixelArea,
                     *confidenceIntervall(stats.area_proportion[i] * stats.N * pixelArea,
                                          stats.area_proportion_se[i] * stats.N * pixelArea)],
                )
            values = np.round(values, 4)
            values[:, -3:] = np.round(values[:, -3:], 2)
            values = smartRound(values.tolist(), 4)
            report.writeTable(
                values, 'Class-wise proportion and area estimates',
                None,
                stats.class_names,
                [('Proportion', 1), ('95 % confidence interval', 2),
                 (f'Area [{pixelUnits}]', 1), ('95 % confidence interval', 2)]
            )

            report.writeParagraph(
                'Implementation is based on: '
                'Stehman, S. V., 2014. '
                'Estimating area and map accuracy for stratified random sampling when the strata are different '
                'from the map classes. '
                'Int. J. Remote Sens. 35, 4923-4939, '
                '<a href="https://doi.org/10.1080/01431161.2014.930207">https://doi.org/10.1080/01431161.2014.930207</a>'
            )


@typechecked()
@dataclass
class StratifiedAccuracyAssessmentResult(object):
    N: float  # total area sum(N_h)
    n: int  # sample size
    class_names: List[str]
    classes: List[Any]
    confusion_matrix_proportions: List[List[float]]  # error matrix (sums to 1)
    confusion_matrix_counts: List[List[float]]  # adjusted confusion matrix counts
    overall_accuracy: float
    overall_accuracy_se: float
    area_proportion: List[float]
    area_proportion_se: List[float]
    users_accuracy: List[float]
    users_accuracy_se: List[float]
    producers_accuracy: List[float]
    producers_accuracy_se: List[float]
    f1: List[float]
    f1_se: List[float]


@typechecked
def stratifiedAccuracyAssessment(
        stratum: Iterable, reference: Iterable, map: Iterable, h: Iterable, N_h: Iterable, classValues, classNames
):
    stats = aa_stratified(stratum, reference, map, h, N_h, classValues)
    return StratifiedAccuracyAssessmentResult(N=float(sum(N_h)), n=len(reference), class_names=classNames, **stats)


# Implementation is based on:
#    Stehman, S. V., 2014.
#    Estimating area and map accuracy for stratified random sampling when the strata are different from the map classes.
#    Int. J. Remote Sens. 35, 4923-4939.
#    https://doi.org/10.1080/01431161.2014.930207
#
# Function naming and signatures are inspired by an R implementation provided by Dirk Pflugmacher:
#    https://scm.cms.hu-berlin.de/pflugmad/mapac/-/tree/master/R

@typechecked
def aa_stratified(
        stratum: Iterable, reference: Iterable, map: Iterable, h: Iterable, N_h: Iterable, classes=None
):
    stratum = np.array(stratum)
    reference = np.array(reference)
    map = np.array(map)
    h = np.array(h)
    N_h = np.array(N_h, dtype=np.float64)

    assert len(stratum) == len(reference) == len(map)
    assert len(h) == len(N_h)
    assert set(h) == set(stratum), f'empty strata detected: {set(h) - set(stratum)}'

    # determine class labels
    if classes is None:
        classes = np.unique(map)

    stats = defaultdict(list)
    stats['classes'] = list(classes)

    # adjusted confusion matrix area proportions (sums to 1).
    cmp = np.zeros((len(classes), len(classes)))
    for i in range(len(classes)):
        for j in range(len(classes)):
            y_u = np.logical_and(map == classes[i], reference == classes[j])
            R, R_SE = aa_estimator_stratified(stratum, y_u, h, N_h)
            cmp[i, j] = R
    stats['confusion_matrix_proportions'] = cmp.tolist()

    # adjusted confusion matrix counts
    stats['confusion_matrix_counts'] = (cmp * len(reference)).tolist()

    # overall accuracy
    oa, oa_se = aa_estimator_stratified(stratum, map == reference, h, N_h)
    stats['overall_accuracy'] = oa
    stats['overall_accuracy_se'] = oa_se

    for i in range(len(classes)):
        # area proportion
        R, R_SE = aa_estimator_stratified(stratum, reference == classes[i], h, N_h)
        stats['area_proportion'].append(R)
        stats['area_proportion_se'].append(R_SE)

        # user's accuracy
        x_u = map == classes[i]
        y_u = np.logical_and(reference == classes[i], map == classes[i])
        ua, ua_se = aa_estimator_stratified_ratio(stratum, x_u, y_u, h, N_h)
        stats['users_accuracy'].append(ua)
        stats['users_accuracy_se'].append(ua_se)

        # producer's accuracy
        x_u = reference == classes[i]
        y_u = np.logical_and(reference == classes[i], map == classes[i])
        pa, pa_se = aa_estimator_stratified_ratio(stratum, x_u, y_u, h, N_h)
        stats['producers_accuracy'].append(pa)
        stats['producers_accuracy_se'].append(pa_se)

        # f1
        stats['f1'].append(2 * ua * pa / (ua + pa))
        stats['f1_se'].append(np.sqrt(np.add(
            (ua_se * (2 * pa / (ua + pa) - 2 * ua * pa / (ua + pa) ** 2)) ** 2,
            (pa_se * (2 * ua / (ua + pa) - 2 * ua * pa / (ua + pa) ** 2)) ** 2
        )))

    return stats


@typechecked
def aa_estimator_stratified(
        stratum: np.ndarray, y_u: np.ndarray, h: np.ndarray, N_h: np.ndarray
) -> Tuple[float, float]:
    Y = 0.
    n_h = np.zeros_like(N_h)
    for i in range(len(h)):
        indices = np.where(stratum == h[i])[0]
        y_u_mean = np.mean(y_u[indices])
        Y += N_h[i] * y_u_mean
        n_h[i] = len(indices)
    R = Y / np.sum(N_h)

    R_VAR = 0.
    for i in range(len(h)):
        indices = np.where(stratum == h[i])[0]
        f = (1. - n_h[i] / N_h[i])
        s2yh = np.var(y_u[indices], ddof=1)
        R_VAR += N_h[i] ** 2 * f * s2yh / n_h[i]
    R_VAR /= np.sum(N_h) ** 2
    R_SE = np.sqrt(R_VAR)
    return R, R_SE


@typechecked
def aa_estimator_stratified_ratio(
        stratum: np.ndarray, x_u: np.ndarray, y_u: np.ndarray, h: np.ndarray, N_h: np.ndarray
) -> Tuple[float, float]:
    X = 0.
    Y = 0.
    n_h = np.zeros_like(N_h)
    for i in range(len(h)):
        indices = np.where(stratum == h[i])[0]
        x_u_mean = np.mean(x_u[indices])
        y_u_mean = np.mean(y_u[indices])
        Y += N_h[i] * y_u_mean
        X += N_h[i] * x_u_mean
        n_h[i] = len(indices)
    R = Y / X

    R_VAR = 0.
    for i in range(len(h)):
        indices = np.where(stratum == h[i])[0]
        f = (1. - n_h[i] / N_h[i])
        s2xh = np.var(x_u[indices], ddof=1)
        s2yh = np.var(y_u[indices], ddof=1)
        sxyh = np.cov(x_u[indices], y_u[indices], ddof=1)[0][1]
        R_VAR += N_h[i] ** 2 * f * (s2yh + R ** 2 * s2xh - 2 * R * sxyh) / n_h[i]
    R_VAR /= X ** 2

    R_VAR = abs(R_VAR)  # fixes an issue with floating-point accuracies that resulted in near zero, but negative values

    R_SE = np.sqrt(R_VAR)
    return R, R_SE
