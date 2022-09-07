import webbrowser
from collections import OrderedDict
from dataclasses import dataclass
from math import isnan
from os import makedirs
from os.path import exists, dirname
from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.rasterizevectoralgorithm import RasterizeVectorAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.reportwriter import MultiReportWriter, HtmlReportWriter, CsvReportWriter
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsVectorLayer, \
    QgsProcessingException
from typeguard import typechecked


@typechecked
class RegressionPerformanceAlgorithm(EnMAPProcessingAlgorithm):
    P_REGRESSION, _REGRESSION = 'regression', 'Regression layer'
    P_REFERENCE, _REFERENCE = 'reference', 'Observed continuous-valued layer'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outRegressionPerformance', 'Output report'

    @classmethod
    def displayName(cls) -> str:
        return 'Regression layer accuracy report'

    def shortDescription(self) -> str:
        return 'Estimates map accuracy.' \
               'We use the formulars as described in ' \
               '<a href="https://scikit-learn.org/stable/modules/model_evaluation.html#regression-metrics">Scikit-Learn Regression metrics</a> ' \
               'user guide. ' \
               'Observed and predicted target variables are matched by name.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._REGRESSION, 'A regression layer that is to be assessed.'),
            (self._REFERENCE, 'A continuous-valued layer representing a (ground truth) observation sample.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Regression.value

    def checkTargets(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        regression = self.parameterAsRasterLayer(parameters, self.P_REGRESSION, context)
        reference = self.parameterAsLayer(parameters, self.P_REFERENCE, context)
        targetsReference = Utils.targetsFromLayer(reference)
        targetsPrediction = Utils.targetsFromLayer(regression)
        for tR in targetsReference:
            for tP in targetsPrediction:
                if tR.name == tP.name:
                    return True, ''  # good, we found the reference target
            return False, f'Observed target "{tR.name}" not found in predicted targets.'
        for tP in targetsPrediction:
            for tR in targetsReference:
                if tR.name == tP.name:
                    return True, ''  # good, we found the map target
            return False, f'Predicted target "{tP.name}" not found in observed targets.'
        return False, 'Empty target list.'

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        checks = [
            self.checkParameterRasterRegression(parameters, self.P_REGRESSION, context),
            self.checkParameterMapRegression(parameters, self.P_REFERENCE, context),
        ]
        for valid, message in checks:
            if not valid:
                return valid, message

        valid, message = self.checkTargets(parameters, context)
        if not valid:
            return valid, message

        return True, ''

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_REGRESSION, self._REGRESSION)
        self.addParameterMapLayer(self.P_REFERENCE, self._REFERENCE)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        regression = self.parameterAsRasterLayer(parameters, self.P_REGRESSION, context)
        reference = self.parameterAsLayer(parameters, self.P_REFERENCE, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            targetsReference = Utils.targetsFromLayer(reference)
            targetsPrediction = Utils.targetsFromLayer(regression)

            # prepare reference
            if isinstance(reference, QgsVectorLayer):
                feedback.pushInfo('Rasterize continuous-valued layer')
                noDataValue = Utils.defaultNoDataValue(np.float32)
                fieldNames = reference.fields().names()
                filenames = list()
                for i, target in enumerate(targetsReference, 1):
                    assert target.name in fieldNames
                    alg = RasterizeVectorAlgorithm()
                    alg.initAlgorithm()
                    parameters = {
                        alg.P_VECTOR: reference,
                        alg.P_GRID: regression,
                        alg.P_BURN_ATTRIBUTE: target.name,
                        alg.P_INIT_VALUE: noDataValue,
                        alg.P_DATA_TYPE: alg.Float32,
                        alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, f'target_{i}.tif')
                    }
                    self.runAlg(alg, parameters, None, feedback2, context, True)
                    filenames.append(parameters[alg.P_OUTPUT_RASTER])
                ds = gdal.BuildVRT(Utils.tmpFilename(filename, 'observation.vrt'), filenames, separate=True)
                writer = RasterWriter(ds)
                writer.setNoDataValue(noDataValue)
                for bandNo, target in enumerate(targetsReference, 1):
                    writer.setBandName(target.name, bandNo)
                    if target.color is not None:
                        writer.setBandColor(QColor(target.color), bandNo)

                source = writer.source()
                del writer, ds
                reference = QgsRasterLayer(source)
            elif isinstance(reference, QgsRasterLayer):
                alg = TranslateRasterAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_RASTER: reference,
                    alg.P_GRID: regression,
                    alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'observation.vrt')
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
                reference = QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER])

            # prepare prediction (reorder bands)
            targetNames = [t.name for t in targetsReference]
            bandNames = [t.name for t in targetsPrediction]
            bandList = [bandNames.index(targetName) + 1 for targetName in targetNames]
            alg = TranslateRasterAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_RASTER: regression,
                alg.P_BAND_LIST: bandList,
                alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'prediction.vrt')
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)
            regression = QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER])

            # read data and calculate regression metrics
            feedback.pushInfo('Read data and calculate regression metrics')
            # Note that we can be sure that:
            #   - all pixel grids match
            #   - target bands match
            readerObserved = RasterReader(reference)
            readerPredicted = RasterReader(regression)
            statss = OrderedDict()
            for bandNo, target in enumerate(targetsReference, 1):
                arrayObserved = readerObserved.array(bandList=[bandNo])
                arrayPredicted = readerPredicted.array(bandList=[bandNo])
                maskArrayObserved = readerObserved.maskArray(arrayObserved, bandList=[bandNo])
                maskArrayPredicted = readerPredicted.maskArray(arrayPredicted, bandList=[bandNo])

                ok = maskArrayPredicted[0][maskArrayObserved[0]].all()
                if not ok:
                    raise QgsProcessingException('Observed missing pixel predictions.')

                yObserved = arrayObserved[0][maskArrayObserved[0]].astype(np.float32)
                yPredicted = arrayPredicted[0][maskArrayObserved[0]].astype(np.float32)
                statss[target.name] = accuracyAssessment(yObserved, yPredicted)

            Utils.jsonDump(statss, filename + '.json')
            feedback.pushInfo('Create report')
            self.writeReport(filename, statss)
            result = {self.P_OUTPUT_REPORT: filename}

            if openReport:
                webbrowser.open_new_tab(filename)

            self.toc(feedback, result)

        return result

    @classmethod
    def writeReport(cls, filename: str, statss: Dict[str, 'AccuracyAssessmentResult']):

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
            report.writeHeader('Regression layer accuracy report')

            report.writeParagraph(f'Sample size: {list(statss.values())[0].n} px')

            report.writeSubHeader('Regression metrics')

            keys = ['meanAbsoluteError', 'rootMeanSquaredError', 'ratioOfPerformanceToDeviation',
                    'meanError', 'meanSquaredError', 'medianAbsoluteError', 'squaredPearsonCorrelationScore',
                    'explainedVarianceScore', 'r2Score']
            rowHeaders = [
                'Mean absolute error (MAE)',
                'Root MSE (RMSE)',
                'Ratio of performance to deviation (RPD)',
                'Mean error (ME)',
                'Mean squared error (MSE)',
                'Median absolute error (MedAE)',
                'Squared pearson correlation (r^2)',
                'Explained variance score',
                'Coefficient of determination (R^2)'
            ]
            values = [[smartRound(getattr(stats, key), 4) for stats in statss.values()] for key in keys]
            report.writeTable(values, None, list(statss), rowHeaders)

            report.writeSubHeader('Scatter and Residuals Plots')

            import matplotlib
            from matplotlib import pyplot

            for name, stats in statss.items():
                yO = stats.yObserved
                yP = stats.yPredicted
                fig, ax = pyplot.subplots(facecolor='white', figsize=(7, 7))
                # prepare 2x2 grid for plotting scatterplot on lower left, and adjacent histograms
                gs = matplotlib.gridspec.GridSpec(2, 2, width_ratios=[3, 1], height_ratios=[1, 3])

                ax0 = pyplot.subplot(gs[0, 0])
                ax0.hist(yO, bins=100, edgecolor='None', color='navy')
                pyplot.xlim([np.min(yO), np.max(yO)])
                pyplot.tick_params(which='both', direction='out', length=10, pad=10)
                # hide ticks and ticklabels
                ax0.set_xticklabels([])
                ax0.set_ylabel('counts')
                ax0.set_title(name)
                ax0.xaxis.set_ticks_position('bottom')
                ax0.yaxis.set_ticks_position('left')

                ax1 = pyplot.subplot(gs[1, 1])
                ax1.hist(yP, orientation='horizontal', bins=100, edgecolor='None', color='navy')
                pyplot.tick_params(which='both', direction='out', length=10, pad=10)
                pyplot.ylim([np.min(yO), np.max(yO)])
                # hide ticks and ticklabels
                ax1.set_yticklabels([])
                ax1.set_xlabel('counts')
                ax1.yaxis.set_ticks_position('left')
                ax1.xaxis.set_ticks_position('bottom')

                ax2 = pyplot.subplot(gs[1, 0])
                ax2.scatter(yO, yP, s=10)  # , edgecolor='', color='navy')
                ymin = np.min(yO)
                ymax = np.max(yO)
                yspan = ymax - ymin
                ymin -= yspan * 0.01  # give some more space
                ymax += yspan * 0.01

                pyplot.xlim([ymin, ymax])
                pyplot.ylim([ymin, ymax])
                pyplot.tick_params(which='both', direction='out')
                pyplot.xlabel('Observed')
                pyplot.ylabel('Predicted')

                minX = np.min(yO)
                maxX = np.max(yO)
                # 1:1 line
                pyplot.plot([minX, maxX], [minX, maxX], 'k-')
                # fitted line
                m, n = stats.fittedLineCoeffs
                if n > 0:
                    fittedLineText = 'f(x) = {} * x + {}'.format(round(m, 5), round(n, 5))
                else:
                    fittedLineText = 'f(x) = {} * x - {}'.format(round(m, 5), abs(round(n, 5)))

                pyplot.plot([minX, maxX], [m * minX + n, m * maxX + n], 'r--', label=fittedLineText)
                pyplot.legend(bbox_to_anchor=(0.75, -0.15))
                fig.tight_layout()
                filenameFig = filename + f'.{name}.scatter.png'
                fig.savefig(filenameFig, format='png')
                pyplot.close()
                report.writeImage(filenameFig)

                fig, ax = pyplot.subplots(facecolor='white', figsize=(7, 5))
                ax.hist(stats.residuals, bins=100, edgecolor='None', color='navy')
                ax.set_title(name)
                ax.set_xlabel('Predicted - Observed')
                ax.set_ylabel('Counts')
                fig.tight_layout()
                filenameFig = filename + f'.{name}.residuals.png'
                fig.savefig(filenameFig, format='png')
                pyplot.close()
                report.writeImage(filenameFig)


