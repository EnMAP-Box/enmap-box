import traceback
from enum import Enum
from math import nan
from os import makedirs
from os.path import abspath, dirname, exists, isabs, join, splitext
from time import time
from typing import Any, Dict, Iterable, List, Optional, TextIO, Tuple

import numpy as np
from osgeo import gdal
import processing
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.core import (Qgis, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem, QgsMapLayer,
                       QgsPalettedRasterRenderer, QgsProcessing, QgsProcessingAlgorithm, QgsProcessingContext,
                       QgsProcessingException, QgsProcessingFeedback, QgsProcessingOutputLayerDefinition,
                       QgsProcessingParameterBand, QgsProcessingParameterBoolean, QgsProcessingParameterCrs,
                       QgsProcessingParameterDefinition, QgsProcessingParameterEnum, QgsProcessingParameterExtent,
                       QgsProcessingParameterField, QgsProcessingParameterFile, QgsProcessingParameterFileDestination,
                       QgsProcessingParameterFolderDestination, QgsProcessingParameterMapLayer,
                       QgsProcessingParameterMatrix, QgsProcessingParameterMultipleLayers, QgsProcessingParameterNumber,
                       QgsProcessingParameterRange, QgsProcessingParameterRasterLayer, QgsProcessingParameterString,
                       QgsProcessingParameterVectorDestination, QgsProcessingParameterVectorLayer, QgsProcessingUtils,
                       QgsProject, QgsProperty, QgsRasterLayer, QgsRectangle, QgsVectorLayer)

from enmapbox.typeguard import typechecked
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.glossary import injectGlossaryLinks
from enmapboxprocessing.parameter.processingparameterrasterdestination import ProcessingParameterRasterDestination
from enmapboxprocessing.processingfeedback import ProcessingFeedback
from enmapboxprocessing.typing import ClassifierDump, ClustererDump, CreationOptions, GdalResamplingAlgorithm, \
    RegressorDump, TransformerDump
from enmapboxprocessing.utils import Utils


class AlgorithmCanceledException(Exception):
    pass


