import json
import pickle
import re
import uuid
from os import makedirs, mkdir
from os.path import join, dirname, basename, exists, splitext
from random import randint
from typing import Tuple, Optional, Callable, Any, Dict, Union, List
from warnings import warn

import numpy as np
from osgeo import gdal

from enmapbox.qgispluginsupport.qps.utils import SpatialExtent, SpatialPoint
from enmapbox.typeguard import typechecked
from enmapboxprocessing.typing import (NumpyDataType, MetadataValue, GdalDataType,
                                       GdalResamplingAlgorithm, Categories, Category, Targets, Target)
from qgis.PyQt.QtCore import QDateTime, QDate
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import (QgsRasterBlock, QgsProcessingFeedback, QgsPalettedRasterRenderer,
                       QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsRectangle, QgsRasterLayer,
                       QgsRasterDataProvider, QgsPointXY, QgsPoint, Qgis, QgsWkbTypes, QgsSymbol, QgsVectorLayer,
                       QgsFeature, QgsRasterRenderer, QgsFeatureRenderer, QgsMapLayer, QgsCoordinateTransform,
                       QgsProject, QgsCoordinateReferenceSystem, QgsReadWriteContext,
                       QgsMultiBandColorRenderer, QgsContrastEnhancement, QgsSingleBandPseudoColorRenderer,
                       QgsRasterShader, QgsColorRampShader, QgsColorRamp, QgsSingleBandGrayRenderer,
                       QgsSingleCategoryDiagramRenderer, QgsGraduatedSymbolRenderer,
                       QgsProcessingUtils, QgsGeometry
                       )
from qgis.gui import QgsMapCanvas


