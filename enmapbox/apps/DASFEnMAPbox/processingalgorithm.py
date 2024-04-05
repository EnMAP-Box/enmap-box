# 0
from qgis.core import *
from .core import DASF_retrieval

# 1
class DASFretrievalAlgorithm(QgsProcessingAlgorithm):

    P_INPUT = 'Input Raster'
    P_OUTPUT = 'DASF Output Raster'
    P_Retrieval_Quality = 'DASF retrieval quality Output Raster'
    P_CSC = 'CSC Output Raster'
# 2
    def group(self):
        return 'Vegetation'

    def groupId(self):
        return 'vegetation' # internal id

    def displayName(self):
        return 'DASF retrieval'

    def name(self):
        return 'DASF_retrieval' # internal id
# 3
    def initAlgorithm(self, configuration=None):

        # Define required user inputs.
        self.addParameter(QgsProcessingParameterRasterLayer(name=self.P_INPUT, description='Input Raster'))
        self.addParameter(QgsProcessingParameterRasterDestination(name=self.P_OUTPUT, description='DASF Output Raster'))
        self.addParameter(QgsProcessingParameterRasterDestination(name=self.P_Retrieval_Quality,
                                                                  description='DASF retrieval quality Output Raster'))
        self.addParameter(QgsProcessingParameterRasterDestination(name=self.P_CSC,
                                                                  description='CSC Output Raster'))
# 4
    def processAlgorithm(self, parameters, context, feedback):
        assert isinstance(feedback, QgsProcessingFeedback)

        # try to execute the core algorithm
        try:

            # pass all selected input parameters to the core algorithm
            DASF_retrieval(
                inputFile=self.parameterAsRasterLayer(parameters, self.P_INPUT, context).source(),
                outputName=self.parameterAsOutputLayer(parameters, self.P_OUTPUT, context),
                secondoutputName=self.parameterAsOutputLayer(parameters, self.P_Retrieval_Quality, context),
                thirdoutputName= self.parameterAsOutputLayer(parameters, self.P_CSC, context)
            )

            # return all output parameters
            return {self.P_OUTPUT: self.parameterAsOutputLayer(parameters, self.P_OUTPUT, context)}
            return {self.P_Retrieval_Quality: self.parameterAsOutputLayer(parameters, self.P_Retrieval_Quality, context)}
            return {self.P_CSC: self.parameterAsOutputLayer(parameters, self.P_CSC, context)}

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
       '<p>This tool derives the DASF (directional area scattering factor) function for vegetation canopy with dark' \
        'background or sufficiently dense vegetation where the impact of canopy background is negligible.</p>' \
        '<a href="https://doi.org/10.1073/pnas.1210196109">Knyazikhin et al. 2013</a>' \
        '<h3>Input raster</h3>' \
        '<p>Hyperspectral raster image.</p>' \
        '<h3>DASF output raster</h3>' \
        '<p>Enter a name to your DASF output raster.</p>' \
        '<h3>Retrieval quality output raster</h3>' \
        '<p>Enter a name to the second output raster. This tool returns a two layers raster file for which:' \
        '<p>Band 1 = R squared</p>' \
        '<p>Band 2 = P value</p>' \
        '<p>allowing you to access the quality of the DASF retrieval for each pixel.</p>'\
        '<h3>CSC output raster</h3>' \
        '<p>Enter a name to your CSC out raster.</p>' \


        return html
# 6
    def helpUrl(self, *args, **kwargs):
        return ''
# 7
    def createInstance(self):
        return type(self)()
