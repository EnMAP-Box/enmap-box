import sys

from qgis.core import *

#from enmapbox.qgispluginsupport.qps.speclib.core import SpectralLibrary
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibrary
from _classic.hubflow.core import *
import _classic.hubdc.progressbar
#from _classic.enmapboxgeoalgorithms import ENMAPBOXGEOALGORITHMS_VERSION
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm

TESTALGORITHMS = list()
ALGORITHMS = list()


class EnMAPProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        # for a in TESTALGORITHMS: self.addAlgorithm(a)
        for a in ALGORITHMS: self.addAlgorithm(a)

    def id(self):
        return 'EnMAPBoxTestProvider'

    def name(self):
        return 'EnMAP-Box Test Provider'

    def longName(self):
        #version = ENMAPBOXGEOALGORITHMS_VERSION
        return 'EnMAP-Box TestProvider'

    def supportsNonFileBasedOutput(self):
        return False


class Link():
    def __init__(self, url, name):
        self.url = url
        self.name = name


class Help(object):
    def __init__(self, text='undocumented', links=()):
        for link in links:
            assert isinstance(link, Link)
        self.text = text
        self.links = links

    def html(self):
        htmlLinks = [r'<a href="{url}">{name}</a>'.format(url=link.url, name=link.name) for link in self.links]
        htmlText = self.text.format(*htmlLinks)
        htmlText = htmlText.replace('\n', '<br>')
        return htmlText

    def rst(self):
        rstLinks = [r'`{name} <{url}>`_'.format(url=link.url, name=link.name) for link in self.links]
        rstText = self.text.format(*rstLinks)
        rstText = rstText.replace('\n', '\n\n')
        return rstText

    def tooltip(self):
        links = [link.name for link in self.links]
        tooltip = self.text.format(*links)
        return tooltip


# help = Help('abc {} def {} dsa', (Link('www.google.de', 'Google'), Link('www.google.de', 'Google')))
# print(help.html())
# print(help.tooltip())
# exit()

class Cookbook(object):
    URL = r'https://enmap-box.readthedocs.io/en/latest/usr_section/usr_cookbook'
    R_CLASSIFICATION = 'Classification'
    R_REGRESSION = 'Regression'
    R_CLUSTERING = 'Clustering'
    R_TRANSFORMATION = 'Transformation'
    R_FILTERING = 'Filtering'
    R_GRAPHICALMODELER = 'Graphical Modeler'
    R_GENERICFILTER = 'Generic Filter'
    LINK = {R_CLASSIFICATION: 'classification.html',
            R_REGRESSION: 'regression.html',
            R_CLUSTERING: 'clustering.html',
            R_TRANSFORMATION: 'transformation.html',
            R_FILTERING: 'filtering.html',
            R_GRAPHICALMODELER: 'graphical_modeler.html',
            R_GENERICFILTER: 'generic_filter.html'
            }

    @classmethod
    def url(cls, key):
        return '{}/{}'.format(cls.URL, cls.LINK[key])