@typechecked
class Utils(object):

    @staticmethod
    def maximumMemoryUsage() -> int:
        """Return maximum memory usage in bytes."""
        return gdal.GetCacheMax()

    @staticmethod
    def qgisDataTypeToNumpyDataType(dataType: Qgis.DataType) -> NumpyDataType:
        if dataType == Qgis.DataType.Float32:
            return np.float32
        elif dataType == Qgis.DataType.Float64:
            return np.float64
        elif dataType == Qgis.DataType.Int8:
            return np.int8
        elif dataType == Qgis.DataType.Int16:
            return np.int16
        elif dataType == Qgis.DataType.Int32:
            return np.int32
        elif dataType == Qgis.DataType.Byte:
            return np.uint8
        elif dataType == Qgis.DataType.UInt16:
            return np.uint16
        elif dataType == Qgis.DataType.UInt32:
            return np.uint32
        elif dataType == Qgis.DataType.ARGB32:
            return np.uint32
        elif dataType == Qgis.DataType.ARGB32_Premultiplied:
            return np.uint32
        else:
            raise ValueError(f'unsupported data type: {dataType}')

    @staticmethod
    def qgisDataTypeToGdalDataType(dataType: Optional[Qgis.DataType]) -> Optional[int]:
        if dataType is None:
            return None
        elif dataType == Qgis.DataType.Float32:
            return gdal.GDT_Float32
        elif dataType == Qgis.DataType.Float64:
            return gdal.GDT_Float64
        elif dataType == Qgis.DataType.Int8:
            return gdal.GDT_Int8
        elif dataType == Qgis.DataType.Int16:
            return gdal.GDT_Int16
        elif dataType == Qgis.DataType.Int32:
            return gdal.GDT_Int32
        elif dataType == Qgis.DataType.Byte:
            return gdal.GDT_Byte
        elif dataType == Qgis.DataType.UInt16:
            return gdal.GDT_UInt16
        elif dataType == Qgis.DataType.UInt32:
            return gdal.GDT_UInt32
        else:
            raise ValueError(f'unsupported data type: {dataType}')

    @staticmethod
    def gdalDataTypeToNumpyDataType(dataType: Optional[int]) -> Optional[NumpyDataType]:
        if dataType == gdal.GDT_Byte:
            return np.uint8
        elif dataType == gdal.GDT_Float32:
            return np.float32
        elif dataType == gdal.GDT_Float64:
            return np.float64
        elif dataType == gdal.GDT_Int16:
            return np.int16
        elif dataType == gdal.GDT_Int32:
            return np.int32
        elif dataType == gdal.GDT_UInt16:
            return np.uint16
        elif dataType == gdal.GDT_UInt32:
            return np.uint32
        else:
            raise ValueError(f'unsupported data type: {dataType}')

    def qgisDataTypeName(dataType: Qgis.DataType) -> str:
        typeNameMap = {
            Qgis.DataType.UnknownDataType: 'UnknownDataType',
            Qgis.DataType.Byte: 'Byte',
            Qgis.DataType.UInt16: 'UInt16',
            Qgis.DataType.Int16: 'Int16',
            Qgis.DataType.UInt32: 'UInt32',
            Qgis.DataType.Int32: 'Int32',
            Qgis.DataType.Float32: 'Float32',
            Qgis.DataType.Float64: 'Float64',
            Qgis.DataType.CInt16: 'CInt16',
            Qgis.DataType.CInt32: 'CInt32',
            Qgis.DataType.CFloat32: 'CFloat32',
            Qgis.DataType.CFloat64: 'CFloat64',
            Qgis.DataType.ARGB32: 'ARGB32',
            Qgis.DataType.ARGB32_Premultiplied: 'ARGB32_Premultiplied'
        }
        return typeNameMap[dataType]

    @staticmethod
    def gdalResampleAlgName(resampleAlg: GdalResamplingAlgorithm) -> str:
        for name in 'NearestNeighbour Bilinear Cubic CubicSpline Lanczos Average Mode Min Q1 Med Q3 Max'.split():
            if getattr(gdal, 'GRA_' + name) == resampleAlg:
                return name
        raise ValueError(f'unsupported resampling algorithm: {resampleAlg}')

    @staticmethod
    def gdalDataTypeToQgisDataType(dataType: GdalDataType) -> Qgis.DataType:
        if dataType == gdal.GDT_Byte:
            return Qgis.DataType.Byte
        elif dataType == gdal.GDT_Float32:
            return Qgis.DataType.Float32
        elif dataType == gdal.GDT_Float64:
            return Qgis.DataType.Float64
        elif dataType == gdal.GDT_Int16:
            return Qgis.DataType.Int16
        elif dataType == gdal.GDT_Int32:
            return Qgis.DataType.Int32
        elif dataType == gdal.GDT_UInt16:
            return Qgis.DataType.UInt16
        elif dataType == gdal.GDT_UInt32:
            return Qgis.DataType.UInt32
        else:
            raise ValueError(f'unsupported data type: {dataType}')

    @staticmethod
    def numpyDataTypeToQgisDataType(dataType: NumpyDataType) -> Qgis.DataType:
        if dataType in [bool, np.uint8]:
            return Qgis.DataType.Byte
        elif dataType == np.float32:
            return Qgis.DataType.Float32
        elif dataType == np.float64:
            return Qgis.DataType.Float64
        elif dataType == np.int16:
            return Qgis.DataType.Int16
        elif dataType in [np.int32, np.int64]:
            return Qgis.DataType.Int32
        elif dataType == np.uint16:
            return Qgis.DataType.UInt16
        elif dataType in [np.uint32, np.uint64]:
            return Qgis.DataType.UInt32
        else:
            raise ValueError(f'unsupported data type: {dataType}')

    @classmethod
    def qgsRasterBlockToNumpyArray(cls, block: QgsRasterBlock) -> np.ndarray:
        dtype = cls.qgisDataTypeToNumpyDataType(block.dataType())
        array = np.frombuffer(np.array(block.data()), dtype=dtype)
        array = np.reshape(array, (block.height(), block.width()))
        return array

    @classmethod
    def numpyArrayToQgsRasterBlock(cls, array: np.ndarray, dataType: int = None) -> QgsRasterBlock:
        assert array.ndim == 2
        height, width = array.shape
        if dataType is None:
            dataType = cls.numpyDataTypeToQgisDataType(array.dtype)
        block = QgsRasterBlock(dataType, width, height)
        block.setData(array.tobytes())
        return block

    @classmethod
    def metadateValueToString(cls, value: MetadataValue) -> str:
        if isinstance(value, list):
            string = '{' + ', '.join([str(v).replace(',', '_').strip() for v in value]) + '}'
        else:
            string = str(value).replace(',', '_').strip()
        return string

    @classmethod
    def stringToMetadateValue(cls, string: str) -> MetadataValue:
        string = string.strip()
        isList = string.startswith('{') and string.endswith('}')
        if isList:
            value = [v.strip() for v in string[1:-1].split(',')]
        else:
            value = string.strip()
        return value

    @classmethod
    def splitQgsVectorLayerSourceString(cls, string: str) -> Tuple[str, Optional[str]]:
        if '|' in string:
            filename, tmp = string.split('|')
            _, layerName = tmp.split('=')
        else:
            filename = string
            layerName = None
        return filename, layerName

    @classmethod
    def qgisFeedbackToGdalCallback(
            cls, feedback: QgsProcessingFeedback = None
    ) -> Optional[Callable]:
        if feedback is None:
            callback = None
        else:
            def callback(progress: float, message: str, *args):
                feedback.setProgress(progress * 100)
                if feedback.isCanceled():
                    from enmapboxprocessing.enmapalgorithm import AlgorithmCanceledException
                    raise AlgorithmCanceledException()
        return callback

    @classmethod
    def palettedRasterRendererFromCategories(
            cls, provider: QgsRasterDataProvider, bandNumber: int, categories: Categories
    ) -> QgsPalettedRasterRenderer:
        classes = [QgsPalettedRasterRenderer.Class(c.value, QColor(c.color), c.name) for c in categories]
        renderer = QgsPalettedRasterRenderer(provider, bandNumber, classes)
        return renderer

    @classmethod
    def multiBandColorRenderer(
            cls, provider: QgsRasterDataProvider, bandNumbers: List[int], minValues: List[float], maxValues: List[float]
    ) -> QgsMultiBandColorRenderer:

        renderer = QgsMultiBandColorRenderer(provider, *bandNumbers)
        ce = QgsContrastEnhancement(provider.dataType(bandNumbers[0]))
        ce.setMinimumValue(minValues[0], False)
        ce.setMaximumValue(maxValues[0], False)
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
        renderer.setRedContrastEnhancement(ce)
        ce = QgsContrastEnhancement(provider.dataType(bandNumbers[1]))
        ce.setMinimumValue(minValues[1], False)
        ce.setMaximumValue(maxValues[1], False)
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
        renderer.setGreenContrastEnhancement(ce)
        ce = QgsContrastEnhancement(provider.dataType(bandNumbers[2]))
        ce.setMinimumValue(minValues[2], False)
        ce.setMaximumValue(maxValues[2], False)
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
        renderer.setBlueContrastEnhancement(ce)
        return renderer

    @classmethod
    def singleBandGrayRenderer(
            cls, provider: QgsRasterDataProvider, grayBand: int, minValue: float, maxValue: float
    ) -> QgsSingleBandGrayRenderer:

        renderer = QgsSingleBandGrayRenderer(provider, grayBand)
        ce = QgsContrastEnhancement(provider.dataType(grayBand))
        ce.setMinimumValue(minValue, False)
        ce.setMaximumValue(maxValue, False)
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
        renderer.setContrastEnhancement(ce)
        return renderer

    @classmethod
    def singleBandPseudoColorRenderer(
            cls, provider: QgsRasterDataProvider, bandNo: int, minValue: float, maxValue: float,
            colorRamp: Optional[QgsColorRamp] = None, colorRampType=QgsColorRampShader.Type.Interpolated,

    ) -> QgsSingleBandPseudoColorRenderer:
        shader = QgsRasterShader()
        colorRampShader = QgsColorRampShader()
        colorRampShader.setMinimumValue(minValue)
        colorRampShader.setMaximumValue(maxValue)
        colorRampShader.setColorRampType(colorRampType)

        # derive ramp items
        if colorRamp is not None:
            rampItems = cls.deriveColorRampShaderRampItems(minValue, maxValue, colorRamp)
            colorRampShader.setColorRampItemList(rampItems)

        shader.setRasterShaderFunction(colorRampShader)
        renderer = QgsSingleBandPseudoColorRenderer(provider, bandNo, shader)
        return renderer

    @classmethod
    def deriveColorRampShaderRampItems(
            cls, minValue: float, maxValue: float, ramp: QgsColorRamp
    ) -> List[QgsColorRampShader.ColorRampItem]:

        # derive ramp items
        delta = maxValue - minValue
        fractionalSteps = [i / (ramp.count() - 1) for i in range(ramp.count())]
        colors = [ramp.color(f) for f in fractionalSteps]
        steps = [minValue + f * delta for f in fractionalSteps]
        rampItems = [QgsColorRampShader.ColorRampItem(step, color, str(step)) for step, color in zip(steps, colors)]
        return rampItems

    @classmethod
    def categorizedSymbolRendererFromCategories(
            cls, fieldName: str, categories: Categories
    ) -> QgsCategorizedSymbolRenderer:
        rendererCategories = list()
        for c in categories:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.geometryType(QgsWkbTypes.Point))
            symbol.setColor(QColor(c.color))
            category = QgsRendererCategory(c.value, symbol, c.name)
            rendererCategories.append(category)

        renderer = QgsCategorizedSymbolRenderer(fieldName, rendererCategories)
        return renderer

    @classmethod
    def categoriesFromCategorizedSymbolRenderer(cls, renderer: QgsCategorizedSymbolRenderer) -> Categories:
        c: QgsRendererCategory
        categories = [Category(c.value(), c.label(), c.symbol().color().name())
                      for c in renderer.categories()
                      if c.label() != '']
        return categories

    @classmethod
    def categoriesFromRenderer(cls, renderer: Union[QgsFeatureRenderer, QgsRasterRenderer],
                               layer: QgsMapLayer = None) -> Optional[Categories]:
        if isinstance(renderer, QgsPalettedRasterRenderer):
            return Utils.categoriesFromPalettedRasterRenderer(renderer)
        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            return Utils.categoriesFromCategorizedSymbolRenderer(renderer)
        if isinstance(renderer, QgsSingleBandGrayRenderer):
            return Utils.categoriesFromRasterBand(layer, renderer.inputBand())

    @classmethod
    def categoriesFromRasterBand(cls, raster: QgsRasterLayer, bandNo: int) -> Categories:
        from enmapboxprocessing.rasterreader import RasterReader
        reader = RasterReader(raster)
        array = reader.array(bandList=[bandNo])
        mask = reader.maskArray(array, bandList=[bandNo], defaultNoDataValue=0)
        values = np.unique(array[0][mask[0]])
        categories = [Category(int(v), str(v), QColor(randint(0, 2 ** 24)).name()) for v in values]
        return categories

    @classmethod
    def categoriesFromVectorField(
            cls, vector: QgsVectorLayer, valueField: str, nameField: str = None, colorField: str = None
    ) -> Categories:
        feature: QgsFeature
        values = list()
        names = dict()
        colors = dict()
        for feature in vector.getFeatures():
            value = feature.attribute(valueField)
            if isinstance(value, (int, float, str)):
                values.append(value)
                if nameField is not None:
                    names[value] = feature.attribute(nameField)  # only keep the last occurrence!
                if colorField is not None:
                    colors[value] = feature.attribute(colorField)  # only keep the last occurrence!

        values = np.unique(values).tolist()
        categories = list()
        for value in values:
            color = colors.get(value, QColor(randint(0, 2 ** 24 - 1)))
            color = cls.parseColor(color).name()
            name = names.get(value, str(value))
            categories.append(Category(value, name, color))
        return categories

    @classmethod
    def categoriesFromRasterLayer(cls, raster: QgsRasterLayer, bandNo: int = None) -> Tuple[Categories, int]:
        renderer = raster.renderer()
        if isinstance(renderer, QgsPalettedRasterRenderer):
            categories = cls.categoriesFromPalettedRasterRenderer(renderer)
            bandNo = renderer.band()
        else:
            if bandNo is None:
                bandNo = 1
            categories = cls.categoriesFromRasterBand(raster, bandNo)
        return categories, bandNo

    @classmethod
    def categoriesFromPalettedRasterRenderer(cls, renderer: QgsPalettedRasterRenderer) -> Categories:
        categories = [Category(int(c.value), c.label, c.color.name())
                      for c in renderer.classes()
                      if c.label != '']
        return categories

    @classmethod
    def targetsFromSingleCategoryDiagramRenderer(cls, renderer: QgsSingleCategoryDiagramRenderer) -> Optional[Targets]:
        if len(renderer.diagramSettings()) != 1:
            raise NotImplementedError()

        diagramSettings = renderer.diagramSettings()[0]

        if not diagramSettings.enabled:
            return None

        names = [categoryAttribute.strip('"') for categoryAttribute in diagramSettings.categoryAttributes]
        colors = [categoryColor.name() for categoryColor in diagramSettings.categoryColors]
        targets = [Target(name, color) for name, color in zip(names, colors)]
        return targets

    @classmethod
    def targetsFromGraduatedSymbolRenderer(cls, renderer: QgsGraduatedSymbolRenderer) -> Targets:
        color = renderer.sourceSymbol().color().name()
        name = renderer.classAttribute()
        targets = [Target(name, color)]
        return targets

    @classmethod
    def targetsFromLayer(cls, layer: QgsMapLayer) -> Optional[Targets]:
        if isinstance(layer, QgsVectorLayer):
            targets = cls.targetsFromSingleCategoryDiagramRenderer(layer.diagramRenderer())
            if targets is None and isinstance(layer.renderer(), QgsGraduatedSymbolRenderer):
                targets = cls.targetsFromGraduatedSymbolRenderer(layer.renderer())
        elif isinstance(layer, QgsRasterLayer):
            from enmapboxprocessing.rasterreader import RasterReader
            reader = RasterReader(layer)
            targets = list()
            for bandNo in reader.bandNumbers():
                name = reader.bandName(bandNo)
                color = reader.bandColor(bandNo)
                if color is None:
                    hexcolor = '#000000'
                else:
                    hexcolor = color.name()
                target = Target(name, hexcolor)
                targets.append(target)
        else:
            raise ValueError()

        return targets

    @classmethod
    def parseColor(cls, obj) -> Optional[QColor]:
        if obj is None:
            return None

        if isinstance(obj, QColor):
            return obj

        if isinstance(obj, str):
            if QColor(obj).isValid():
                return QColor(obj)
            try:  # try to evaluate ...
                obj = eval(obj)
            except Exception:
                raise ValueError(f'invalid color: {obj}')

        if isinstance(obj, int):
            return QColor(obj)

        if isinstance(obj, (list, tuple)):
            return QColor(*obj)

        raise ValueError('invalid color')

    @classmethod
    def parseSpatialPoint(cls, obj) -> Optional['SpatialPoint']:
        error = ValueError(f'invalid spatial point: {obj}')
        if obj is None:
            return None

        if isinstance(obj, SpatialPoint):
            return obj

        if isinstance(obj, str):
            items: List[str] = [v for v in obj.replace(' ', ',').split(',') if len(v) > 1]
            if len(items) == 2:
                lon, lat = items
                try:
                    return SpatialPoint(QgsCoordinateReferenceSystem.fromEpsgId(4326), float(lat), float(lon))
                except Exception:
                    pass
                try:
                    def conversion(
                            old):  # adopted from https://stackoverflow.com/questions/10852955/python-batch-convert-gps-positions-to-lat-lon-decimals
                        direction = {'N': 1, 'S': -1, 'E': 1, 'W': -1}
                        new = old.replace(u'°', ' ').replace('\'', ' ').replace('"', ' ')
                        new = new.split()
                        new_dir = new.pop()
                        new.extend([0, 0, 0])
                        return (int(new[0]) + int(new[1]) / 60.0 + float(new[2]) / 3600.0) * direction[new_dir]

                    return SpatialPoint(QgsCoordinateReferenceSystem.fromEpsgId(4326), conversion(lat), conversion(lon))
                except Exception:
                    pass
            if len(items) == 3:
                lat, lon, epsgId = items
                if epsgId.upper().startswith('[EPSG:'):
                    epsgId = int(epsgId[6:-1])
                    return SpatialPoint(QgsCoordinateReferenceSystem.fromEpsgId(epsgId), float(lat), float(lon))

        raise error

    @classmethod
    def parseSpatialExtent(cls, obj) -> Optional['SpatialExtent']:
        error = ValueError(f'invalid spatial extent: {obj}')
        if obj is None:
            return None

        if isinstance(obj, SpatialExtent):
            return obj

        if isinstance(obj, str):
            items: List[str] = obj.split('[')
            if len(items) == 1:
                wkt = items[0]
                geometry = QgsGeometry.fromWkt(wkt)
                return SpatialExtent(QgsCoordinateReferenceSystem.fromEpsgId(4326), geometry.boundingBox())
            if len(items) == 2:
                wkt, epsgId = items
                if epsgId.upper().startswith('EPSG:') and epsgId.strip().endswith(']'):
                    epsgId = int(epsgId.strip()[5:-1])
                    geometry = QgsGeometry.fromWkt(wkt)
                    return SpatialExtent(QgsCoordinateReferenceSystem.fromEpsgId(epsgId), geometry.boundingBox())
        raise error

    @classmethod
    def parseDateTime(cls, obj) -> QDateTime:
        if isinstance(obj, QDateTime):
            return obj

        if isinstance(obj, int):  # milliseconds since 1970
            return cls.msecToDateTime(obj)

        if isinstance(obj, str):
            if obj.isdecimal():  # milliseconds since 1970
                return cls.msecToDateTime(int(obj))
            elif len(obj) == 10:  # date, e.g. 2021-12-24
                dateTime = QDateTime.fromString(obj, 'yyyy-MM-dd')
                dateTime = dateTime.addSecs(12 * 60 * 60)
                return dateTime
            elif len(obj) >= 19:  # date, e.g. 2021-12-24T12:30:42.123..
                return QDateTime.fromString(obj[:19], 'yyyy-MM-ddTHH:mm:ss')
            elif obj in ['', 'None']:  # invalid date
                return QDateTime()

        raise ValueError(f'invalid datetime: {obj}')

    @classmethod
    def msecToDateTime(cls, msec: int) -> QDateTime:
        return QDateTime(QDate(1970, 1, 1)).addMSecs(int(msec))

    @classmethod
    def prepareCategories(
            cls, categories: Categories, valuesToInt=False, removeLastIfEmpty=False
    ) -> Tuple[Categories, Dict]:

        categoriesOrig = categories
        if removeLastIfEmpty:
            if categories[-1].name == '':
                categories = categories[:-1]

        if valuesToInt:
            def castValueToInt(category: Category, index: int) -> Category:
                if str(category.value).isdecimal():
                    return Category(int(category.value), category.name, category.color)
                else:
                    return Category(index + 1, category.name, category.color)

            categories = [castValueToInt(c, i) for i, c in enumerate(categories)]

        namesOrig = [c.name for c in categoriesOrig]
        valueLookup = dict()
        for c in categories:
            index = namesOrig.index(c.name)
            valueOrig = categoriesOrig[index].value
            valueNew = c.value
            valueLookup[valueOrig] = valueNew

        return categories, valueLookup

    @classmethod
    def smallesUIntDataType(cls, value: int) -> Qgis.DataType:
        if 0 <= value < 256:
            return Qgis.DataType.Byte
        elif value < 65536:
            return Qgis.DataType.UInt16
        elif value < 4294967296:
            return Qgis.DataType.UInt32
        else:
            raise ValueError(f'not a valid UInt value: {value}')

    @classmethod
    def snapExtentToRaster(cls, extent: QgsRectangle, raster: QgsRasterLayer) -> QgsRectangle:
        provider: QgsRasterDataProvider = raster.dataProvider()
        ulSubPixel: QgsPoint = provider.transformCoordinates(
            QgsPoint(extent.xMinimum(), extent.yMaximum()), QgsRasterDataProvider.TransformLayerToImage
        )
        lrSubPixel: QgsPoint = provider.transformCoordinates(
            QgsPoint(extent.xMaximum(), extent.yMinimum()), QgsRasterDataProvider.TransformLayerToImage
        )
        ul = provider.transformCoordinates(
            QgsPoint(round(ulSubPixel.x()), round(ulSubPixel.y())), QgsRasterDataProvider.TransformImageToLayer
        )
        lr = provider.transformCoordinates(
            QgsPoint(round(lrSubPixel.x()), round(lrSubPixel.y())), QgsRasterDataProvider.TransformImageToLayer
        )
        return QgsRectangle(QgsPointXY(ul), QgsPointXY(lr))

    @classmethod
    def gdalResampleAlgToGdalWarpFormat(cls, resampleAlg: Optional[GdalResamplingAlgorithm]) -> Optional[str]:
        # Because of a bug in gdal.WarpOptions, we need to use strings for resampleAlg instead of enum codes.
        resampleAlgStrings = {
            None: None,
            gdal.GRA_NearestNeighbour: 'near',
            gdal.GRA_Bilinear: 'bilinear',
            gdal.GRA_Cubic: 'cubic',
            gdal.GRA_CubicSpline: 'cubicspline',
            gdal.GRA_Lanczos: 'lanczos',
            gdal.GRA_Average: 'average',
            gdal.GRA_Mode: 'mode',
            gdal.GRA_Max: 'max',
            gdal.GRA_Min: 'min',
            gdal.GRA_Med: 'med',
            gdal.GRA_Q1: 'q1',
            gdal.GRA_Q3: 'q3'
            # Add sum and rms later, after QGIS updates to required GDAL version
            #   sum: compute the weighted s
            #   um of all non-NODATA contributing pixels (since GDAL 3.1)
            #   rms: root mean square / quadratic mean of all non-NODATA contributing pixels (GDAL >= 3.3)
        }
        return resampleAlgStrings[resampleAlg]

    @classmethod
    def tmpFilename(cls, root: str, basename_: str):
        """Create a temp-filename relative to root."""
        tmpDirname = join(dirname(root), f'_temp_{basename(root)}')
        if not exists(tmpDirname) and not tmpDirname.startswith('/vsimem/'):
            makedirs(tmpDirname)
        tmpFilename = join(tmpDirname, basename_)
        return tmpFilename

    @classmethod
    def sidecarFilename(cls, filename: str, extention: str, replaceExtension=True):
        if replaceExtension:
            filename = splitext(filename)[0]
        return filename + extention

    @classmethod
    def pickleDump(cls, obj: Any, filename: str):
        with open(filename, 'wb') as file:
            pickle.dump(obj, file)

    @classmethod
    def pickleLoad(cls, filename: str) -> Any:
        with open(filename, 'rb') as file:
            return pickle.load(file)

    @classmethod
    def jsonDumps(cls, obj: Any, default=None, indent=2, timeFormat=None) -> str:

        if default is None:
            def default(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, QColor):
                    return obj.name()
                elif isinstance(obj, QDateTime):
                    return obj.toString(timeFormat)
                elif hasattr(obj, '__dict__'):
                    return obj.__dict__
                else:
                    return str(obj)

        return json.dumps(obj, default=default, indent=indent)

    @classmethod
    def jsonDump(cls, obj: Any, filename: str, default=None, indent=2, timeFormat=None):
        with open(filename, 'w') as file:
            text = Utils.jsonDumps(obj, default, indent, timeFormat)
            file.write(text)

    @classmethod
    def jsonLoad(cls, filename: str) -> Any:
        with open(filename) as file:
            return json.load(file)

    @classmethod
    def isPolygonGeometry(cls, wkbType: int) -> bool:
        types = [value for key, value in QgsWkbTypes.__dict__.items() if 'Polygon' in key]
        return wkbType in types

    @classmethod
    def isPointGeometry(cls, wkbType: int) -> bool:
        types = [value for key, value in QgsWkbTypes.__dict__.items() if 'Point' in key]
        return wkbType in types

    @classmethod
    def makeIdentifier(cls, string):
        """Make a valid Python identifier from the given string."""
        s = string.strip()
        s = re.sub('[\\s\\t\\n]+', '_', s)
        s = re.sub('[^0-9a-zA-Z_]', '_', s)
        s = re.sub('^[^a-zA-Z_]+', '_', s)
        return s

    @classmethod
    def makeBasename(cls, string):
        """Make a valid file basename from the given string."""

        def sub(c: str):
            if c.isalnum():
                return c
            if c in ' :._- ':
                return c
            return '_'

        return ''.join([sub(c) for c in string])

    @classmethod
    def wavelengthUnitsShortName(cls, units: str) -> Optional[str]:
        if units.lower() in ['nm', 'nanometers', 'nanometer']:
            return 'nm'
        elif units.lower() in ['μm', 'um', 'micrometers', 'micrometer']:
            return 'μm'
        elif units.lower() in ['mm', 'millimeters', 'millimeter']:
            return 'mm'
        elif units.lower() in ['cm', 'centimeters', 'centimeter']:
            return 'cm'
        elif units.lower() in ['m', 'meters', 'meter']:
            return 'm'
        else:
            warn(f'unknown wavelength unit: {units}')
            return None

    @classmethod
    def wavelengthUnitsLongName(cls, units: str) -> Optional[str]:
        if units.lower() in ['nm', 'nanometers', 'nanometer']:
            return 'Nanometers'
        elif units.lower() in ['μm', 'um', 'micrometers', 'micrometer']:
            return 'Micrometers'
        elif units.lower() in ['mm', 'millimeters', 'millimeter']:
            return 'Millimeters'
        elif units.lower() in ['cm', 'centimeters', 'centimeter']:
            return 'Centimeters'
        elif units.lower() in ['m', 'meters', 'meter']:
            return 'Meters'
        else:
            warn(f'unknown wavelength unit: {units}')
            return None

    @classmethod
    def wavelengthUnitsConversionFactor(cls, srcUnits: str, dstUnits: str) -> float:
        toNanometers = {
            'nm': 1., 'μm': 1e3, 'um': 1e3, 'mm': 1e6, 'cm': 1e7, 'm': 1e9
        }[cls.wavelengthUnitsShortName(srcUnits)]
        toDstUnits = {
            'nm': 1., 'μm': 1e-3, 'um': 1e-3, 'mm': 1e-6, 'cm': 1e-7, 'm': 1e-9
        }[cls.wavelengthUnitsShortName(dstUnits)]
        return toNanometers * toDstUnits

    @classmethod
    def dateTimeToDecimalYear(self, dateTime: Optional[QDateTime]) -> Optional[float]:
        if dateTime is None:
            return None
        date = dateTime.date()
        secOfYear = QDateTime(QDate(date.year(), 1, 1)).secsTo(dateTime)
        secsInYear = date.daysInYear() * 24 * 60 * 60
        return date.year() + secOfYear / secsInYear

    @classmethod
    def decimalYearToDateTime(self, decimalYear: Optional[float]) -> Optional[QDateTime]:
        if decimalYear is None:
            return None
        year = int(decimalYear)
        secsInYear = QDate(year, 1, 1).daysInYear() * 24 * 60 * 60
        secOfYear = int((decimalYear - year) * secsInYear)
        dateTime = QDateTime(QDate(year, 1, 1)).addSecs(secOfYear)
        return dateTime

    @classmethod
    def transformExtent(
            cls, extent: QgsRectangle, crs: QgsCoordinateReferenceSystem, toCrs: QgsCoordinateReferenceSystem
    ) -> QgsRectangle:

        if crs == toCrs:
            return extent
        else:
            transform = QgsCoordinateTransform(crs, toCrs, QgsProject.instance())
            return transform.transformBoundingBox(extent)

    @classmethod
    def mapCanvasCrs(cls, mapCanvas: QgsMapCanvas) -> QgsCoordinateReferenceSystem:
        return mapCanvas.mapSettings().destinationCrs()

    @classmethod
    def sortedBy(cls, lists: List[List], by: List, reverse=False):
        argsort = np.argsort(by, )
        if reverse:
            argsort = list(reversed(argsort))
        return [list(np.array(list_)[argsort]) for list_ in lists]

    @classmethod
    def defaultNoDataValue(cls, numpyDataType) -> float:
        try:
            noDataValue = np.finfo(numpyDataType).min
            noDataValue = float(max(np.finfo(np.float32).min, noDataValue))  # always use float32.min for float types
        except Exception:
            noDataValue = int(np.iinfo(numpyDataType).min)  # use min for int types
            if noDataValue == 0:
                noDataValue = int(np.iinfo(numpyDataType).max)  # use max for uint types
        return noDataValue

    @classmethod
    def setLayerDataSource(cls, layer: QgsMapLayer, newProvider: str, newDataSource: str, extent: QgsRectangle = None):
        # adopted from the changeDatasourcePlugin

        XMLDocument = QDomDocument("style")
        XMLMapLayers = XMLDocument.createElement("maplayers")
        XMLMapLayer = XMLDocument.createElement("maplayer")
        context = QgsReadWriteContext()
        layer.writeLayerXml(XMLMapLayer, XMLDocument, context)
        # apply layer definition
        XMLMapLayer.firstChildElement("datasource").firstChild().setNodeValue(newDataSource)
        XMLMapLayer.firstChildElement("provider").firstChild().setNodeValue(newProvider)
        if extent:  # if a new extent (for raster) is provided it is applied to the layer
            XMLMapLayerExtent = XMLMapLayer.firstChildElement("extent")
            XMLMapLayerExtent.firstChildElement("xmin").firstChild().setNodeValue(str(extent.xMinimum()))
            XMLMapLayerExtent.firstChildElement("xmax").firstChild().setNodeValue(str(extent.xMaximum()))
            XMLMapLayerExtent.firstChildElement("ymin").firstChild().setNodeValue(str(extent.yMinimum()))
            XMLMapLayerExtent.firstChildElement("ymax").firstChild().setNodeValue(str(extent.yMaximum()))

        XMLMapLayers.appendChild(XMLMapLayer)
        XMLDocument.appendChild(XMLMapLayers)
        layer.readLayerXml(XMLMapLayer, context)
        layer.reload()

    @classmethod
    def getTempDirInTempFolder(cls):
        # reimplementation of deprecated QGIS function; see #1357
        path = QgsProcessingUtils.tempFolder()
        path = join(path, uuid.uuid4().hex)
        mkdir(path)
        return path