@typechecked
class EnMAPProcessingAlgorithm(QgsProcessingAlgorithm):
    O_RESAMPLE_ALG = 'NearestNeighbour Bilinear Cubic CubicSpline Lanczos Average Mode Min Q1 Med Q3 Max'.split()
    NearestNeighbourResampleAlg, BilinearResampleAlg, CubicResampleAlg, CubicSplineResampleAlg, LanczosResampleAlg, \
        AverageResampleAlg, ModeResampleAlg, MinResampleAlg, Q1ResampleAlg, MedResampleAlg, Q3ResampleAlg, \
        MaxResampleAlg = range(12)
    O_DATA_TYPE = 'Byte Int16 UInt16 UInt32 Int32 Float32 Float64'.split()
    Byte, Int16, UInt16, Int32, UInt32, Float32, Float64 = range(len(O_DATA_TYPE))
    PickleFileFilter = 'Pickle files (*.pkl)'
    PickleFileExtension = 'pkl'
    PickleFileDestination = 'Pickle file destination.'
    JsonFileFilter = 'JSON files (*.json)'
    JsonFileExtension = 'json'
    JsonFileDestination = 'JSON file destination.'
    GeoJsonFileFilter = 'GEOJSON files (*.geojson)'
    GeoJsonFileExtension = 'geojson'
    GeoJsonFileDestination = 'GEOJSON file destination.'
    GpkgFileFilter = 'GeoPackage files (*.gpkg)'
    GpkgFileExtension = 'gpkg'
    GpkgFileDestination = 'GeoPackage file destination.'
    CsvFileFilter = 'CSV files (*.csv)'
    CsvFileExtension = 'cvs'
    CsvFileDestination = 'CSV file destination.'
    DatasetFileFilter = PickleFileFilter + ';;' + JsonFileFilter
    DatasetFileDestination = 'Dataset file destination.'
    RasterFileDestination = 'Raster file destination.'
    VectorFileDestination = 'Vector file destination.'
    TableFileDestination = 'Table file destination.'
    ReportFileFilter = 'HTML files (*.html)'
    ReportFileDestination = 'Report file destination.'
    ReportOpen = 'Whether to open the output report in the web browser.'
    FolderDestination = 'Folder destination.'
    VrtFormat = Driver.VrtFormat
    DefaultVrtCreationOptions = Driver.DefaultVrtCreationOptions
    DefaultVrtCreationProfile = VrtFormat + ' ' + ' '.join(DefaultVrtCreationOptions)
    GTiffFormat = Driver.GTiffFormat
    DefaultGTiffCreationOptions = Driver.DefaultGTiffCreationOptions
    DefaultGTiffCreationProfile = GTiffFormat + ' ' + ' '.join(DefaultGTiffCreationOptions)
    EnviFormat = Driver.EnviFormat
    DefaultEnviCreationOptions = Driver.DefaultEnviBsqCreationOptions
    DefaultEnviCreationProfile = EnviFormat + ' ' + ' '.join(DefaultEnviCreationOptions)

    def icon(self):
        return QIcon(':/enmapbox/gui/ui/icons/enmapbox.svg')

    def createInstance(self):
        return type(self)()

    def group(self) -> str:
        raise NotImplementedError()

    def displayName(self) -> str:
        raise NotImplementedError()

    def _generateId(self, name):
        nameId = name
        for c in '!?-+/*()[]{}':
            nameId = nameId.replace(c, '')
        nameId = ''.join([s.title() for s in nameId.split(' ')])
        return nameId

    def groupId(self) -> str:
        return self._generateId(self.group())

    def name(self) -> str:
        return self._generateId(self.displayName())

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        raise NotImplementedError

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raise NotImplementedError()

    def parameterDefinition(self, name: str) -> QgsProcessingParameterDefinition:
        parameter = super().parameterDefinition(name)
        assert parameter is not None, name
        return parameter

    def parameterAsLayer(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[QgsMapLayer]:

        layer = super().parameterAsLayer(parameters, name, context)
        if layer is None:
            return None

        # if layer is given by string (but not by layer ID), ...
        if isinstance(parameters.get(name), str) and parameters.get(name) not in QgsProject.instance().mapLayers():
            layer.loadDefaultStyle()  # ... we need to manually load the default style

        if layer.renderer() is None:  # if we still have no valid renderer...
            layer.loadDefaultStyle()  # ... we also load the dafault style

        return layer

    def parameterAsLayerList(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[List[QgsMapLayer]]:
        layers = super().parameterAsLayerList(parameters, name, context)
        if layers is None or len(layers) == 0:
            return None
        for layer in layers:
            if isinstance(layer, QgsMapLayer) and layer.renderer() is None:
                layer.loadDefaultStyle()
        return layers

    def parameterAsRasterLayer(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[QgsRasterLayer]:
        layer = super().parameterAsRasterLayer(parameters, name, context)

        if layer is None:
            return None

        # if layer is given by string (but not by layer ID), ...
        if isinstance(parameters.get(name), str) and parameters.get(name) not in QgsProject.instance().mapLayers():
            layer.loadDefaultStyle()  # ... we need to manually load the default style

        if layer.renderer() is None:  # if we still have no valid renderer...
            layer.loadDefaultStyle()  # ... we also load the dafault style

        return layer

    def parameterAsSpectralRasterLayer(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext, checkWavelength=True,
            checkFwhm=False
    ) -> Optional[QgsRasterLayer]:
        from enmapboxprocessing.rasterreader import RasterReader

        layer = self.parameterAsRasterLayer(parameters, name, context)
        if layer is not None:
            if checkWavelength:
                if not RasterReader(layer).isSpectralRasterLayer():
                    message = f'Missing wavelength definition for spectral raster layer: {name}'
                    raise QgsProcessingException(message)
            if checkFwhm:
                if not RasterReader(layer).isSpectralRasterLayer():
                    message = f'Missing FWHM definition for spectral raster layer: {name}'
                    raise QgsProcessingException(message)
        return layer

    def parameterAsVectorLayer(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext, convertFromMemoryToOgr=False
    ) -> Optional[QgsVectorLayer]:
        layer = super().parameterAsVectorLayer(parameters, name, context)

        if layer is None:
            return None

        # convert temporary scratch layer to OGR layer
        if layer.dataProvider().name() == 'memory' and convertFromMemoryToOgr:
            renderer = layer.renderer().clone()
            parameters = {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT'}
            feedback = None
            result = self.runAlg('native:savefeatures', parameters, None, feedback, context, True)
            layer = QgsVectorLayer(result['OUTPUT'], layer.name())
            layer.setRenderer(renderer)
            layer.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

        # if parameter is given as filename, we need to manually load the default style
        if isinstance(parameters.get(name), str) or layer.renderer() is None:
            if QgsProject.instance().mapLayer(parameters.get(name)) is not None:
                pass  # do nothing in case of a valid layer ID
            else:
                layer.loadDefaultStyle()

        return layer

    def parameterAsFields(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[List[str]]:
        if Qgis.versionInt() >= 33200:
            fields = super().parameterAsStrings(parameters, name, context)
        else:
            fields = super().parameterAsFields(parameters, name, context)
        if len(fields) == 0:
            return None
        else:
            return fields

    def parameterAsField(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[str]:
        fields = self.parameterAsFields(parameters, name, context)
        if fields is None:
            return None
        else:
            return fields[0]

    def parameterAsFile(self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext) -> Optional[str]:
        filename = super().parameterAsFile(parameters, name, context)
        if filename == '':
            return None
        return filename

    def parameterAsClassifierDump(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[ClassifierDump]:
        filename = super().parameterAsFile(parameters, name, context)
        if filename == '':
            return None
        dump = Utils.pickleLoad(filename)
        dump = ClassifierDump.fromDict(dump)
        return dump

    def parameterAsRegressorDump(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext,
            optionalTargets=False, optionalFeatures=False, optionalX=False, optionalY=False, optionalRegressor=True
    ) -> Optional[RegressorDump]:
        filename = super().parameterAsFile(parameters, name, context)
        if filename == '':
            return None
        dump = Utils.pickleLoad(filename)
        try:
            dump = RegressorDump.fromDict(dump)
        except Exception:
            raise QgsProcessingException(
                f'Wrong or missing parameter value: {self.parameterDefinition(name).description()}'
            )
        for attr, optional in [
            ('targets', optionalTargets), ('features', optionalFeatures), ('X', optionalX), ('y', optionalY),
            ('regressor', optionalRegressor)
        ]:
            if optional:
                continue
            if getattr(dump, attr) is None:
                raise QgsProcessingException(f'Not a valid regression dataset, missing attribute "{attr}": {filename}')

        return dump

    def parameterAsTransformerDump(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[TransformerDump]:
        filename = super().parameterAsFile(parameters, name, context)
        if filename == '':
            return None
        dump = Utils.pickleLoad(filename)
        dump = TransformerDump.fromDict(dump)
        return dump

    def parameterAsClustererDump(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[ClustererDump]:
        filename = super().parameterAsFile(parameters, name, context)
        if filename == '':
            return None
        dump = Utils.pickleLoad(filename)
        dump = ClustererDump.fromDict(dump)
        return dump

    def parameterAsEnum(self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext) -> int:
        return super().parameterAsEnum(parameters, name, context)

    def parameterAsEnums(self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext) -> List[int]:
        return super().parameterAsEnums(parameters, name, context)

    def parameterAsString(self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext) -> Optional[str]:
        string = super().parameterAsString(parameters, name, context)
        if string == '':
            if isinstance(parameters.get(name),
                          str):  # workaround a QGIS bug, where super().parameterAsString would return an empty string instead of the actual string
                return parameters.get(name)
            return None
        return string

    def parameterAsDouble(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[float]:
        if self.parameterIsNone(parameters, name):
            return self.parameterDefinition(name).defaultValue()
        else:
            return super().parameterAsDouble(parameters, name, context)

    parameterAsFloat = parameterAsDouble

    def parameterAsInt(self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext) -> Optional[int]:
        if self.parameterIsNone(parameters, name):
            return self.parameterDefinition(name).defaultValue()
        else:
            if isinstance(parameters[name], int):
                return parameters[name]
            else:
                return super().parameterAsInt(parameters, name, context)

    def parameterAsInts(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[List[int]]:
        ints = super().parameterAsInts(parameters, name, context)
        if len(ints) == 0:
            ints = None
        return ints

    def parameterAsBand(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[int]:
        bandNo = self.parameterAsInt(parameters, name, context)
        if bandNo is None or bandNo == -1:
            return None
        return bandNo

    def parameterAsRange(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[Tuple[float, float]]:
        range = super().parameterAsRange(parameters, name, context)
        if len(range) == 0:
            range = None
        return tuple(range)

    def parameterAsValues(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[List[Optional[Any]]]:
        string = self.parameterAsString(parameters, name, context)
        if string is None:
            return None
        if string == '':
            return None

        string = string.replace('\n', '')
        try:
            values = eval(string, {'nan': nan})
        except Exception as error:
            raise QgsProcessingException(f'Invalid value list: {self.parameterDefinition(name).description()}')

        if not isinstance(values, (tuple, list)):
            values = [values]
        values = list(values)
        return values

    def parameterAsStringValues(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext, allowNoneValues=False,
    ) -> Optional[List[Optional[Any]]]:
        values = self.parameterAsValues(parameters, name, context)
        if values is None:
            return None
        for value in values:
            if allowNoneValues and value is None:
                pass
            elif not isinstance(value, str):
                raise QgsProcessingException(f'invalid string item {value}: {name} ')
        return values

    def parameterAsIntValues(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext, allowNoneValues=False,
    ) -> Optional[List[Any]]:
        values = self.parameterAsValues(parameters, name, context)
        if values is None:
            return None
        for value in values:
            if allowNoneValues and value is None:
                pass
            elif not isinstance(value, int):
                raise QgsProcessingException(f'invalid integer item {value}: {name} ')
        return values

    def parameterAsFloatValues(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext, allowNoneValues=False,
    ) -> Optional[List[Any]]:
        values = self.parameterAsValues(parameters, name, context)
        if values is None:
            return None
        for value in values:
            if allowNoneValues and value is None:
                pass
            elif not isinstance(value, (int, float)):
                raise QgsProcessingException(f'invalid float item {value}: {name} ')
        return values

    def parameterAsBool(self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext) -> bool:
        return super().parameterAsBool(parameters, name, context)

    def parameterAsBoolean(self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext) -> bool:
        return super().parameterAsBoolean(parameters, name, context)

    def parameterAsObject(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[Any]:
        string = self.parameterAsString(parameters, name, context)
        if string is None:
            return None
        if string == '':
            return None
        try:
            value = eval(string, {'nan': nan})
        except Exception:
            raise QgsProcessingException(f'Invalid value: {self.parameterDefinition(name).description()}')

        return value

    def parameterAsFileOutput(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[str]:
        filename = super().parameterAsFileOutput(parameters, name, context)
        if filename == '':
            filename = parameters.get(name, '')
        if filename == '':
            return None
        if filename is None:
            return None
        if not isabs(filename):
            filename = join(QgsProcessingUtils.tempFolder(), filename)
        if isinstance(self.parameterDefinition(name), QgsProcessingParameterFolderDestination):
            if not exists(filename):
                makedirs(filename)
        if isinstance(self.parameterDefinition(name), QgsProcessingParameterFileDestination):
            if not exists(dirname(filename)):
                makedirs(dirname(filename))
        return filename

    def parameterAsOutputLayer(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[str]:
        filename = super().parameterAsOutputLayer(parameters, name, context)

        if filename == '':
            filename = parameters.get(name, '')

        if isinstance(filename, QgsProcessingOutputLayerDefinition):
            sink: QgsProperty = filename.sink
            filename = sink.toVariant()['val']
            assert isinstance(filename, str)

        if filename == '':
            return None
        if not isabs(filename):
            filename = abspath(filename)

        parameterDefinition: ProcessingParameterRasterDestination = self.parameterDefinition(name)
        success, message = parameterDefinition.isSupportedOutputValue(filename, context)
        if not success:
            raise QgsProcessingException(message)

        if not exists(dirname(filename)):
            makedirs(dirname(filename))
        return filename

    def parameterAsCrs(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> QgsCoordinateReferenceSystem:
        if self.parameterIsNone(parameters, name):
            return self.parameterDefinition(name).defaultValue()
        else:
            return super().parameterAsCrs(parameters, name, context)

    def parameterAsExtent(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext,
            crs: QgsCoordinateReferenceSystem
    ) -> QgsRectangle:
        return super().parameterAsExtent(parameters, name, context, crs)

    def parameterAsQgsDataType(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext, default: Qgis.DataType = None
    ) -> Optional[Qgis.DataType]:
        if self.parameterIsNone(parameters, name):
            return default
        else:
            index = self.parameterAsEnum(parameters, name, context)
            label = self.O_DATA_TYPE[index]
            return getattr(Qgis, label)

    def parameterAsGdalResampleAlg(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[GdalResamplingAlgorithm]:
        index = self.parameterAsInt(parameters, name, context)
        if index == -1:
            return None
        label = self.O_RESAMPLE_ALG[index]
        return getattr(gdal, f'GRA_{label}')

    def parameterAsCreationProfile(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext, filename: str
    ) -> Tuple[str, CreationOptions]:
        text = self.parameterAsString(parameters, name, context)
        if text is None or text == '':
            extension = splitext(filename)[1].lower()
            defaultCreationProfilesByExtension = {
                '.tif': self.DefaultGTiffCreationProfile,
                '.bsq': 'ENVI INTERLEAVE=BSQ',
                '.bil': 'ENVI INTERLEAVE=BIL',
                '.bip': 'ENVI INTERLEAVE=BIP',
                '.vrt': self.DefaultVrtCreationProfile,
            }
            text = defaultCreationProfilesByExtension[extension]
        format, *options = text.split()

        # check that extension is correct
        extension = splitext(filename)[1]
        extensions = {'VRT': '.vrt', 'ENVI': '.bsq .bil .bip', 'GTiff': '.tif'}[format].split()
        if extension not in extensions:
            extensions = ' '.join([f'{extension}' for extension in extensions])
            message = f'unsupported file extension ({extension}) for format ({format}), ' \
                      f'use {extensions} instead'
            raise QgsProcessingException(message)
        return format, options

    def parameterAsMatrix(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Optional[List[Any]]:
        value = parameters.get(name)
        if value == [QVariant()]:
            return None
        return value

    def parameterIsNone(self, parameters: Dict[str, Any], name: str):
        return parameters.get(name, None) is None

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        valid, message = super().checkParameterValues(parameters, context)
        return valid, message

    def checkParameterVectorClassification(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Tuple[bool, str]:
        layer = self.parameterAsVectorLayer(parameters, name, context)
        if layer is None:
            return True, ''
        renderer = layer.renderer()
        return (
            isinstance(renderer, QgsCategorizedSymbolRenderer),
            f'Invalid categorized vector layer, '
            f'requires categorized symbol renderer ({self.parameterDefinition(name).description()})'
        )

    def checkParameterRasterClassification(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Tuple[bool, str]:

        layer = self.parameterAsRasterLayer(parameters, name, context)
        if layer is None:
            return True, ''
        renderer = layer.renderer()
        return (
            isinstance(renderer, QgsPalettedRasterRenderer),
            f'Invalid categorized raster layer, '
            f'requires paletted/unique values renderer ({self.parameterDefinition(name).description()})'
        )

    def checkParameterMapClassification(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Tuple[bool, str]:
        layer = self.parameterAsLayer(parameters, name, context)
        if layer is None:
            return True, ''
        elif isinstance(layer, QgsRasterLayer):
            return self.checkParameterRasterClassification(parameters, name, context)
        elif isinstance(layer, QgsVectorLayer):
            return self.checkParameterVectorClassification(parameters, name, context)
        else:
            raise ValueError()

    def checkParameterVectorRegression(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Tuple[bool, str]:
        layer = self.parameterAsVectorLayer(parameters, name, context)
        if layer is None:
            return True, ''
        if Utils.targetsFromLayer(layer) is None:
            return False, 'Invalid continuous-valued vector layer, ' \
                          'requires either a graduated symbol renderer specifying a single target variable, ' \
                          'or a diagram renderer specifying multiple targets. ' \
                          f' ({self.parameterDefinition(name).description()})'
        return True, ''

    def checkParameterRasterRegression(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Tuple[bool, str]:
        return True, ''  # each raster layer is a valid regression layer

    def checkParameterMapRegression(
            self, parameters: Dict[str, Any], name: str, context: QgsProcessingContext
    ) -> Tuple[bool, str]:
        layer = self.parameterAsLayer(parameters, name, context)
        if layer is None:
            return True, ''
        elif isinstance(layer, QgsRasterLayer):
            return self.checkParameterRasterRegression(parameters, name, context)
        elif isinstance(layer, QgsVectorLayer):
            return self.checkParameterVectorRegression(parameters, name, context)
        else:
            raise ValueError()

    def shortDescription(self):
        raise NotImplementedError()

    def helpCookbookUrls(self) -> List[Tuple[str, str]]:
        return []

    def helpParameters(self) -> List[Tuple[str, str]]:
        return []

    def helpHeader(self) -> Optional[Tuple[str, str]]:
        return None

    def shortHelpString(self):
        text = '<p>' + injectGlossaryLinks(self.shortDescription()) + '</p>'
        if self.helpHeader() is not None:
            title, text2 = self.helpHeader()
            text += f' <i><h3>{title}</h3> </i><p>{injectGlossaryLinks(text2)}</p>'
        for name, text2 in self.helpParameters():
            if text2 == '':
                continue
            text += f'<h3>{name}</h3><p>{injectGlossaryLinks(text2)}</p>'
        return text

    def helpString(self):
        return self.shortHelpString()

    def helpUrl(self, *args, **kwargs):
        return 'https://enmap-box.readthedocs.io/en/latest/usr_section/usr_manual/processing_algorithms/processing_algorithms.html'

    def isRunnungInsideModeller(self):
        # hacky way to figure out if this algorithm is currently running inside the modeller
        # needed for fixing issue #504
        for text in traceback.format_stack():
            if 'ModelerDialog.py' in text:
                return True
        return False

    def addParameterClassificationDataset(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        from enmapboxprocessing.parameter.processingparameterpicklefileclassificationdatasetwidget import \
            ProcessingParameterPickleFileClassificationDatasetWidgetWrapper
        behavior = QgsProcessingParameterFile.Behavior.File
        extension = ''
        fileFilter = 'Pickle files (*.pkl);;JSON files (*.json)'
        param = QgsProcessingParameterFile(name, description, behavior, extension, defaultValue, optional, fileFilter)

        if not self.isRunnungInsideModeller():
            param.setMetadata(
                {'widget_wrapper': {'class': ProcessingParameterPickleFileClassificationDatasetWidgetWrapper}})
            param.setDefaultValue(defaultValue)

        self.addParameter(param)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterClassifierCode(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        from enmapboxprocessing.parameter.processingparameterestimatorcodeeditwidget import \
            ProcessingParameterClassifierCodeEditWrapper
        param = QgsProcessingParameterString(name, description, defaultValue, True, optional)
        param.setMetadata({'widget_wrapper': {'class': ProcessingParameterClassifierCodeEditWrapper}})
        param.setDefaultValue(defaultValue)
        self.addParameter(param)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterRegressionDataset(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        from enmapboxprocessing.parameter.processingparameterpicklefileregressiondatasetwidget import \
            ProcessingParameterPickleFileRegressionDatasetWidgetWrapper
        behavior = QgsProcessingParameterFile.Behavior.File
        extension = ''
        fileFilter = 'Pickle files (*.pkl);;JSON files (*.json)'
        param = QgsProcessingParameterFile(name, description, behavior, extension, defaultValue, optional, fileFilter)

        if not self.isRunnungInsideModeller():
            param.setMetadata(
                {'widget_wrapper': {'class': ProcessingParameterPickleFileRegressionDatasetWidgetWrapper}}
            )
            param.setDefaultValue(defaultValue)

        self.addParameter(param)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterRegressorCode(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        from enmapboxprocessing.parameter.processingparameterestimatorcodeeditwidget import \
            ProcessingParameterRegressorCodeEditWrapper
        param = QgsProcessingParameterString(name, description, defaultValue, True, optional)
        param.setMetadata({'widget_wrapper': {'class': ProcessingParameterRegressorCodeEditWrapper}})
        param.setDefaultValue(defaultValue)
        self.addParameter(param)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterUnsupervisedDataset(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        from enmapboxprocessing.parameter.processingparameterpicklefileunsuperviseddatasetwidget import \
            ProcessingParameterPickleFileUnsupervisedDatasetWidgetWrapper
        behavior = QgsProcessingParameterFile.Behavior.File
        extension = ''
        fileFilter = 'Pickle files (*.pkl);;JSON files (*.json)'
        param = QgsProcessingParameterFile(name, description, behavior, extension, defaultValue, optional, fileFilter)

        if not self.isRunnungInsideModeller():
            param.setMetadata(
                {'widget_wrapper': {'class': ProcessingParameterPickleFileUnsupervisedDatasetWidgetWrapper}}
            )
            param.setDefaultValue(defaultValue)

        self.addParameter(param)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterMapLayer(self, name: str, description: str, defaultValue=None, optional=False, advanced=False):
        self.addParameter(QgsProcessingParameterMapLayer(name, description, defaultValue, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterRasterLayer(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        self.addParameter(QgsProcessingParameterRasterLayer(name, description, defaultValue, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterMultipleLayers(
            self, name: str, description: str, layerType=QgsProcessing.SourceType.TypeMapLayer,
            defaultValue=None, optional=False, advanced=False
    ):
        self.addParameter(QgsProcessingParameterMultipleLayers(name, description, layerType, defaultValue, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterBand(
            self, name: str, description: str, defaultValue: int = None, parentLayerParameterName: str = None,
            optional=False, allowMultiple=False, advanced=False
    ):
        self.addParameter(
            QgsProcessingParameterBand(
                name, description, defaultValue, parentLayerParameterName, optional, allowMultiple
            )
        )
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterBandList(
            self, name: str, description: str, defaultValue: List[int] = None, parentLayerParameterName: str = None,
            optional=False, advanced=False
    ):
        assert parentLayerParameterName is not None
        self.addParameterBand(name, description, defaultValue, parentLayerParameterName, optional, True)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterVectorLayer(
            self, name: str, description: str, types=(QgsProcessing.SourceType.TypeVectorAnyGeometry,),
            defaultValue=None, optional=False, advanced=False
    ):
        if types is None:
            types = []
        self.addParameter(QgsProcessingParameterVectorLayer(name, description, types, defaultValue, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterCrs(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        self.addParameter(QgsProcessingParameterCrs(name, description, defaultValue, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterExtent(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        self.addParameter(QgsProcessingParameterExtent(name, description, defaultValue, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterRasterDestination(
            self, name: str, description: str, defaultValue=None, optional=False, createByDefault=True,
            allowTif=True, allowEnvi=True, allowVrt=False, defaultFileExtension: str = None, advanced=False
    ):
        self.addParameter(
            ProcessingParameterRasterDestination(
                name, description, defaultValue, optional, createByDefault, allowTif, allowEnvi, allowVrt,
                defaultFileExtension
            )
        )
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterVrtDestination(
            self, name: str, description: str, defaultValue=None, optional=False, createByDefault=True,
            vrtOnly=False, defaultFileExtension: str = None, advanced=False
    ):
        if defaultFileExtension is None:
            defaultFileExtension = 'vrt'
        self.addParameterRasterDestination(
            name, description, defaultValue, optional, createByDefault, not vrtOnly, not vrtOnly, True,
            defaultFileExtension, advanced
        )

        self.flagParameterAsAdvanced(name, advanced)

    def addParameterVectorDestination(
            self, name: str, description='Output vector', type=QgsProcessing.SourceType.TypeVectorAnyGeometry,
            defaultValue=None, optional=False, createByDefault=True, advanced=False
    ):
        self.addParameter(
            QgsProcessingParameterVectorDestination(name, description, type, defaultValue, optional, createByDefault)
        )
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterFile(
            self, name: str, description: str,
            behavior: QgsProcessingParameterFile.Behavior = QgsProcessingParameterFile.Behavior.File,
            extension: str = '', defaultValue=None, optional=False, fileFilter='', advanced=False
    ):
        self.addParameter(
            QgsProcessingParameterFile(
                name, description, behavior, extension, defaultValue, optional, fileFilter
            )
        )
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterPickleFile(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        from enmapboxprocessing.parameter.processingparameterpicklefilewidget import \
            ProcessingParameterPickleFileWidgetWrapper

        param = QgsProcessingParameterFile(
            name, description, QgsProcessingParameterFile.Behavior.File, '', defaultValue, optional,
            self.PickleFileFilter
        )
        if not self.isRunnungInsideModeller():
            param.setMetadata({'widget_wrapper': {'class': ProcessingParameterPickleFileWidgetWrapper}})
            param.setDefaultValue(defaultValue)
        self.addParameter(param)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterFileDestination(
            self, name: str, description: str, fileFilter='', defaultValue=None, optional=False,
            createByDefault=True, advanced=False
    ):
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name, description, fileFilter, defaultValue, optional, createByDefault
            )
        )
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterFolderDestination(
            self, name: str, description: str, defaultValue=None, optional=False, createByDefault=True,
            advanced=False
    ):
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                name, description, defaultValue, optional, createByDefault
            )
        )
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterNumber(
            self, name: str, description: str, type: QgsProcessingParameterNumber.Type, defaultValue=None,
            optional=False, minValue: float = None, maxValue: float = None, advanced=False
    ):
        if minValue is None:
            minValue = np.finfo(float).min
        if maxValue is None:
            maxValue = np.finfo(float).max

        self.addParameter(
            QgsProcessingParameterNumber(name, description, type, defaultValue, optional, minValue, maxValue)
        )
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterInt(
            self, name: str, description: str, defaultValue=None, optional=False, minValue: int = None,
            maxValue: int = None, advanced=False
    ):
        type = QgsProcessingParameterNumber.Type.Integer
        self.addParameterNumber(name, description, type, defaultValue, optional, minValue, maxValue)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterFloat(
            self, name: str, description: str, defaultValue=None, optional=False, minValue: float = None,
            maxValue: float = None, advanced=False
    ):
        type = QgsProcessingParameterNumber.Type.Double
        self.addParameterNumber(name, description, type, defaultValue, optional, minValue, maxValue)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterBoolean(self, name: str, description: str, defaultValue=None, optional=False, advanced=False):
        self.addParameter(QgsProcessingParameterBoolean(name, description, defaultValue, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterField(
            self, name: str, description: str, defaultValue=None, parentLayerParameterName: str = '',
            type=QgsProcessingParameterField.DataType.Any, allowMultiple=False,
            optional=False, defaultToAllFields=False, advanced=False
    ):
        self.addParameter(
            QgsProcessingParameterField(
                name, description, defaultValue, parentLayerParameterName, type, allowMultiple, optional,
                defaultToAllFields
            )
        )
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterEnum(
            self, name: str, description: str, options: Iterable[str], allowMultiple=False, defaultValue=None,
            optional=False, advanced=False
    ):
        self.addParameter(QgsProcessingParameterEnum(name, description, options, allowMultiple, defaultValue, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterIntRange(
            self, name: str, description: str, defaultValue: List[int] = None,
            optional=False, advanced=False
    ):
        type = QgsProcessingParameterNumber.Type.Integer
        self.addParameter(QgsProcessingParameterRange(name, description, type, defaultValue, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterString(
            self, name: str, description: str, defaultValue=None, multiLine=False, optional=False, advanced=False
    ):
        self.addParameter(QgsProcessingParameterString(name, description, defaultValue, multiLine, optional))
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterCode(
            self, name: str, description: str, defaultValue=None, optional=False, advanced=False
    ):
        from enmapboxprocessing.parameter.processingparametercodeeditwidget import \
            ProcessingParameterCodeEditWidgetWrapper
        param = QgsProcessingParameterString(name, description, optional=optional)
        param.setMetadata({'widget_wrapper': {'class': ProcessingParameterCodeEditWidgetWrapper}})
        param.setDefaultValue(defaultValue)
        self.addParameter(param)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterDataType(
            self, name: str, description='Data type', defaultValue: int = None, optional=False,
            advanced=False
    ):
        options = self.O_DATA_TYPE
        self.addParameterEnum(name, description, options, False, defaultValue, optional, advanced)

    def addParameterCreationProfile(
            self, name: str, description='Output options', defaultValue: str = None, optional=False, advanced=False
    ):
        from enmapboxprocessing.parameter.processingparametercreationprofilewidget import \
            ProcessingParameterCreationProfileWidgetWrapper
        param = QgsProcessingParameterString(name, description, optional=optional)
        param.setMetadata({'widget_wrapper': {'class': ProcessingParameterCreationProfileWidgetWrapper}})
        param.setDefaultValue(defaultValue)
        self.addParameter(param)
        self.flagParameterAsAdvanced(name, advanced)

    def addParameterResampleAlg(
            self, name: str, description='Resample algorithm', defaultValue=0, optional=False, advanced=False
    ):
        options = self.O_RESAMPLE_ALG
        self.addParameterEnum(name, description, options, False, defaultValue, optional, advanced)

    def addParameterMatrix(
            self, name: str, description: str, numberRows=3, hasFixedNumberRows=False, headers: Iterable[str] = None,
            defaultValue=None, optional=False, advanced=False
    ):
        self.addParameter(
            QgsProcessingParameterMatrix(
                name, description, numberRows, hasFixedNumberRows, headers, defaultValue, optional
            )
        )
        self.flagParameterAsAdvanced(name, advanced)

    def flagParameterAsAdvanced(self, name: str, advanced: bool):
        if advanced:
            p = self.parameterDefinition(name)
            p.setFlags(p.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)

    def flagParameterAsHidden(self, name: str, hidden: bool):
        if hidden:
            p = self.parameterDefinition(name)
            p.setFlags(p.flags() | QgsProcessingParameterDefinition.Flag.FlagHidden)

    def createLoggingFeedback(
            cls, feedback: QgsProcessingFeedback, logfile: TextIO
    ) -> Tuple[ProcessingFeedback, ProcessingFeedback]:
        feedbackMainAlgo = ProcessingFeedback(feedback, logfile=logfile)
        feedbackChildAlgo = ProcessingFeedback(feedback, logfile=logfile, isChildFeedback=True, silenced=True)
        return feedbackMainAlgo, feedbackChildAlgo

    @classmethod
    def htmlItalic(cls, text: str) -> str:
        return f'<i>{text}</i>'

    @classmethod
    def htmlBold(cls, text: str) -> str:
        return f'<b>{text}</b>'

    @classmethod
    def htmlLink(cls, link: str, text: str = None) -> str:
        if text is None:
            text = link
        return '<a href="' + link + '">' + text + '</a>'

    def tic(self, feedback: ProcessingFeedback, parameters: Dict[str, Any], context: QgsProcessingContext):
        self._startTime = time()

    def toc(self, feedback: ProcessingFeedback, result: Dict):
        feedback.pushTiming(time() - self._startTime)

    @staticmethod
    def runAlg(algOrName, parameters, onFinish=None, feedback=None, context=None, is_child_algorithm=False) -> Dict:
        return processing.run(algOrName, parameters, onFinish, feedback, context, is_child_algorithm)


class Group(Enum):
    AccuracyAssessment = 'Accuracy Assessment'
    AnalysisReadyData = 'Analysis ready data'
    Auxilliary = 'Auxilliary'
    Classification = 'Classification'
    Clustering = 'Clustering'
    ConvolutionMorphologyAndFiltering = 'Convolution, morphology and filtering'
    DatasetCreation = 'Dataset creation'
    Experimental = 'Experimental'
    ExportData = 'Export data'
    FeatureSelection = 'Feature selection'
    ImportData = 'Import data'
    Masking = 'Masking'
    Options = 'Options'
    Preprocessing = 'Pre-processing'
    RasterAnalysis = 'Raster analysis'
    RasterConversion = 'Raster conversion'
    RasterExtraction = 'Raster extraction'
    RasterMiscellaneous = 'Raster miscellaneous'
    RasterProjections = 'Raster projections'
    Regression = 'Regression'
    Sampling = 'Sampling'
    SpectralLibrary = 'Spectral Library'
    SpectralResampling = 'Spectral resampling'
    Testdata = 'Testdata'
    Transformation = 'Transformation'
    Unmixing = 'Unmixing'
    VectorConversion = 'Vector conversion'
    VectorCreation = 'Vector creation'


class CookbookUrls(object):
    URL = r'https://enmap-box.readthedocs.io/en/latest/usr_section/usr_cookbook/usr_cookbook.html'
    URL_CLASSIFICATION = ('Classification', URL + '/classification.html')
    URL_REGRESSION = ('Regression', URL + '/regression.html')
    URL_CLUSTERING = ('Clustering', URL + '/clustering.html')
    URL_TRANSFORMATION = ('Transformation', URL + '/transformation.html')
    URL_FILTERING = ('Filtering', URL + '/filtering.html')
    URL_GRAPHICAL_MODELER = ('Graphical Modeler', URL + '/graphical_modeler.html')
    URL_GENERIC_FILTER = ('Generic Filter', URL + '/generic_filter.html')