class EnMAPAlgorithm(QgisAlgorithm):
    GROUP_ACCURACY_ASSESSMENT = 'Accuracy Assessment'
    GROUP_AUXILLIARY = 'Auxilliary'
    GROUP_CONVOLUTION = 'Convolution, Morphology and Filtering'
    GROUP_CREATE_RASTER = 'Create Raster'
    GROUP_CREATE_SAMPLE = 'Create Sample'
    GROUP_CLASSIFICATION = 'Classification'
    GROUP_CLUSTERING = 'Clustering'
    GROUP_IMPORT_DATA = 'Import Data'
    GROUP_MASKING = 'Masking'
    GROUP_OPTIONS = 'Options'
    GROUP_PREPROCESSING = 'Pre-Processing'
    GROUP_POSTPROCESSING = 'Post-Processing'
    GROUP_RESAMPLING = 'Resampling and Subsetting'
    GROUP_RANDOM = 'Random'
    GROUP_REGRESSION = 'Regression'
    GROUP_TEST = 'TEST'
    GROUP_TESTDATA = 'Testdata'
    GROUP_TRANSFORMATION = 'Transformation'

    def cookbookRecipes(self):
        return []

    def cookbookDescription(self):
        return 'Used in the Cookbook Recipes:'

    def initAlgorithm(self, configuration=None):
        self._configuration = configuration
        self.defineCharacteristics()

    def group(self):
        assert 0

    def displayName(self):
        assert 0

    def _generateId(self, name):
        id = name
        for c in ' !?-+/*()[]{}':
            id = id.replace(c, '')
        return id

    def groupId(self):
        groupId = self._generateId(self.group())
        return groupId

    def name(self):
        name = self._generateId(self.displayName())
        return name

    def validateInputCrs(self, parameters, context):
        return True  # we accept different crs per default

    def defineCharacteristics(self):
        assert 0, 'overload this methode!'

    def processAlgorithm(self, parameters, context, feedback):

        try:
            self._feedback = feedback
            self._progressBar = ProgressBar(feedback=feedback)
            self._context = context
            self._parameters = parameters
            result = self.processAlgorithm_()
            assert isinstance(result,
                              dict), 'return value error, expected a dict as return value, check {}.processAlgorithm_()'.format(
                self.__class__.__name__)
            return result
        except EnMAPAlgorithmParameterValueError as error:
            feedback.reportError(str(error))
            return {}
        except:

            import traceback
            traceback.print_exc()
            for line in traceback.format_exc().split('\n'):
                feedback.reportError(line)  # .replace('\n', '<br>')
            raise Exception('unexpected error')
            # return {}

    def addParameter_(self, parameterDefinition, help=None):
        self.addParameter(parameterDefinition=parameterDefinition)
        if help is None:
            help = Help('undocumented parameter')
        if isinstance(help, str):
            help = Help(help)
        assert isinstance(help, Help)
        parameterDefinition._help = help
        parameterDefinition.toolTip = lambda: help.tooltip()

    P_RASTER = 'raster'

    def addParameterRaster(self, name=P_RASTER, description='Raster', defaultValue=None, optional=False, help=None):
        if help is None:
            help = 'Specify input raster.'
        self.addParameter_(QgsProcessingParameterRasterLayer(name=name, description=description,
                                                             defaultValue=defaultValue, optional=optional),
                           help=help)

    def getParameterRaster(self, name=P_RASTER):
        assert name in self._parameters
        qgsRasterLayer = self.parameterAsRasterLayer(self._parameters, name, self._context)
        if qgsRasterLayer is None:
            return None
        elif isinstance(qgsRasterLayer, QgsRasterLayer):
            filename = qgsRasterLayer.source()
            return Raster(filename=filename)
        else:
            assert 0, repr(qgsRasterLayer)

    P_BAND = 'band'

    def addParameterBand(self, name=P_BAND, description='Band', defaultValue=None, parentLayerParameterName=P_RASTER,
                         optional=False, help=None):
        if help is None:
            help = 'Specify input raster band.'
        self.addParameter_(QgsProcessingParameterBand(name=name, description=description, defaultValue=defaultValue,
                                                      parentLayerParameterName=parentLayerParameterName,
                                                      optional=optional),
                           help=help)

    def getParameterBand(self, name=P_BAND):
        assert name in self._parameters
        band = self._parameters[name]
        if band == -1:
            band = None
        return band

    P_CLASSIFICATION = 'classification'

    def addParameterClassification(self, name=P_CLASSIFICATION, description='Classification', optional=False,
                                   help=None):

        self.addParameterRaster(name=name, description=description, optional=optional, help=help)

    def getParameterClassification(self, name=P_CLASSIFICATION, minOverallCoverage=0.5, minDominantCoverage=0.5):
        if self.getParameterRaster(name=name) is None:
            return None
        else:
            return Classification(filename=self.getParameterRaster(name=name).filename(),
                                  minOverallCoverage=minOverallCoverage,
                                  minDominantCoverage=minDominantCoverage)

    P_REGRESSION = 'regression'

    def addParameterRegression(self, name=P_REGRESSION, description='Regression', optional=False, help=None):
        self.addParameterRaster(name=name, description=description, optional=optional, help=help)

    def getParameterRegression(self, name=P_REGRESSION, minOverallCoverage=0.5):
        if self.getParameterRaster(name=name) is None:
            return None
        else:
            return Regression(filename=self.getParameterRaster(name=name).filename(),
                              minOverallCoverage=minOverallCoverage)

    P_FRACTION = 'fraction'

    def addParameterFraction(self, name=P_FRACTION, description='ClassFraction', optional=False, help=None):
        self.addParameterRaster(name=name, description=description, optional=optional, help=help)

    def getParameterFraction(self, name=P_FRACTION, minOverallCoverage=0.5, minDominantCoverage=0.5):
        if self.getParameterRaster(name=name) is None:
            return None
        else:
            return Fraction(filename=self.getParameterRaster(name=name).filename(),
                            minOverallCoverage=minOverallCoverage,
                            minDominantCoverage=minDominantCoverage)

    P_MASK = 'mask'

    def addParameterMask(self, name=P_MASK, description='Mask', optional=True, allowRaster=True, allowVector=True,
                         help=None):
        if help is None:
            help = 'Specified vector or raster is interpreted as a boolean mask.\n' \
                   'In case of a vector, all pixels covered by features are interpreted as True, all other pixels as False.\n' \
                   'In case of a raster, all pixels that are equal to the no data value (default is 0) are interpreted as False, all other pixels as True.' \
                   'Multiband rasters are first evaluated band wise. The final mask for a given pixel is True, if all band wise masks for that pixel are True.'

        if allowRaster and allowVector:
            self.addParameterMap(name=name, description=description, optional=optional, help=help)
        elif allowRaster:
            self.addParameterRaster(name=name, description=description, optional=optional, help=help)
        elif allowVector:
            self.addParameterVector(name=name, description=description, optional=optional, help=help)
        else:
            assert 0

    def getParameterMask(self, name=P_MASK, minOverallCoverage=0.5):
        mask = self.getParameterMap(name=name)
        if isinstance(mask, Raster):
            mask = Mask(filename=mask.filename(), minOverallCoverage=minOverallCoverage)
        elif isinstance(mask, Vector):
            mask = VectorMask(filename=mask.filename())
        return mask

    P_INVERT_MASK = 'invertMask'

    def addParameterInvertableMask(self, name=P_MASK, description='Mask', optional=True,
                                   allowRaster=True, allowVector=True, help=None):
        self.addParameterMask(name=name, description=description, optional=optional,
                              allowRaster=allowRaster, allowVector=allowVector, help=help)
        self.addParameterBoolean(name=self.P_INVERT_MASK, description='Invert Mask',
                                 help='Whether or not to invert the selected mask.')

    def getParameterInvertableMask(self, name=P_MASK, minOverallCoverage=0.5):
        mask = self.getParameterMask(name=name, minOverallCoverage=minOverallCoverage)
        if self.getParameterBoolean(name=self.P_INVERT_MASK):

            if isinstance(mask, Mask):
                mask = Mask(filename=mask.filename(), noDataValues=mask.noDataValues(),
                            minOverallCoverage=mask.minOverallCoverage(), indices=mask.indices(),
                            invert=not mask.invert())
            elif isinstance(mask, VectorMask):
                mask = VectorMask(filename=mask.filename(), layer=mask.layer(), invert=True)
            else:
                assert 0
        return mask

    P_VECTOR = 'vector'

    def addParameterVector(self, name=P_VECTOR, description='Vector', defaultValue=None, optional=False,
                           help=None):
        if help is None:
            help = 'Specify input vector.'

        self.addParameter_(QgsProcessingParameterVectorLayer(name=name, description=description,
                                                             defaultValue=defaultValue, optional=optional),
                           help=help)

    def getParameterVector(self, name=P_VECTOR, **kwargs):
        assert name in self._parameters
        qgsVectorLayer = self.parameterAsVectorLayer(self._parameters, name, self._context)

        if qgsVectorLayer is None:
            return None
        elif isinstance(qgsVectorLayer, QgsVectorLayer):
            filename = qgsVectorLayer.source()
            return Vector(filename=filename, **kwargs)
        else:
            assert 0, repr(qgsVectorLayer)

    P_VECTOR_LIBRARY = 'vectorLibrary'

    def addParameterVectorLibrary(self, name=P_VECTOR_LIBRARY, description='Library', defaultValue=None, optional=False,
                                  help=None):
        if help is None:
            help = 'Specify input library.'

        self.addParameter_(QgsProcessingParameterVectorLayer(name=name, description=description,
                                                             defaultValue=defaultValue, optional=optional),
                           help=help)

    def getParameterVectorLibrary(self, name=P_VECTOR_LIBRARY, **kwargs):
        assert name in self._parameters
        qgsVectorLayer = self.parameterAsVectorLayer(self._parameters, name, self._context)

        if qgsVectorLayer is None:
            return None
        elif isinstance(qgsVectorLayer, QgsVectorLayer):
            filename = qgsVectorLayer.source()
            return SpectralLibrary(uri=filename)
        else:
            assert 0, repr(qgsVectorLayer)

    P_MAP = 'map'

    def addParameterMap(self, name=P_MAP, description='Map', defaultValue=None, optional=False, help=None):
        self.addParameter_(QgsProcessingParameterMapLayer(name=name, description=description,
                                                          defaultValue=defaultValue, optional=optional),
                           help=help)

    def getParameterMap(self, name=P_MAP):
        assert name in self._parameters, name
        qgsMapLayer = self.parameterAsLayer(self._parameters, name, self._context)
        if qgsMapLayer is None:
            return None
        elif isinstance(qgsMapLayer, QgsRasterLayer):
            filename = qgsMapLayer.source()
            return Raster(filename=filename)
        elif isinstance(qgsMapLayer, QgsVectorLayer):
            filename = qgsMapLayer.source()
            return Vector(filename=filename)
        else:
            assert 0, repr(qgsMapLayer)

    P_CLASSIFICATION_ATTRIBUTE = 'classificationAttribute'

    def addParameterVectorClassification(self, name=P_VECTOR, description='Vector', defaultValue=None, optional=False,
                                         minCoveragesDefaultValues=(None, None), hideMinDominantCoverage=False,
                                         oversamplingDefaultValue=1):
        self.addParameterVector(name=name, description=description, defaultValue=defaultValue, optional=optional)
        self.addParameterField(name=self.P_CLASSIFICATION_ATTRIBUTE, description='Class id attribute',
                               parentLayerParameterName=name,
                               type=QgsProcessingParameterField.Numeric,
                               help='Vector field specifying the class ids.')

        self.addParameterMinCoverages(defaultValues=minCoveragesDefaultValues,
                                      hideMinDominantCoverage=hideMinDominantCoverage)
        self.addParameterOversampling(defaultValue=oversamplingDefaultValue)

    def getParameterVectorClassification(self):
        return VectorClassification(filename=self.getParameterVector().filename(),
                                    classAttribute=self.getParameterField(self.P_CLASSIFICATION_ATTRIBUTE),
                                    minOverallCoverage=self.getParameterMinOverallCoverage(),
                                    minDominantCoverage=self.getParameterMinDominantCoverage(),
                                    oversampling=self.getParameterOversampling())

    P_REGRESSION_ATTRIBUTE = 'regressionAttribute'

    def addParameterVectorRegression(self, name=P_VECTOR, description='Vector', defaultValue=None, optional=False,
                                     minCoveragesDefaultValues=(None, None), oversamplingDefaultValue=1):
        self.addParameterVector(name=name, description=description, defaultValue=defaultValue, optional=optional)
        self.addParameterField(name=self.P_REGRESSION_ATTRIBUTE, description='Regression value attribute',
                               parentLayerParameterName=name,
                               type=QgsProcessingParameterField.Numeric,
                               help='Vector field specifying the regression values.')
        self.addParameterNoDataValue()
        self.addParameterMinCoverages(defaultValues=minCoveragesDefaultValues, hideMinDominantCoverage=True)
        self.addParameterOversampling(defaultValue=oversamplingDefaultValue)

    def getParameterVectorRegression(self):
        return VectorRegression(filename=self.getParameterVector().filename(),
                                regressionAttribute=self.getParameterField(self.P_REGRESSION_ATTRIBUTE),
                                noDataValue=self.getParameterNoDataValue(),
                                minOverallCoverage=self.getParameterMinOverallCoverage(),
                                oversampling=self.getParameterOversampling())

    P_MIN_OVERALL_COVERAGE = 'minOverallCoverage'

    def addParameterMinOverallCoverage(self, name=P_MIN_OVERALL_COVERAGE, description='Minimal overall coverage',
                                       defaultValue=0.5):

        help = 'Mask out all pixels that have an overall coverage less than the specified value. This controls how edges between labeled and no data regions are treated.'
        self.addParameterFloat(name=name, description=description, minValue=0., maxValue=1.,
                               defaultValue=defaultValue, help=help)

    P_MIN_DOMINANT_COVERAGE = 'minDominantCoverage'

    def addParameterMinDominantCoverage(self, name=P_MIN_DOMINANT_COVERAGE, description='Minimal dominant coverage',
                                        defaultValue=0.5):

        help = 'Mask out all pixels that have a coverage of the predominant class less than the specified value. This controls pixel purity.'
        self.addParameterFloat(name=name, description=description, minValue=0., maxValue=1.,
                               defaultValue=defaultValue, help=help)

    def addParameterMinCoverages(self, defaultValues=(0.5, 0.5), hideMinDominantCoverage=False):
        self.addParameterMinOverallCoverage(defaultValue=defaultValues[0])
        if not hideMinDominantCoverage:
            self.addParameterMinDominantCoverage(defaultValue=defaultValues[1])

    def getParameterMinOverallCoverage(self, name=P_MIN_OVERALL_COVERAGE):
        return self.getParameterFloat(name=name)

    def getParameterMinDominantCoverage(self, name=P_MIN_DOMINANT_COVERAGE):
        if name not in self._parameters:
            return 0.
        else:
            return self.getParameterFloat(name=name)

    P_OVERSAMPLING = 'oversampling'

    def addParameterOversampling(self, name=P_OVERSAMPLING, defaultValue=1, description='Oversampling factor'):
        help = 'Defines the degree of detail by which the class information given by the vector is rasterized. ' \
               'An oversampling factor of 1 (default) simply rasterizes the vector on the target pixel grid.' \
               'An oversampling factor of 2 will rasterize the vector on a target pixel grid with resolution twice as fine.' \
               'An oversampling factor of 3 will rasterize the vector on a target pixel grid with resolution three times as fine, ... and so on.\n' \
               'Mind that larger values are always better (more accurate), but depending on the inputs, this process can be quite computationally intensive, when a higher factor than 1 is used.'
        self.addParameterInteger(name=name, description=description, minValue=1, maxValue=10, defaultValue=defaultValue,
                                 help=help)

    def getParameterOversampling(self, name=P_OVERSAMPLING):
        return self.getParameterInteger(name=name)

    P_FIELD = 'field'

    def addParameterField(self, name=P_FIELD, description='Field', defaultValue=None,
                          parentLayerParameterName=P_VECTOR, type=QgsProcessingParameterField.Any,
                          allowMultiple=False, optional=False, help=None):
        if help is None:
            help = 'Specify field of vector layer for which unique values should be derived.'

        self.addParameter_(QgsProcessingParameterField(name=name, description=description, defaultValue=defaultValue,
                                                       parentLayerParameterName=parentLayerParameterName,
                                                       type=type, allowMultiple=allowMultiple, optional=optional),
                           help=help)

    def getParameterField(self, name=P_FIELD):
        assert name in self._parameters
        return self._parameters[name]

    P_STRING = 'string'

    def addParameterString(self, name=P_STRING, description='String', defaultValue=None,
                           multiLine=False, optional=False, help=None):
        self.addParameter_(QgsProcessingParameterString(name=name, description=description, defaultValue=defaultValue,
                                                        multiLine=multiLine, optional=optional), help=help)

    def getParameterString(self, name=P_STRING):
        assert name in self._parameters, name
        string = str(self._parameters[name])
        return string

    P_STRING_LIST = 'stringList'

    def addParameterStringList(self, name=P_STRING_LIST, description='StringList', defaultValue=None,
                               multiLine=False, optional=False, help=None):
        self.addParameterString(name=name, description=description, defaultValue=defaultValue,
                                multiLine=multiLine, optional=optional, help=help)

    def getParameterStringList(self, name=P_STRING_LIST, separator=','):
        string = self.getParameterString(name=name)
        if string == '':
            stringList = []
        else:
            stringList = [s.strip() for s in string.split(separator)]
        return stringList

    P_INTEGER = 'integer'

    def addParameterInteger(self, name=P_INTEGER, description='Integer', defaultValue=0, optional=False,
                            minValue=None, maxValue=None, help=None):

        if minValue is None:
            minValue = -sys.maxsize
        if maxValue is None:
            maxValue = sys.maxsize

        self.addParameter_(QgsProcessingParameterNumber(name=name, description=description,
                                                        type=QgsProcessingParameterNumber.Integer,
                                                        defaultValue=defaultValue, optional=optional, minValue=minValue,
                                                        maxValue=maxValue), help=help)

    def getParameterInteger(self, name=P_INTEGER):
        assert name in self._parameters, name
        # number = self.parameterAsInt(parameters=self._parameters, name=name, context=self._context) # returned wrong numbers!?
        number = int(round(self._parameters[name], 0))
        return number

    P_FLOAT = 'float'

    def addParameterFloat(self, name=P_FLOAT, description='Float', defaultValue=0., optional=False,
                          minValue=None, maxValue=None, help=None):

        if minValue is None:
            minValue = -sys.maxsize
        if maxValue is None:
            maxValue = sys.maxsize

        self.addParameter_(QgsProcessingParameterNumber(name=name, description=description,
                                                        type=QgsProcessingParameterNumber.Double,
                                                        defaultValue=defaultValue, optional=optional, minValue=minValue,
                                                        maxValue=maxValue), help=help)

    def getParameterFloat(self, name=P_FLOAT):
        assert name in self._parameters, name
        # number = self.parameterAsDouble(parameters=self._parameters, name=name, context=self._context)
        number = float(self._parameters[name])
        return number

    P_BOOLEAN = 'boolean'

    def addParameterBoolean(self, name=P_BOOLEAN, description='Boolean', defaultValue=0, optional=False, help=None):

        self.addParameter_(QgsProcessingParameterBoolean(name=name, description=description, defaultValue=defaultValue,
                                                         optional=optional), help=help)

    def getParameterBoolean(self, name=P_BOOLEAN):
        assert name in self._parameters, name
        boolean = self._parameters[name]
        return boolean

    P_NO_DATA_VALUE = 'noDataValue'

    def addParameterNoDataValue(self, name=P_NO_DATA_VALUE, description='No Data Value', optional=False):
        self.addParameterString(name=name, description=description, optional=optional,
                                help='Specify output no data value.')

    def getParameterNoDataValue(self, name=P_NO_DATA_VALUE):
        string = self.getParameterString(name=name)
        if string in ['', 'None', None]:
            noDataValue = None
        else:
            noDataValue = float(string)
        return noDataValue

    P_LIST = 'list'

    def addParameterList(self, name=P_LIST, description='List', defaultValue=None, multiLine=False,
                         optional=False, help=None):
        if defaultValue is None:
            defaultValue = '[]'
        self.addParameterString(name=name, description=description, defaultValue=defaultValue, multiLine=multiLine,
                                optional=optional, help=help)

    def getParameterList(self, name=P_LIST, type=None):
        text = self.getParameterString(name=name)
        values = eval(text)
        assert isinstance(values, list)
        if type is not None:
            for v in values:
                assert isinstance(v, type)
        return values

    P_ENUM = 'enum'

    def addParameterEnum(self, name=P_ENUM, description='Enumerate', options=None, allowMultiple=False,
                         defaultValue=None, optional=False, help=None):

        self.addParameter_(QgsProcessingParameterEnum(name=name, description=description, options=options,
                                                      allowMultiple=allowMultiple, defaultValue=defaultValue,
                                                      optional=optional), help=help)

    def getParameterEnum(self, name=P_ENUM):
        assert name in self._parameters, name
        # selection = self.parameterAs???(parameters=self._parameters, name=name, context=self._context)
        selection = int(self._parameters[name])
        return selection

    P_DATA_TYPE = 'dataType'
    DATA_TYPES = ((numpy.int16, 'Integer 16 Bit'),
                  (numpy.int32, 'Integer 32 Bit'),
                  (numpy.int64, 'Integer 64 Bit'),
                  (numpy.uint8, 'Unsigned Integer 8 Bit'),
                  (numpy.uint16, 'Unsigned Integer 16 Bit'),
                  (numpy.uint32, 'Unsigned Integer 32 Bit'),
                  (numpy.uint64, 'Unsigned Integer 64 Bit'),
                  (numpy.float32, 'Single Precision Float 32 Bit'),
                  (numpy.float64, 'Double precision float 64 Bit'))
    DATA_TYPE_TYPES, DATA_TYPE_NAMES = zip(*DATA_TYPES)

    def addParameterDataType(self, name=P_DATA_TYPE, description='Data Type', defaultValue=7):
        self.addParameterEnum(name=name, description=description, options=self.DATA_TYPE_NAMES,
                              defaultValue=defaultValue,
                              help='Specify output datatype.')

    def getParameterDataType(self, name=P_DATA_TYPE):
        selection = self.getParameterEnum(name=name)
        return self.DATA_TYPE_TYPES[selection]

    P_GDAL_RESAMPLING_ALG = 'resamplingAlg'
    GDAL_RESAMPLING_ALG_IDS, GDAL_RESAMPLING_ALG_NAMES = zip(
        *[(gdal.__dict__[key], key[4:]) for key in (gdal.__dict__.keys()) if key.startswith('GRA_')])

    def addParameterGDALResamplingAlg(self, name=P_GDAL_RESAMPLING_ALG, description='Resampling Algorithm',
                                      defaultValue=0):
        self.addParameterEnum(name=name, description=description, options=self.GDAL_RESAMPLING_ALG_NAMES,
                              defaultValue=defaultValue,
                              help='Specify resampling algorithm.')

    def getParameterGDALResamplingAlg(self, name=P_GDAL_RESAMPLING_ALG):
        selection = self.getParameterEnum(name=name)
        return self.GDAL_RESAMPLING_ALG_IDS[selection]

    P_FILE = 'file'

    def addParameterFile(self, name=P_FILE, description='File', extension=None, defaultValue=None, optional=False,
                         help=None):
        self.addParameter_(QgsProcessingParameterFile(name=name, description=description,
                                                      behavior=QgsProcessingParameterFile.File,
                                                      extension=extension, defaultValue=defaultValue,
                                                      optional=optional), help=help)

    def getParameterFile(self, name=P_FILE):
        assert name in self._parameters, name
        filename = self._parameters[name]
        return filename

    P_LIBRARY = 'library'

    def addParameterLibrary(self, name=P_LIBRARY, description='Library', optional=False,
                            help=None):

        if help is None:
            help = 'Select path to an ENVI Spectral Library file (e.g. .sli or .esl).'
        self.addParameterFile(name=name, description=description, optional=optional,
                              # extension='esl *.sli' two extensions seam not to work
                              help=help)

    def getParameterLibrary(self, name=P_LIBRARY):
        filename = self.getParameterFile(name=name)
        if filename == '':
            library = None
        else:
            library = EnviSpectralLibrary(filename=filename)
        return library

    '''P_CLASS_DEFINITION = 'classDefinition'

    def addParameterClassDefinition(self, name=P_CLASS_DEFINITION, description='Class Definition', defaultValue=None):

        help = Help(text = 'Enter a class definition, e.g.:\n' \
                           "ClassDefinition(names=['Urban', 'Forest', 'Water'], colors=['red', '#00FF00', (0, 0, 255)])\n" \
                           'For supported named colors see the {}.',
                    links=[Link(url='https://www.w3.org/TR/SVG/types.html#ColorKeywords', name='W3C recognized color keyword names')])

        self.addParameterString(name=name, description=description, defaultValue=defaultValue,
                                multiLine=True, optional=True, help=help)

    def getParameterClassDefinition(self, name=P_CLASS_DEFINITION):
        string = self.getParameterString(name=name)
        if string != '':
            classDefinition = eval(string)
        else:
            # get number of classes from vector or raster layer
            if self.P_VECTOR in self._parameters:
                assert self.P_CLASSIDFIELD in self._parameters
                vector = self.getParameterVector(name=self.P_VECTOR)
                classIdField = self.getParameterField(name=self.P_CLASSIDFIELD)
                classes = numpy.max(vector.uniqueValues(attribute=classIdField))
            elif self.P_RASTER in self._parameters:
                assert 0  # todo
            else:
                raise EnMAPAlgorithmParameterValueError('can not evaluate ClassDefinition')
            classDefinition = ClassDefinition(classes=classes)

        assert isinstance(classDefinition, ClassDefinition)
        return classDefinition'''

    P_NUMBER_OF_POINTS = 'numberOfPoints'

    def addParameterNumberOfPoints(self, name=P_NUMBER_OF_POINTS, description='Number of Points',
                                   defaultValue=100, optional=False):
        help = 'Number of points, given as integer or fraction between 0 and 1, to sample from the mask.'

        self.addParameterString(name=name, description=description, defaultValue=str(defaultValue), optional=optional,
                                help=help)

    def getParameterNumberOfPoints(self, name=P_NUMBER_OF_POINTS, funcTotal=None):
        string = self.getParameterString(name)

        if string == '':
            n = None
        else:
            n = eval(string)
            if isinstance(n, int) and n >= 0:
                pass
            elif isinstance(n, float) and n >= 0 and n <= 1:
                total = funcTotal()
                n = int(round(n * total))
            else:
                parameterDefinition = self.parameterDefinition(name)
                raise EnMAPAlgorithmParameterValueError(
                    'Unexpected parameter value ({}): "{}"'.format(parameterDefinition.name, string))
        return n

    P_NUMBER_OF_POINTS_PER_CLASS = 'numberOfPointsPerClass'

    def addParameterNumberOfPointsPerClass(self, name=P_NUMBER_OF_POINTS_PER_CLASS,
                                           description='Number of Points per Class',
                                           defaultValue=100, optional=False):

        help = 'List of number of points, given as integers or fractions between 0 and 1, to sample from each class. If a scalar is specified, the value is broadcasted to all classes. \n\n'

        self.addParameterString(name=name, description=description, defaultValue=str(defaultValue), optional=optional,
                                help=help)

    def getParameterNumberOfPointsPerClass(self, name=P_NUMBER_OF_POINTS_PER_CLASS, classes=None, funcClassTotals=None):
        assert classes is not None

        string = self.getParameterString(name)
        if string == '':
            n = None
        else:
            n = eval(string)

            # turn scalars into list, e.g. [10,10,10] or [0.1, 0.1, 0.1]
            if isinstance(n, (int, float)):
                n = [n] * classes

            # check if list if correct
            if not isinstance(n, list) or len(n) != classes:
                raise EnMAPAlgorithmParameterValueError('Unexpected value (Number of Points per Class): "{}"'.format(
                    string))

            # turn all values into absolute numbers
            totals = None
            for i in range(classes):
                if isinstance(n[i], float):
                    assert n[i] >= 0 and n[i] <= 1
                    if totals is None:
                        totals = funcClassTotals()
                    n[i] = int(round(n[i] * totals[i], 0))

        return n

    P_OUTPUT_RASTER = 'outRaster'

    def addParameterOutputRaster(self, name=P_OUTPUT_RASTER, description='Output Raster', optional=False, help=None):
        parameter = QgsProcessingParameterRasterDestination(name=name, description=description,
                                                            optional=optional)  # , defaultValue='hello.bsq')

        if help is None:
            help = 'Specify output path for raster.'
        self.addParameter_(parameter, help=help)

    def getParameterOutputRaster(self, name=P_OUTPUT_RASTER):
        return self.getParameterOutputFile(name=name)

    P_OUTPUT_VECTOR = 'outVector'

    def addParameterOutputVector(self, name=P_OUTPUT_VECTOR, description='Output Vector', help=None):
        if help is None:
            help = 'Specify output path for the vector.'
        self.addParameter_(QgsProcessingParameterVectorDestination(name=name, description=description
                                                                   # , defaultValue='hello.bsq'
                                                                   ),
                           help=help)

    def getParameterOutputVector(self, name=P_OUTPUT_VECTOR):
        return self.getParameterOutputFile(name=name)

    P_OUTPUT_MASK = 'outMask'

    def addParameterOutputMask(self, name=P_OUTPUT_MASK, description='Output Mask', help=None):
        if help is None:
            help = 'Specify output path for mask raster.'
        self.addParameterOutputRaster(name=name, description=description, help=help)

    def getParameterOutputMask(self, name=P_OUTPUT_MASK):
        return self.getParameterOutputFile(name=name)

    P_OUTPUT_CLASSIFICATION = 'outClassification'

    def addParameterOutputClassification(self, name=P_OUTPUT_CLASSIFICATION, description='Output Classification',
                                         optional=False, help=None):
        if help is None:
            help = 'Specify output path for classification raster.'
        self.addParameterOutputRaster(name=name, description=description, optional=optional, help=help)

    def getParameterOutputClassification(self, name=P_OUTPUT_CLASSIFICATION):
        return self.getParameterOutputFile(name=name)

    P_OUTPUT_REGRESSION = 'outRegression'

    def addParameterOutputRegression(self, name=P_OUTPUT_REGRESSION, description='Output Regression',
                                     optional=False, help=None):
        if help is None:
            help = 'Specify output path for regression raster.'
        self.addParameterOutputRaster(name=name, description=description, optional=optional, help=help)

    def getParameterOutputRegression(self, name=P_OUTPUT_REGRESSION):
        return self.getParameterOutputFile(name=name)

    P_OUTPUT_FRACTION = 'outFraction'

    def addParameterOutputFraction(self, name=P_OUTPUT_FRACTION, description='Output Fraction',
                                   optional=False, help=None):
        if help is None:
            help = 'Specify output path for fraction raster.'
        self.addParameterOutputRaster(name=name, description=description, optional=optional, help=help)

    def getParameterOutputFraction(self, name=P_OUTPUT_FRACTION):
        return self.getParameterOutputFile(name=name)

    P_OUTPUT_REPORT = 'outReport'

    def addParameterOutputReport(self, name=P_OUTPUT_REPORT, description='HTML Report', help=None):
        if help is None:
            help = 'Specify output path for HTML report file (.html).'
        self.addParameter_(QgsProcessingParameterFileDestination(name=name, description=description,
                                                                 fileFilter='HTML files (*.html)'), help)
    def getParameterOutputReport(self, name=P_OUTPUT_REPORT):
        self._progressBar.setText(str(self._parameters))
        filename = self.parameterAsFileOutput(self._parameters, name, self._context)
        return filename

    P_GRID = 'grid'

    def addParameterGrid(self, name=P_GRID, description='Pixel Grid'):
        self.addParameterRaster(name=name, description=description)

    def getParameterGrid(self, name=P_GRID):
        return self.getParameterRaster(name=name).grid()

    P_WAVELENGTH = 'wavelength'

    def addParameterWavelength(self, name=P_WAVELENGTH, description='Wavelength'):
        self.addParameterRaster(name=name, description=description)

    def getParameterWavelength(self, name=P_WAVELENGTH):
        return self.getParameterRaster(name=name).metadataWavelength()

    P_FLOW_OBJECT = 'flowObject'

    def addParameterFlowObject(self, name=P_FLOW_OBJECT, description='FlowObject File', defaultValue=None,
                               optional=False, help=None):
        self.addParameterFile(name=name, description=description, extension='pkl', defaultValue=defaultValue,
                              optional=optional, help=help)

    def getParameterFlowObject(self, name=P_FLOW_OBJECT, cls=FlowObject):
        filename = self.getParameterFile(name)
        try:
            flowObject = cls.unpickle(filename=filename)
        except FlowObjectTypeError as error:
            raise EnMAPAlgorithmParameterValueError(str(error))

        return flowObject

    P_ESTIMATOR = 'estimator'

    def addParameterEstimator(self, name=P_ESTIMATOR, description='Estimator', help=None):
        self.addParameterFlowObject(name=name, description=description, help=help)

    def getParameterEstimator(self, name=P_ESTIMATOR, cls=Estimator):
        return self.getParameterFlowObject(name=name, cls=cls)

    P_CLASSIFIER = 'classifier'

    def addParameterClassifier(self, name=P_CLASSIFIER, description='Classifier', help=None):
        if help is None:
            help = 'Select path to a classifier file (.pkl).'
        self.addParameterEstimator(name=name, description=description, help=help)

    def getParameterClassifier(self, name=P_CLASSIFIER, cls=Classifier):
        return self.getParameterEstimator(name=name, cls=cls)

    P_REGRESSOR = 'regressor'

    def addParameterRegressor(self, name=P_REGRESSOR, description='Regressor', help=None):
        if help is None:
            help = 'Select path to a regressor file (.pkl).'
        self.addParameterEstimator(name=name, description=description, help=help)

    def getParameterRegressor(self, name=P_REGRESSOR, cls=Regressor):
        return self.getParameterEstimator(name=name, cls=cls)

    P_CLUSTERER = 'clusterer'

    def addParameterClusterer(self, name=P_CLUSTERER, description='Clusterer', help=None):
        if help is None:
            help = 'Select path to a clusterer file (.pkl).'
        self.addParameterEstimator(name=name, description=description, help=help)

    def getParameterClusterer(self, name=P_CLUSTERER, cls=Clusterer):
        return self.getParameterEstimator(name=name, cls=cls)

    P_TRANSFORMER = 'transformer'

    def addParameterTransformer(self, name=P_TRANSFORMER, description='Transformer', help=None):
        if help is None:
            help = 'Select path to a transformer file (.pkl).'
        self.addParameterEstimator(name=name, description=description, help=help)

    def getParameterTransformer(self, name=P_TRANSFORMER, cls=Transformer):
        return self.getParameterEstimator(name=name, cls=cls)

    P_OUTPUT_FILE = 'outFile'

    def addParameterOutputFile(self, name=P_OUTPUT_FILE, description='Output File', fileFilter=None,
                               defaultValue=None, optional=False, help=None):
        self.addParameter_(QgsProcessingParameterFileDestination(name=name, description=description,
                                                                 fileFilter=fileFilter,
                                                                 defaultValue=defaultValue,
                                                                 optional=optional), help=help)
        if help is None:
            help = 'Specify output path for file.'
        # self.addOutput(QgsProcessingOutputFile(name=name, description=description))

    def getParameterOutputFile(self, name):
        assert name in self._parameters, name

        if isinstance(self._parameters[name], QgsProcessingOutputLayerDefinition):
            filename = str(self.parameterAsOutputLayer(self._parameters, name, self._context))
        elif isinstance(self._parameters[name], str):
            filename = self._parameters[name]
        else:
            assert 0, repr(self._parameters[name])
        assert isinstance(filename, str), repr(filename)

        if not isabs(filename):
            filename = abspath(join(QgsApplication.qgisSettingsDirPath(), 'processing', 'outputs', filename))
        return filename

    P_OUTPUT_FLOW_OBJECT = 'outFlowObject'

    def addParameterOutputFlowObject(self, name=P_OUTPUT_FLOW_OBJECT, description='Output FlowObject', help=None):
        if help is None:
            help = 'Specify output path for flow object pickle file.'
        self.addParameterOutputFile(name=name, description=description, fileFilter='Pickle files (*.pkl)',
                                    defaultValue='{}.pkl'.format(name),
                                    help=help)

    def getParameterOutputFlowObject(self, name=P_OUTPUT_FLOW_OBJECT):
        filename = self.getParameterOutputFile(name=name)
        ext = os.path.splitext(filename)[1][1:].lower()
        if ext != 'pkl':
            raise EnMAPAlgorithmParameterValueError(
                'Unexpected output pickle ({}) file extension: {}, use pkl instead.'.format(name, ext))

        return filename

    P_OUTPUT_ESTIMATOR = 'outEstimator'

    def addParameterOutputEstimator(self, name=P_OUTPUT_ESTIMATOR, description='Output Estimator', help=None):
        self.addParameterOutputFlowObject(name=name, description=description, help=help)

    def getParameterOutputEstimator(self, name=P_OUTPUT_ESTIMATOR):
        return self.getParameterOutputFlowObject(name=name)

    P_OUTPUT_CLASSIFIER = 'outClassifier'

    def addParameterOutputClassifier(self, name=P_OUTPUT_CLASSIFIER, description='Output Classifier', help=None):
        if help is None:
            help = "Specifiy output path for the classifier (.pkl). This file can be used for applying the classifier to an image using 'Classification -> Predict Classification' and 'Classification -> Predict ClassFraction'."

        self.addParameterOutputEstimator(name=name, description=description, help=help)

    P_OUTPUT_CLUSTERER = 'outClusterer'

    def addParameterOutputClusterer(self, name=P_OUTPUT_CLUSTERER, description='Output Clusterer', help=None):
        if help is None:
            help = "Specifiy output path for the clusterer (.pkl). This file can be used for applying the clusterer to an image using 'Clustering -> Predict Clustering'."
        self.addParameterOutputEstimator(name=name, description=description, help=help)

    P_OUTPUT_REGRESSOR = 'outRegressor'

    def addParameterOutputRegressor(self, name=P_OUTPUT_REGRESSOR, description='Output Regressor', help=None):
        if help is None:
            help = "Specifiy output path for the regressor (.pkl). This file can be used for applying the regressor to an image using 'Regression -> Predict Regression'."
        self.addParameterOutputEstimator(name=name, description=description, help=help)

    P_OUTPUT_TRANSFORMER = 'outTransformer'

    def addParameterOutputTransformer(self, name=P_OUTPUT_TRANSFORMER, description='Output Transformer', help=None):
        if help is None:
            help = "Specifiy output path for the transformer (.pkl). This file can be used for applying the transformer to an image using 'Transformation -> Transform Raster' and 'Transformation -> InverseTransform Raster'."
        self.addParameterOutputEstimator(name=name, description=description, help=help)

    def hasHtmlOutputs(self, *args, **kwargs):
        return False

    def description(self):
        return Help('undocumented algorithm')

    def shortHelpString(self):

        if isinstance(self.description(), str):
            text = '<p>' + self.description() + '</p>'
        elif isinstance(self.description(), Help):
            text = '<p>' + self.description().html() + '</p>'
        else:
            assert 0

        if len(self.cookbookRecipes()) > 0:
            text += '<p>Used in the Cookbook Recipes: '
            for i, key in enumerate(self.cookbookRecipes()):
                url = Cookbook.url(key)
                text += '<a href="{}">{}</a>'.format(url, key)
                if i < len(self.cookbookRecipes()) - 1:
                    text += ', '
            text += '</p>\n\n'

        for pd in self.parameterDefinitions():
            assert isinstance(pd, QgsProcessingParameterDefinition)
            text += '<h3>' + pd.description() + '</h3>'
            text += '<p>' + pd._help.html() + '</p>'

        return text

    def helpString(self):
        return self.shortHelpString()

    def helpUrl(self, *args, **kwargs):
        return 'https://enmap-box.readthedocs.io/en/latest/usr_section/usr_manual/processing_algorithms/processing_algorithms.html'


class ProgressBar(_classic.hubdc.progressbar.ProgressBar):
    def __init__(self, feedback):
        assert isinstance(feedback, QgsProcessingFeedback)
        self.feedback = feedback

    def setText(self, text):
        self.feedback.pushInfo(str(text))

    def setPercentage(self, percentage):
        if percentage == 100:
            return  # setting percentage to 100 would prevent further outputs in QGIS Dialog, at leaset under QGIS 2.x
        self.feedback.setProgress(percentage)


class EnMAPAlgorithmParameterValueError(Exception):
    pass
