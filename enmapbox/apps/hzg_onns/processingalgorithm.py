# 0
from qgis.core import *
from .core import onns

# 1
class OnnsProcessingAlgorithm(QgsProcessingAlgorithm):

    P_FILE = 'innc'
    P_SENSOR = 'sensor'
    P_ADAPT = 'adapt'
    P_AC = 'ac'
    P_OSIZE = 'osize'

    P_OUTPUT_FOLDER = 'outfolder'

    SENSORS_ALGO = ['OLCI', "MERIS", "VIIRS", "MODIS", "EnMAP", "GOCI2", "OCM2", "PACE", "SeaWiFS", "SGLI"]
    SENSORS_USER = ['OLCI (Ocean and Land Colour Instrument, Europe)', "MERIS (Medium Resolution Imaging Spectrometer, Europe)", "VIIRS (Visible Infrared Imaging Radiometer Suite, USA)", "MODIS (Moderate Resolution Imaging Spectrometer, USA)", "EnMAP (Environmental Mapping and Analysis Program, Germany)", "GOCI2 (Geostationary Ocean Color Imager, South Korea)", "OCM2 (Ocean Colour Monitor, India)", "PACE (Ocean Color Instrument of the Plankton, Aerosol, Cloud, ocean Ecosystem mission, USA)", "SeaWiFS (Sea-Viewing Wide Field-of-View Sensor, USA)", "SGLI (Second-Generation Global Imager, Japan)"]
    ADAPT = ['No band shifting', 'First OLCI band (400 nm) is adapted (replaced)', 'All OLCI bands are adapted (replaced)']
    AC = ['C2R', 'POLYMER', 'IPF'] #, 'FUB']
    OSIZE = ['Minimum output', 'Standard output', 'Excessive output']

# 2
    def group(self):
        return 'Water'

    def groupId(self):
        return 'water' # internal id

    def displayName(self):
        return 'ONNS'

    def name(self):
        return 'onns' # internal id
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
            name=self.P_ADAPT,
            description='Band shifting',
            options=self.ADAPT,
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
            defaultValue=1))

        self.addParameter(QgsProcessingParameterFolderDestination(
            name=self.P_OUTPUT_FOLDER, description='Output Folder'))
# 4
    def processAlgorithm(self, parameters, context, feedback):
        assert isinstance(feedback, QgsProcessingFeedback)

        # try to execute the core algorithm
        try:

            cmd, output = onns(inputfile=self.parameterAsFile(parameters, self.P_FILE, context),
                 outputDirectory=self.parameterAsFileOutput(parameters, self.P_OUTPUT_FOLDER, context),
                 sensor=self.SENSORS_ALGO[self.parameterAsEnum(parameters, self.P_SENSOR, context)],
                 adapt=self.parameterAsEnum(parameters, self.P_ADAPT, context),
                 ac=self.parameterAsEnum(parameters, self.P_AC, context) + 1,        # note that we deleted the insitu case!!!
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
       '<p>ONNS (OLCI Neural Network Swarm) is a bio-geo-optical algorithm for the retrieval of water quality ' \
       'parameters from satellite imagery or in situ radiometric measurements [' \
       '<a href="https://www.frontiersin.org/articles/10.3389/fmars.2017.00140/full">Hieronymi et al., 2017</a>' \
       ']. </p>' \
       '' \
       '<h3>Input</h3>' \
       '<p>The algorithm processes atmospherically corrected satellite data in NETCDF4 format. </p>' \
       '' \
       '<h3>Sensor</h3>' \
       '<p>The algorithm has been designed for data processing from the Ocean and Land Colour Instrument (OLCI) ' \
       'onboard Sentinel-3. However, data input from other historical, current and future ocean colour sensor is ' \
       'possible too, e.g. from SeaWiFS, MODIS, MERIS, OCM-2, VIIRS, SGLI, GOCI-2, EnMAP or PACE. </p>' \
       '' \
       '<h3>Band-shifting</h3>' \
       '<p>The algorithm requires input at 11 OLCI bands, namely remote-sensing reflectances at 400, 412.5, 442.5, ' \
       '490, 510, 560, 620, 665, 755, 777.5 and 865 nm. A spectral band-shifting procedure is implemented, which ' \
       'allows exploitation of atmospherically corrected input from other ocean colour missions too [' \
       '<a href="https://www.osapublishing.org/oe/fulltext.cfm?uri=oe-27-12-A707&id=412341">Hieronymi, 2019</a>' \
       ']. In case of OLCI data, one has three options: no band-shifting or replacing reflectance input at only one ' \
       'or all spectral bands, e.g. in case of faulty atmospheric correction. In case of MERIS, options 2 and 3 are ' \
       'allowed. Complete band-shifting (option 3) must be applied for all other sensors. </p>' \
       '' \
       '<h3>Atmospheric correction</h3>' \
       '<p>Results of the previously calculated atmospheric correction may vary significantly depending on the water ' \
       'type, which ' \
       'transfers to the ONNS products. For OLCI, three atmospheric correction methods are applicable, namely the ' \
       '"C2R" (Case-2 Regional, standard method for ONNS application) by [' \
       '<a href="https://www.brockmann-consult.de/wp-content/uploads/2017/11/sco1_12brockmann.pdf">Brockmann et al., 2016</a>' \
       '], "Polymer" by ['\
       '<a href="https://www.osapublishing.org/oe/fulltext.cfm?uri=oe-19-10-9783&id=213648">Steinmetz et al., 2011</a>' \
       '] and the standard Level-2 product "IPF". For the other sensors, only "Polymer" is usable. </p>' \
       '' \
       '<h3>Processor output size</h3>' \
       '<p>The minimum output contains 12 ocean colour products with an estimate of their associated uncertainties, ' \
       'e.g. concentrations of chlorophyll and suspended matter as well as different optical water properties. ' \
       'The standard output contains additional derived properties and the input remote-sensing reflectances. ' \
       'In addition, excessive information on optical water type classification can be stored. </p>' \
       '' \
       '<h3>Output Folder</h3>' \
       '<p>Specify where to save the output.  </p>'
       return html
# 6
    def helpUrl(self, *args, **kwargs):
        return 'https://enmap-box-workshop2019.readthedocs.io'
# 7
    def createInstance(self):
        return type(self)()
