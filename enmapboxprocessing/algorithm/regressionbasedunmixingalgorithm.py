from collections import defaultdict
from os import makedirs
from os.path import join, exists, dirname
from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapboxprocessing.algorithm.aggregaterasterbandsalgorithm import AggregateRasterBandsAlgorithm
from enmapboxprocessing.algorithm.classificationfromclassprobabilityalgorithm import \
    ClassificationFromClassProbabilityAlgorithm
from enmapboxprocessing.algorithm.fitgenericregressoralgorithm import FitGenericRegressorAlgorithm
from enmapboxprocessing.algorithm.predictregressionalgorithm import PredictRegressionAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromsynthmixalgorithm import \
    PrepareRegressionDatasetFromSynthMixAlgorithm
from enmapboxprocessing.algorithm.stackrasterlayersalgorithm import StackRasterLayersAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class RegressionBasedUnmixingAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Endmember dataset'
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_REGRESSOR, _REGRESSOR = 'regressor', 'Regressor'
    P_N, _N = 'n', 'Number of mixtures per class'
    P_BACKGROUND, _BACKGROUND = 'background', 'Proportion of background mixtures (%)'
    P_INCLUDE_ENDMEMBER, _INCLUDE_ENDMEMBER = 'includeEndmember', 'Include original endmembers'
    P_MIXING_PROBABILITIES, _MIXING_PROBABILITIES = 'mixingProbabilities', 'Mixing complexity probabilities'
    P_ALLOW_WITHINCLASS_MIXTURES, _ALLOW_WITHINCLASS_MIXTURES = 'allowWithinClassMixtures', 'Allow within-class mixtures'
    P_CLASS_PROBABILITIES, _CLASS_PROBABILITIES = 'classProbabilities', 'Class probabilities'
    P_ENSEMBLE_SIZE, _ENSEMBLE_SIZE = 'ensembleSize', 'Ensemble size'
    P_ROBUST_FUSION, _ROBUST_FUSION = 'robustFusion', 'Robust decision fusion'
    P_OUTPUT_FRACTION, _OUTPUT_FRACTION = 'outputFraction', 'Output class fraction layer'
    P_OUTPUT_CLASSIFICATION, _OUTPUT_CLASSIFICATION = 'outputClassification', 'Output classification layer'
    P_OUTPUT_VARIATION, _OUTPUT_VARIATION = 'outputFractionVariation', 'Output class fraction variation layer'

    def displayName(self) -> str:
        return 'Regression-based unmixing'

    def shortDescription(self) -> str:
        return 'Implementation of the regression-based unmixing approach ' \
               '<a href="https://doi.org/10.1109/JSTARS.2016.2634859">' \
               '"Ensemble Learning From Synthetically Mixed Training Data for Quantifying Urban Land Cover With ' \
               'Support Vector Regression"</a> ' \
               'in IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing, vol. 10, no. 4, ' \
               'pp. 1640-1650, April 2017.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'A classification dataset with spectral endmembers used for synthetical mixing.'),
            (self._RASTER, 'A raster layer to be unmixed.'),
            (self._REGRESSOR, 'Scikit-Learn Python code specifying a regressor.'),
            (self._N, 'Number of mixtures per class.'),
            (self._BACKGROUND, 'Proportion of background mixtures.'),
            (self._INCLUDE_ENDMEMBER, 'Whether to include the original library spectra into the dataset.'),
            (self._MIXING_PROBABILITIES, 'A list of probabilities for using 2, 3, 4, ... endmember mixing models. '
                                         'Trailing 0 probabilities can be skipped. The default values of 0.5, 0.5,'
                                         'results in 50% 2-endmember and 50% 3-endmember models.'),
            (self._ALLOW_WITHINCLASS_MIXTURES, 'Whether to allow mixtures with profiles belonging to the same class.'),
            (self._CLASS_PROBABILITIES, 'A list of probabilities for drawing profiles from each class. '
                                        'If not specified, class probabilities are proportional to the class size.'),
            (self._ENSEMBLE_SIZE, 'Number of individual runs/predictions.'),
            (self._ROBUST_FUSION, 'Whether to use median and IQR (interquartile range) aggregation for ensemble '
                                  'decicion fusion. The default is to use mean and standard deviation.'),
            (self._OUTPUT_FRACTION, self.RasterFileDestination),
            (self._OUTPUT_CLASSIFICATION, self.RasterFileDestination),
            (self._OUTPUT_VARIATION, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterClassificationDataset(self.P_DATASET, self._DATASET)
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterRegressorCode(self.P_REGRESSOR, self._REGRESSOR)
        self.addParameterInt(self.P_N, self._N, 1000, False, 1)
        self.addParameterInt(self.P_BACKGROUND, self._BACKGROUND, 0, False, 0, 100)
        self.addParameterBoolean(self.P_INCLUDE_ENDMEMBER, self._INCLUDE_ENDMEMBER, True)
        self.addParameterString(self.P_MIXING_PROBABILITIES, self._MIXING_PROBABILITIES, '0.5, 0.5', False, True)
        self.addParameterBoolean(self.P_ALLOW_WITHINCLASS_MIXTURES, self._ALLOW_WITHINCLASS_MIXTURES, True)
        self.addParameterString(self.P_CLASS_PROBABILITIES, self._CLASS_PROBABILITIES, None, False, True)
        self.addParameterInt(self.P_ENSEMBLE_SIZE, self._ENSEMBLE_SIZE, 1, False, 1)
        self.addParameterBoolean(self.P_ROBUST_FUSION, self._ROBUST_FUSION, False, True)
        self.addParameterRasterDestination(self.P_OUTPUT_FRACTION, self._OUTPUT_FRACTION)
        self.addParameterRasterDestination(self.P_OUTPUT_CLASSIFICATION, self._OUTPUT_CLASSIFICATION, None, True, False)
        self.addParameterRasterDestination(self.P_OUTPUT_VARIATION, self._OUTPUT_VARIATION, None, True, False)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameClassificationDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        code = self.parameterAsString(parameters, self.P_REGRESSOR, context)
        n = self.parameterAsInt(parameters, self.P_N, context)
        background = self.parameterAsInt(parameters, self.P_BACKGROUND, context)
        includeEndmember = self.parameterAsBoolean(parameters, self.P_INCLUDE_ENDMEMBER, context)
        mixingProbabilities = self.parameterAsString(parameters, self.P_MIXING_PROBABILITIES, context)
        allowWithinClassMixtures = self.parameterAsBoolean(parameters, self.P_ALLOW_WITHINCLASS_MIXTURES, context)
        classProbabilities = self.parameterAsValues(parameters, self.P_CLASS_PROBABILITIES, context)
        ensembleSize = self.parameterAsInt(parameters, self.P_ENSEMBLE_SIZE, context)
        robustFusion = self.parameterAsBoolean(parameters, self.P_ROBUST_FUSION, context)
        filenameFraction = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_FRACTION, context)
        filenameClassification = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_CLASSIFICATION, context)
        filenameVariation = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_VARIATION, context)

        with open(filenameFraction + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            categories = ClassifierDump.fromDict(Utils.pickleLoad(filenameClassificationDataset)).categories

            # create ensemble runs
            feedback.pushInfo('Create ensemble')
            filenames = defaultdict(list)
            folderEnsemble = Utils.tmpFilename(filenameFraction, 'ensemble')
            folderRuns = join(folderEnsemble, 'runs')
            for run in range(1, ensembleSize + 1):
                feedback.setProgress((run - 1) / ensembleSize * 100)

                folderRun = join(folderRuns, str(run))

                # create mixtures
                alg = PrepareRegressionDatasetFromSynthMixAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_DATASET: filenameClassificationDataset,
                    alg.P_N: n,
                    alg.P_BACKGROUND: background,
                    alg.P_INCLUDE_ENDMEMBER: includeEndmember,
                    alg.P_MIXING_PROBABILITIES: mixingProbabilities,
                    alg.P_ALLOW_WITHINCLASS_MIXTURES: allowWithinClassMixtures,
                    alg.P_CLASS_PROBABILITIES: classProbabilities,
                    alg.P_OUTPUT_FOLDER: folderRun
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)

                for category in categories:
                    filenameRegressionDatasetRun = join(folderRun, category.name + '.pkl')
                    filenameRegressorRun = filenameRegressionDatasetRun.replace('.pkl', '.regressor.pkl')
                    filenameFractionRun = filenameRegressionDatasetRun.replace('.pkl', '.fraction.tif')

                    # create regressor
                    alg = FitGenericRegressorAlgorithm()
                    alg.initAlgorithm()
                    parameters = {
                        alg.P_DATASET: filenameRegressionDatasetRun,
                        alg.P_REGRESSOR: code,
                        alg.P_OUTPUT_REGRESSOR: filenameRegressorRun
                    }
                    self.runAlg(alg, parameters, None, feedback2, context, True)

                    # predict map
                    alg = PredictRegressionAlgorithm()
                    alg.initAlgorithm()
                    parameters = {
                        alg.P_RASTER: raster,
                        alg.P_REGRESSOR: filenameRegressorRun,
                        alg.P_OUTPUT_REGRESSION: filenameFractionRun
                    }
                    self.runAlg(alg, parameters, None, feedback2, context, True)

                    filenames[category.name].append(filenameFractionRun)

            # aggregate over runs
            feedback.pushInfo('Aggregate runs')
            for i, category in enumerate(categories):
                feedback.setProgress(i / len(categories) * 100)

                # stack runs
                filenameStack = join(folderEnsemble, 'stack', category.name + '.vrt')
                filenameAggregation = join(folderEnsemble, 'aggregation', category.name + '.tif')
                if not exists(dirname(filenameStack)):
                    makedirs(dirname(filenameStack))
                if not exists(dirname(filenameAggregation)):
                    makedirs(dirname(filenameAggregation))
                gdal.BuildVRT(filenameStack, filenames[category.name], separate=True)

                # aggregate runs
                alg = AggregateRasterBandsAlgorithm()
                parameters = {
                    alg.P_RASTER: filenameStack,
                    alg.P_OUTPUT_RASTER: filenameAggregation
                }
                if robustFusion:
                    parameters[alg.P_FUNCTION] = [alg.MedianFunction]
                    if filenameVariation is not None:
                        parameters[alg.P_FUNCTION].append(alg.InterquartileRangeFunction)
                else:
                    parameters[alg.P_FUNCTION] = [alg.ArithmeticMeanFunction]
                    if filenameVariation is not None:
                        parameters[alg.P_FUNCTION].append(alg.StandardDeviationFunction)
                self.runAlg(alg, parameters, None, feedback2, context, True)

            # prepare fraction results
            feedback.pushInfo('Prepare fraction layer')
            filenames = [join(folderEnsemble, 'aggregation', category.name + '.tif') for category in categories]
            filename = Utils.tmpFilename(filenameFraction, 'fraction.vrt')
            alg = StackRasterLayersAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_RASTERS: filenames,
                alg.P_BAND: 1,
                alg.P_OUTPUT_RASTER: filename
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)
            ds = gdal.Translate(filenameFraction, filename)
            writer = RasterWriter(ds)
            for bandNo, category in enumerate(categories, 1):
                writer.setBandName(category.name, bandNo)
                writer.setBandColor(QColor(category.color), bandNo)

            # prepare variation results
            if filenameVariation is not None:
                feedback.pushInfo('Prepare variation layer')
                filename = Utils.tmpFilename(filenameFraction, 'variation.vrt')
                alg = StackRasterLayersAlgorithm()
                parameters = {
                    alg.P_RASTERS: filenames,
                    alg.P_BAND: 2,
                    alg.P_OUTPUT_RASTER: filename
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
                ds = gdal.Translate(filenameVariation, filename)
                writer = RasterWriter(ds)
                for bandNo, category in enumerate(categories, 1):
                    writer.setBandName(category.name, bandNo)
                    writer.setBandColor(QColor(category.color), bandNo)

            # prepare classification result
            if filenameClassification is not None:
                feedback.pushInfo('Prepare classification layer')
                alg = ClassificationFromClassProbabilityAlgorithm()
                parameters = {
                    alg.P_PROBABILITY: filenameFraction,
                    alg.P_OUTPUT_CLASSIFICATION: filenameClassification
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {
                self.P_OUTPUT_FRACTION: filenameFraction,
                self.P_OUTPUT_VARIATION: filenameVariation,
                self.P_OUTPUT_CLASSIFICATION: filenameClassification
            }

            self.toc(feedback, result)

        return result
