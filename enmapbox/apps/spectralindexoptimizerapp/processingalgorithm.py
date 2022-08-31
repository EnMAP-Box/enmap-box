# 0
from qgis.core import *

from spectralindexoptimizerapp.core import spectralIndexOptimizer


# 1
class SpectralIndexOptimizerProcessingAlgorithm(QgsProcessingAlgorithm):
    P_FEATURES = 'features'
    P_LABELS = 'labels'
    P_INDEX_TYPE = 'indexType'
    INDEX_TYPE_OPTIONS = ['Normalized Difference Index', 'Ratio Index', 'Difference Index']
    P_PERFORMANCE_TYPE = 'performanceType'
    PERFORMANCE_TYPE_OPTIONS = ['RMSE', 'MAE', 'R^2']
    P_RASTER = 'raster'
    P_OUTPUT_PREDICTION = 'outprediction'
    P_OUTPUT_REPORT = 'outreport'

    # 2
    def group(self):
        return 'Regression'

    def groupId(self):
        return 'Regression'  # internal id

    def displayName(self):
        return 'Spectral Index Optimizer'

    def name(self):
        return 'SpectralIndexOptimizer'  # internal id

    # 3
    def initAlgorithm(self, configuration=None):

        # Define required user inputs.
        self.addParameter(QgsProcessingParameterRasterLayer(
            name=self.P_FEATURES, description='Features'))
        self.addParameter(QgsProcessingParameterRasterLayer(
            name=self.P_LABELS, description='Labels'))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.P_INDEX_TYPE, description='Index Type',
            options=self.INDEX_TYPE_OPTIONS))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.P_PERFORMANCE_TYPE, description='Performance Type',
            options=self.PERFORMANCE_TYPE_OPTIONS))
        self.addParameter(QgsProcessingParameterRasterLayer(
            name=self.P_RASTER, description='Raster'))
        self.addParameter(QgsProcessingParameterRasterDestination(
            name=self.P_OUTPUT_PREDICTION, description='Output prediction'))
        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.P_OUTPUT_REPORT, description='HTML Report',
            defaultValue='spectralIndexOptimizerReport.html')
        )

    # 4
    def processAlgorithm(self, parameters, context, feedback):
        assert isinstance(feedback, QgsProcessingFeedback)

        # try to execute the core algorithm
        try:

            # pass all selected input parameters to the core algorithm
            spectralIndexOptimizer(
                filenamePrediction=self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PREDICTION, context),
                filenameReport=self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context),
                featuresFilename=self.parameterAsRasterLayer(parameters, self.P_FEATURES, context).source(),
                labelsFilename=self.parameterAsRasterLayer(parameters, self.P_LABELS, context).source(),
                rasterFilename=self.parameterAsRasterLayer(parameters, self.P_RASTER, context).source(),
                indexType=self.parameterAsEnum(parameters, self.P_INDEX_TYPE, context),
                performanceType=self.parameterAsEnum(parameters, self.P_PERFORMANCE_TYPE, context))

            #oversampling=self.parameterAsInt(parameters, self.P_OVERSAMPLING, context),
                #coverage=self.parameterAsDouble(parameters, self.P_COVERAGE, context))

            # return all output parameters
            return {
                self.P_OUTPUT_PREDICTION: self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PREDICTION, context),
                self.P_OUTPUT_REPORT: self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)
            }

        # handle any uncatched exceptions
        except:
            # print traceback to console and pass it to the processing feedback object
            import traceback
            traceback.print_exc()
            for line in traceback.format_exc().split('\n'):
                feedback.reportError(line)
            return {}

    # 5
    def shortHelpString(self):

        html = '' \
               '<p>This algorithm finds the optimal spectral two-band index to estimate ' \
               'a measured variable via linear regression.</p>' \
               '<h3>Features</h3>' \
               '<p>Input raster (hyperspectral image).</p>' \
               '<h3>Labels</h3>' \
               '<p>Input raster with measurements at the points they have been measured. </p>' \
               '<h3>Index Type</h3>' \
			   '<ul><li>Normalized Difference: [(a - b) / (a + b)]</li>' \
			   '<li>Ratio Index: (a / b)</li>' \
			   '<li>Difference Index: (a - b)</li></ul>' \
               '<h3>Performance Type</h3>' \
               '<ul><li>RMSE (Root mean squared error)</li>' \
               '<li>MAE (Mean Absolute Error)</li>' \
               '<li>R^2 (R-squared, coefficient of determination)</li></ul>' \
               '<h3>Raster</h3>' \
               '<p>Raster File to apply the model on (may be the same as feature file)</p>' \
               '<h3>Output prediction</h3>' \
               '<p>Specify output raster, otherwise the output will be stored in a temporary file.</p>' \
               '<h3>HTML Report</h3>' \
               '<p>The resulting bands and performance will be displayed in an HTML report.</p>'
        return html

    # '<p>(The labels can be created in the EnMAP box using ...)</p>' \

    # 6
    def helpUrl(self, *args, **kwargs):
        return 'https://trier-for-enmap-box.readthedocs.io/apps/sio.html'

    # 7
    def createInstance(self):
        return type(self)()
