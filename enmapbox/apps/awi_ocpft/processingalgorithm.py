# 0
from qgis.core import *
from .core import ocpft

# 1
class OCPFTProcessingAlgorithm(QgsProcessingAlgorithm):

    P_FILE = 'innc'
    P_SENSOR = 'sensor'
    P_MODEL = 'model'
    P_AC = 'ac'
    P_OSIZE = 'osize'

    P_OUTPUT_FOLDER = 'outfolder'

    SENSORS_ALGO = ['EnMAP', 'OLCI', 'MSI', 'DESIS']
    SENSORS_USER = ['EnMAP (Environmental Mapping and Analysis Program, Germany)', 'OLCI (Ocean and Land Colour Instrument, Europe)', 'MSI (Medium Resolution Imaging Spectrometer, Europe)', 'DESIS (DLR Earth Sensing Imaging Spectrometer, Germany)']
    MODEL = ['LAKE CONSTANCE', 'GLOBAL']
    AC = ['ENPT ACWATER', 'POLYMER'] # ONNS and other options will be added
    OSIZE = ['Standard output'] # define better

# 2
    def group(self):
        return 'Water'

    def groupId(self):
        return 'water' # internal id

    def displayName(self):
        return 'OC-PFT'

    def name(self):
        return 'ocpft' # internal id
# 3
    def initAlgorithm(self, configuration=None):

        # Define required user inputs.
        self.addParameter(QgsProcessingParameterFile(
            name=self.P_FILE, description='Input'))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.P_SENSOR,
            description='Sensor',
            options=self.SENSORS_USER,
            defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.P_MODEL,
            description='Model',
            options=self.MODEL,
            defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.P_AC,
            description='Atmospheric correction',
            options=self.AC,
            defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.P_OSIZE,
            description='Processor output size',
            options=self.OSIZE,
            defaultValue=0))

        self.addParameter(QgsProcessingParameterFolderDestination(
            name=self.P_OUTPUT_FOLDER, description='Output Folder'))
# 4
    def processAlgorithm(self, parameters, context, feedback):
        assert isinstance(feedback, QgsProcessingFeedback)

        # try to execute the core algorithm
        try:
            tmp = self.parameterAsEnum(parameters, self.P_SENSOR, context)
            print(tmp)

            cmd, output = ocpft(inputfile=self.parameterAsFile(parameters, self.P_FILE, context),
                 outputDirectory=self.parameterAsFileOutput(parameters, self.P_OUTPUT_FOLDER, context),
                 sensor=self.SENSORS_ALGO[self.parameterAsEnum(parameters, self.P_SENSOR, context)],
                 model=self.parameterAsEnum(parameters, self.P_MODEL, context),
                 ac=self.parameterAsEnum(parameters, self.P_AC, context),   # note only polymer is implemented!!!
                 osize=self.parameterAsEnum(parameters, self.P_OSIZE, context))

            feedback.pushCommandInfo(cmd)
            feedback.pushDebugInfo(output)

            # return all output parameters
            return {self.P_OUTPUT_FOLDER: self.parameterAsFileOutput(parameters, self.P_OUTPUT_FOLDER, context)}

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
               '<p> OC-PFT is abundance based approach for the retrieval of Phytoplankton Functional Types (PFTs) ' \
               'from satellite or in situ measurements using as a-proxy HPLC measurements of ' \
               'diagnostic pigments by assuming that each marker pigment for specific PFT varies in dependence ' \
               'to chlorophyll-a (Chl-a) ' \
               '[' \
               '<a href="https://bg.copernicus.org/articles/8/311/2011"> Hirata et al. 2011</a>; ' \
               '<a href="https://www.mdpi.com/2072-4292/6/10/10089"> Soppa et al., 2014</a>; ' \
               '<a href="https://www.sciencedirect.com/science/article/pii/S0034425715300614"> Brewin et al., 2015</a>;' \
               '<a href="https://www.frontiersin.org/articles/10.3389/fmars.2017.00203/full"> Losa et al.,2017</a>; ' \
               '<a href="https://desis2021.welcome-manager.de/archiv/web/userfiles/desis2021/Alvarado_DESISWorkshop_vf.pdf"> ' \
               'Alvarado et al., 2022</a>]. </p>' \
               '' \
               '<h3>An </p>'\
               ''\
               '<h3>Input</h3>' \
               '<p>The algorithm processes atmospherically corrected satellite data in NETCDF4 and Geotiff formats. </p>' \
               '' \
               '<h3>Sensor</h3>' \
               '<p>Level-2 Chl-a data from the Environmental Mapping and Analysis Program (EnMAP) or ' \
               'the Ocean and Land Colour Instrument (OLCI) onboard Sentinel-3. However, ' \
               'data input from other historical, current and future ocean colour sensors ' \
               'is possible as well (e.g. DESIS, Sentinel 2-MSI). </p>' \
               '' \
               '<h3>Atmospheric correction</h3>' \
               '<p> The Level-2 Chl-a data should be generated with the atmospheric correction (AC) algorithm Polymer ' \
               '[<a href="https://opg.optica.org/oe/fulltext.cfm?uri=oe-19-10-9783&id=213648"> Steinmetz et al., 2011</a>] ' \
               'by pre-processing of EnMAP Level-1B data to Level-2A using ' \
               'the <a href="https://enmap.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/EnPT/doc/"> EnPT</a>. ' \
               'The Chl-a is calculated based on VNIR spectral bands. </p>' \
               '' \
               '<h3>Processor output size</h3>' \
               '<p>The minimum output contains 2 ocean colour products (PFTs) with an estimate of their associated errors, ' \
               'e.g., concentrations of chlorophyll-a, diatoms, dinoflagallates, prokaryotes, prochloroccocus sp., ' \
               'haptophytes, and green algae. </p>' \
               '' \
               '<h3>Output Folder</h3>' \
               '<p>Specify where to save the output.  </p>'
        return html

    # 6
    # def helpUrl(self, *args, **kwargs):
    #     return 'https://enmap-box-workshop2019.readthedocs.io'
# 7
    def createInstance(self):
        return type(self)()
