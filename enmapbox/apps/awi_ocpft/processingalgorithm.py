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
    AC = ['ENPT-ACWATER Polymer', 'POLYMER'] # ONNS and other options will be added
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
               '<p> OC-PFT is an abundance based approach for the retrieval of Phytoplankton Functional Types (PFTs) ' \
               'from satellite or in situ chlorophyll-a (Chl-a) measurements using functions describing the relationship ' \
               'between PFT specific Chl-a to total Chl-as obtained from a large HPLC based phytoplankton pigment data set. ' \
               'Prior to this specific pigments serving as marker pigment for specific PFT have been converted to ' \
               'specific PFT-Chl-a applying the diagnostic pigment analysis ' \
               '[<a href="https://www.frontiersin.org/articles/10.3389/fmars.2017.00203/full">using Losa et al.,2017</a>; ' \
               '<a href="https://www.awi.de/en/science/climate-sciences/physical-oceanography/main-research-focus/ocean-optics/publications/non-peer-reviewed-articles.html#c33874"> ' \
               'updated as in Alvarado et al., 2022</a>]. </p>' \
               '' \
               '<h3>Input</h3>' \
               '<p>The level-2 Chl-a data in NETCDF4 (Standard Polymer output) and GeoTiff formats (EnPT-ACWater output). </p>' \
               '' \
               '<h3>Sensor</h3>' \
               '<p>Level-2 Chl-a data from the Environmental Mapping and Analysis Program (EnMAP) or ' \
               'the Ocean and Land Colour Instrument (OLCI) onboard Sentinel-3. ' \
               'Data input from other historical, current and future ocean colour sensors ' \
               'is possible as well (e.g. DESIS, Sentinel 2-MSI). </p>' \
               '' \
               '<h3>Model</h3>' \
               '<p> Two models can be applied to the Level-2 Chl-a, global and Lake Constance. ' \
               'The first one is developed using for model development global in-situ data ' \
               '[<a href="https://doi.pangaea.de/10.1594/PANGAEA.954738">Xi et al., 2023</a>]) ' \
               'to derive PFT functions to relate the PFT specific Chl-a to the the total Chl-a, ' \
               'while the second corresponds to an in-situ data set specific Lake Constance (from LUBW-ISF).  </p>' \
               '' \
               '<h3>Atmospheric correction</h3>' \
               '<p> The EnMAP Level-2 Chl-a is generated by EnPT and uses the Polymer algorithm for atmospheric correction ' \
               'over water. Polymer is a spectral matching algorithm in which atmospheric and oceanic signals are obtained ' \
               'simultaneously using the fully available visible spectrum. The algorithm was developed by ' \
               '<a href="https://www.hygeos.com/"> Hygeos</a>; it is available as a python package and it has been largely ' \
               'applied to ocean colour sensors. The Polymer algorithm was integrated into EnPT using the wrapper module ' \
               'ACwater developed by AWI in cooperation with GFZ. In addition, Polymer was further adapted to process ' \
               'EnMAP L1B satellite data. For details on the underlying Polymer algorithm, please refer to ' \
               '<a href="https://doi.org/10.1364/OE.19.009783">Steinmetz et al., 2011</a> ' \
               '<a href="https://www.mdpi.com/1424-8220/21/12/4125"> and Soppa et al. 2021</a>. ' \
               '' \
               '<h3>Processor output size</h3>' \
               '<p>The output contains ocean colour products (PFT concentrations:  1) Chlorophyll-a; ' \
               '2) Diatoms; 3) Dinoflagellates; 4) Prokaryotes; 5) Prochlorococcus sp; 6) Haptophytes;  ' \
               '7) Green Algae; 8) Cryptophytes. </p>' \
               '' \
               '<h3>Output Folder</h3>' \
               '<p>Specify where to save the output.  </p>'
        return html

# 7
    def createInstance(self):
        return type(self)()