@typechecked()
@dataclass
class AccuracyAssessmentResult(object):
    n: int
    yObserved: np.ndarray
    yPredicted: np.ndarray
    residuals: np.ndarray
    explainedVarianceScore: float
    meanAbsoluteError: float
    meanSquaredError: float
    rootMeanSquaredError: float
    ratioOfPerformanceToDeviation: float
    medianAbsoluteError: float
    r2Score: float
    meanError: float
    squaredPearsonCorrelationScore: float
    fittedLineCoeffs: np.ndarray


@typechecked
def accuracyAssessment(yObserved: np.ndarray, yPredicted: np.ndarray):
    from sklearn.metrics import explained_variance_score, mean_absolute_error, mean_squared_error, \
        median_absolute_error, r2_score
    from scipy.stats import pearsonr
    assert yObserved.ndim == 1
    assert yPredicted.ndim == 1
    assert len(yObserved) == len(yPredicted)

    yO = yObserved
    yP = yPredicted
    n = len(yO)
    residuals = yP - yO

    explainedVarianceScore = explained_variance_score(yO, yP)
    meanAbsoluteError = mean_absolute_error(yO, yP)
    meanSquaredError = mean_squared_error(yO, yP)
    rootMeanSquaredError = np.sqrt(meanSquaredError)
    ratioOfPerformanceToDeviation = np.std(yO / rootMeanSquaredError)
    medianAbsoluteError = median_absolute_error(yO, yP)
    r2Score = r2_score(yO, yP)
    meanError = np.mean(yP - yO)
    squaredPearsonCorrelationScore = pearsonr(yO, yP)[0] ** 2
    fittedLineCoeffs = np.polyfit(yO, yP, 1)  # f(x) = m*x + n

    return AccuracyAssessmentResult(
        n, yObserved, yPredicted, residuals, explainedVarianceScore, meanAbsoluteError, meanSquaredError,
        rootMeanSquaredError, ratioOfPerformanceToDeviation, medianAbsoluteError, r2Score, meanError,
        squaredPearsonCorrelationScore, fittedLineCoeffs
    )
