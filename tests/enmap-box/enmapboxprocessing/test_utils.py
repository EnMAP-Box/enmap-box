import unittest
from os.path import join, dirname

import numpy as np
from osgeo import gdal
from qgis.PyQt.QtCore import QDateTime, QSizeF
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsGeometry, QgsVectorLayer, Qgis, QgsProcessingFeedback, QgsRasterLayer, QgsRasterShader, \
    QgsColorRamp, \
    QgsStyle, QgsColorRampShader, QgsRectangle, QgsWkbTypes, QgsCoordinateReferenceSystem
from qgis.gui import QgsMapCanvas

from enmapbox.qgispluginsupport.qps.utils import SpatialPoint, SpatialExtent
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.testcase import TestCase
from enmapboxprocessing.typing import Category, Target
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import landcover_polygon, enmap, hires
from enmapboxtestdata import landcover_polygon_30m, fraction_point_singletarget, fraction_point_multitarget, \
    landcover_map_l3, \
    fraction_map_l3


class TestUtils(TestCase):

    def test_maximumMemoryUsage(self):
        Utils.maximumMemoryUsage()

    def test_qgisDataTypeToNumpyDataType_andBack(self):
        for qgisDataType, numpyDataType in [
            (Qgis.DataType.Byte, np.uint8), (Qgis.DataType.Float32, np.float32), (Qgis.DataType.Float64, np.float64),
            (Qgis.DataType.Int16, np.int16), (Qgis.DataType.Int32, np.int32), (Qgis.DataType.UInt16, np.uint16),
            (Qgis.DataType.UInt32, np.uint32), (Qgis.DataType.ARGB32_Premultiplied, np.uint32)
        ]:
            self.assertEqual(numpyDataType, Utils.qgisDataTypeToNumpyDataType(qgisDataType))
            if qgisDataType is Qgis.DataType.ARGB32_Premultiplied:
                continue
            self.assertEqual(qgisDataType, Utils.numpyDataTypeToQgisDataType(numpyDataType))

        try:
            Utils.qgisDataTypeToNumpyDataType(Qgis.DataType.UnknownDataType)
        except ValueError:
            pass

        try:
            Utils.numpyDataTypeToQgisDataType(np.int64)
        except ValueError:
            pass

    def test_gdalDataTypeToNumpyDataType(self):
        for gdalDataType, numpyDataType, in [
            (gdal.GDT_Byte, np.uint8), (gdal.GDT_Float32, np.float32), (gdal.GDT_Float64, np.float64),
            (gdal.GDT_Int16, np.int16), (gdal.GDT_Int32, np.int32), (gdal.GDT_UInt16, np.uint16),
            (gdal.GDT_UInt32, np.uint32)
        ]:
            self.assertEqual(numpyDataType, Utils.gdalDataTypeToNumpyDataType(gdalDataType))

        try:
            Utils.qgisDataTypeToNumpyDataType(Qgis.DataType.UnknownDataType)
        except ValueError:
            pass

    def test_qgisDataTypeToGdalDataType_andBack(self):
        self.assertIsNone(Utils.qgisDataTypeToGdalDataType(None))
        for qgisDataType, gdalDataType in [
            (Qgis.DataType.Byte, gdal.GDT_Byte), (Qgis.DataType.Float32, gdal.GDT_Float32),
            (Qgis.DataType.Float64, gdal.GDT_Float64), (Qgis.DataType.Int16, gdal.GDT_Int16),
            (Qgis.DataType.Int32, gdal.GDT_Int32), (Qgis.DataType.UInt16, gdal.GDT_UInt16),
            (Qgis.DataType.UInt32, gdal.GDT_UInt32)
        ]:
            self.assertEqual(gdalDataType, Utils.qgisDataTypeToGdalDataType(qgisDataType))
            self.assertEqual(qgisDataType, Utils.gdalDataTypeToQgisDataType(gdalDataType))

        try:
            Utils.qgisDataTypeToGdalDataType(Qgis.DataType.UnknownDataType)
        except ValueError:
            pass

        try:
            Utils.gdalDataTypeToQgisDataType(42)
        except ValueError:
            pass

    def test_qgisDataTypeName(self):
        self.assertEqual('Float32', Utils.qgisDataTypeName(Qgis.DataType.Float32))

    def test_gdalResampleAlgName(self):
        self.assertEqual('Average', Utils.gdalResampleAlgName(gdal.GRA_Average))
        try:
            Utils.gdalResampleAlgName(42)
        except ValueError:
            pass

    def test_numpyDataTypeToQgisDataType(self):
        for qgisDataType, numpyDataType in [
            (Qgis.DataType.Byte, np.uint8), (Qgis.DataType.Float32, np.float32),
            (Qgis.DataType.Float64, np.float64), (Qgis.DataType.Int16, np.int16),
            (Qgis.DataType.Int32, np.int32), (Qgis.DataType.UInt16, np.uint16),
            (Qgis.DataType.UInt32, np.uint32)
        ]:
            self.assertEqual(qgisDataType, Utils.numpyDataTypeToQgisDataType(numpyDataType))

        try:
            Utils.qgisDataTypeToNumpyDataType(Qgis.DataType.UnknownDataType)
        except ValueError:
            pass

    def test_numpyArrayToQgsRasterBlock_andBack(self):
        array = np.array([[1]], np.int32)
        block = Utils.numpyArrayToQgsRasterBlock(array)
        array2 = Utils.qgsRasterBlockToNumpyArray(block)
        self.assertTrue(np.all(array == array2))
        self.assertEqual(array.dtype, array2.dtype)

    def test_metadateValueToString(self):
        self.assertEqual('1', Utils.metadateValueToString(1))
        self.assertEqual('1', Utils.metadateValueToString('1'))
        self.assertEqual('1', Utils.metadateValueToString(' 1'))
        self.assertEqual('A_B', Utils.metadateValueToString('A,B'))
        self.assertEqual('{1, 2}', Utils.metadateValueToString([1, 2]))
        self.assertEqual('{1, 2}', Utils.metadateValueToString([' 1', 2]))
        self.assertEqual('{A_B, 2}', Utils.metadateValueToString(['A,B', 2]))

    def test_stringToMetadateValue(self):
        self.assertEqual('hello', Utils.stringToMetadateValue(' hello '))
        self.assertEqual(['a', 'b'], Utils.stringToMetadateValue('{a, b}'))

    def test_splitQgsVectorLayerSourceString(self):
        source = 'D:/landcover_berlin_point.gpkg|layername=landcover_berlin_point'
        filename, layerName = Utils.splitQgsVectorLayerSourceString(source)
        self.assertEqual('D:/landcover_berlin_point.gpkg', filename)
        self.assertEqual('landcover_berlin_point', layerName)

        source = 'D:/landcover_berlin_point.gpkg'
        filename, layerName = Utils.splitQgsVectorLayerSourceString(source)
        self.assertEqual('D:/landcover_berlin_point.gpkg', filename)
        self.assertIsNone(layerName)

    def test_qgisFeedbackToGdalCallback(self):
        self.assertIsNone(Utils.qgisFeedbackToGdalCallback(None))
        callback = Utils.qgisFeedbackToGdalCallback(QgsProcessingFeedback())
        callback(0, '')

    def test_palettedRasterRendererFromCategories(self):
        layer = QgsRasterLayer(landcover_map_l3)
        categories, bandNo = Utils.categoriesFromRasterLayer(layer)
        renderer = Utils.palettedRasterRendererFromCategories(layer.dataProvider(), bandNo, categories)
        categories2 = Utils.categoriesFromPalettedRasterRenderer(renderer)
        self.assertListEqual(categories, categories2)

    def test_multiBandColorRenderer(self):
        layer = QgsRasterLayer(enmap)
        renderer = Utils.multiBandColorRenderer(layer.dataProvider(), [1, 2, 3], [4, 5, 6], [7, 8, 9])
        self.assertEqual(1, renderer.redBand())
        self.assertEqual(2, renderer.greenBand())
        self.assertEqual(3, renderer.blueBand())
        self.assertEqual(4, renderer.redContrastEnhancement().minimumValue())
        self.assertEqual(5, renderer.greenContrastEnhancement().minimumValue())
        self.assertEqual(6, renderer.blueContrastEnhancement().minimumValue())
        self.assertEqual(7, renderer.redContrastEnhancement().maximumValue())
        self.assertEqual(8, renderer.greenContrastEnhancement().maximumValue())
        self.assertEqual(9, renderer.blueContrastEnhancement().maximumValue())

    def test_singleBandGrayRenderer(self):
        layer = QgsRasterLayer(enmap)
        renderer = Utils.singleBandGrayRenderer(layer.dataProvider(), 1, 2, 3)
        self.assertEqual(1, renderer.grayBand())
        self.assertEqual(2, renderer.contrastEnhancement().minimumValue())
        self.assertEqual(3, renderer.contrastEnhancement().maximumValue())

    @unittest.skipIf('Spectral' not in QgsStyle().defaultStyle().colorRampNames(), 'Missing "Spectral" color ramp')
    def test_singleBandPseudoColorRenderer_and_deriveColorRampShaderRampItems(self):
        layer = QgsRasterLayer(enmap)
        colorRamp: QgsColorRamp = QgsStyle().defaultStyle().colorRamp('Spectral')
        renderer = Utils.singleBandPseudoColorRenderer(layer.dataProvider(), 1, 2, 3, colorRamp)
        self.assertEqual(1, renderer.band())
        shader: QgsRasterShader = renderer.shader()
        colorRampShader: QgsColorRampShader = shader.rasterShaderFunction()
        self.assertIsInstance(shader, QgsRasterShader)
        self.assertIsInstance(colorRampShader, QgsColorRampShader)
        self.assertEqual(2, colorRampShader.minimumValue())
        self.assertEqual(3, colorRampShader.maximumValue())
        self.assertEqual(colorRamp.count(), len(colorRampShader.colorRampItemList()))

    def test_categoriesFromCategorizedSymbolRenderer(self):
        layer = QgsVectorLayer(landcover_polygon)
        fieldName = layer.renderer().classAttribute()
        categories = Utils.categoriesFromCategorizedSymbolRenderer(layer.renderer())
        self.assertEqual(6, len(categories))
        self.assertListEqual(
            [Category(value='roof', name='roof', color='#e60000'),
             Category(value='pavement', name='pavement', color='#9c9c9c'),
             Category(value='low vegetation', name='low vegetation', color='#98e600'),
             Category(value='tree', name='tree', color='#267300'),
             Category(value='soil', name='soil', color='#a87000'),
             Category(value='water', name='water', color='#0064ff')],
            categories
        )

    def test_categorizedSymbolRendererFromCategories(self):
        layer = QgsVectorLayer(landcover_polygon)
        fieldName = layer.renderer().classAttribute()
        categories = Utils.categoriesFromCategorizedSymbolRenderer(layer.renderer())
        renderer = Utils.categorizedSymbolRendererFromCategories(fieldName, categories)
        categories2 = Utils.categoriesFromCategorizedSymbolRenderer(renderer)
        self.assertListEqual(categories, categories2)

    def test_categoriesFromRenderer(self):
        layer = QgsRasterLayer(landcover_polygon_30m)
        categories = Utils.categoriesFromRenderer(layer.renderer())
        self.assertEqual(6, len(categories))

        layer = QgsVectorLayer(landcover_polygon)
        categories = Utils.categoriesFromRenderer(layer.renderer())
        self.assertEqual(6, len(categories))

    def test_categoriesFromRasterBand(self):
        layer = QgsRasterLayer(landcover_polygon_30m)
        categories = Utils.categoriesFromRasterBand(layer, 1)
        self.assertEqual(6, len(categories))
        self.assertListEqual([1, 2, 3, 4, 5, 6], [category.value for category in categories])
        self.assertListEqual(['1', '2', '3', '4', '5', '6'], [category.name for category in categories])

    def test_categoriesFromVectorField(self):
        layer = QgsVectorLayer(landcover_polygon)
        categories = Utils.categoriesFromVectorField(layer, 'level_3_id', 'level_3')
        self.assertEqual(6, len(categories))
        self.assertListEqual([1, 2, 3, 4, 5, 6], [category.value for category in categories])
        self.assertListEqual(
            ['roof', 'pavement', 'low vegetation', 'tree', 'soil', 'water'],
            [category.name for category in categories]
        )

    def test_(self):
        vector = QgsVectorLayer(landcover_polygon)
        categories = Utils.categoriesFromCategorizedSymbolRenderer(renderer=vector.renderer())
        self.assertListEqual(
            [Category(value='roof', name='roof', color='#e60000'),
             Category(value='pavement', name='pavement', color='#9c9c9c'),
             Category(value='low vegetation', name='low vegetation', color='#98e600'),
             Category(value='tree', name='tree', color='#267300'),
             Category(value='soil', name='soil', color='#a87000'),
             Category(value='water', name='water', color='#0064ff')],
            categories
        )

    def test_categoriesFromRasterLayer(self):
        layer = QgsRasterLayer(landcover_polygon_30m)
        categories, bandNo = Utils.categoriesFromRasterLayer(layer)
        self.assertEqual(1, bandNo)
        self.assertEqual(6, len(categories))
        self.assertListEqual(
            [Category(value=1, name='roof', color='#e60000'),
             Category(value=2, name='pavement', color='#9c9c9c'),
             Category(value=3, name='low vegetation', color='#98e600'),
             Category(value=4, name='tree', color='#267300'),
             Category(value=5, name='soil', color='#a87000'),
             Category(value=6, name='water', color='#0064ff')],
            categories
        )

        # layer without renderer
        writer = self.rasterFromArray([[[1, 2, 3]]])
        writer.close()
        layer = QgsRasterLayer(writer.source())
        categories, bandNo = Utils.categoriesFromRasterLayer(layer)
        self.assertEqual(1, bandNo)
        self.assertEqual(3, len(categories))
        self.assertListEqual([1, 2, 3], [category.value for category in categories])

    def test_categoriesFromPalettedRasterRenderer(self):
        layer = QgsRasterLayer(landcover_polygon_30m)
        categories = Utils.categoriesFromPalettedRasterRenderer(layer.renderer())
        self.assertEqual(6, len(categories))
        self.assertListEqual(
            [Category(value=1, name='roof', color='#e60000'),
             Category(value=2, name='pavement', color='#9c9c9c'),
             Category(value=3, name='low vegetation', color='#98e600'),
             Category(value=4, name='tree', color='#267300'),
             Category(value=5, name='soil', color='#a87000'),
             Category(value=6, name='water', color='#0064ff')],
            categories
        )

    def test_targetsFromSingleCategoryDiagramRenderer(self):
        layer = QgsVectorLayer(fraction_point_multitarget)
        targets = Utils.targetsFromSingleCategoryDiagramRenderer(layer.diagramRenderer())
        self.assertEqual(6, len(targets))
        self.assertListEqual(
            [Target(name='roof', color='#e60000'),
             Target(name='pavement', color='#9c9c9c'),
             Target(name='low vegetation', color='#98e600'),
             Target(name='tree', color='#267300'),
             Target(name='soil', color='#a87000'),
             Target(name='water', color='#0064ff')
             ],
            targets
        )

    def test_targetsFromGraduatedSymbolRenderer(self):
        layer = QgsVectorLayer(fraction_point_singletarget)
        targets = Utils.targetsFromGraduatedSymbolRenderer(layer.renderer())
        self.assertEqual(1, len(targets))
        self.assertListEqual([Target(name='vegetation', color='#98e600')], targets)

    def test_targetsFromLayer(self):
        layer = QgsVectorLayer(fraction_point_multitarget)
        targets = Utils.targetsFromLayer(layer)
        self.assertEqual(6, len(targets))
        self.assertListEqual(
            [Target(name='roof', color='#e60000'),
             Target(name='pavement', color='#9c9c9c'),
             Target(name='low vegetation', color='#98e600'),
             Target(name='tree', color='#267300'),
             Target(name='soil', color='#a87000'),
             Target(name='water', color='#0064ff')
             ],
            targets
        )

        layer = QgsVectorLayer(fraction_point_singletarget)
        targets = Utils.targetsFromGraduatedSymbolRenderer(layer.renderer())
        self.assertEqual(1, len(targets))
        self.assertListEqual([Target(name='vegetation', color='#98e600')], targets)

        layer = QgsRasterLayer(fraction_map_l3)
        targets = Utils.targetsFromLayer(layer)
        self.assertEqual(6, len(targets))
        # self.assertListEqual(
        #     [Target(name='roof', color='#e60000'),
        #      Target(name='pavement', color='#9c9c9c'),
        #      Target(name='low vegetation', color='#98e600'),
        #      Target(name='tree', color='#267300'),
        #      Target(name='soil', color='#a87000'),
        #      Target(name='water', color='#0064ff')
        #      ],
        #     targets
        # )

    def test_parseColor(self):
        white = QColor('#FFFFFF')
        self.assertEqual(white, Utils.parseColor('#FFFFFF'))
        self.assertEqual(white, Utils.parseColor(16777215))
        self.assertEqual(white, Utils.parseColor('16777215'))
        self.assertEqual(white, Utils.parseColor((255, 255, 255)))
        self.assertEqual(white, Utils.parseColor([255, 255, 255]))
        self.assertEqual(white, Utils.parseColor('(255, 255, 255)'))
        self.assertEqual(white, Utils.parseColor('[255, 255, 255]'))
        self.assertEqual(white, Utils.parseColor('255, 255, 255'))
        self.assertIsNone(Utils.parseColor(None))

        try:
            Utils.parseColor('dummy')
        except ValueError:
            pass

    def test_parseSpatialPoint(self):
        point = SpatialPoint(QgsCoordinateReferenceSystem.fromEpsgId(4326), 13.895089018465338, 53.07478793449)
        self.assertEqual(point, Utils.parseSpatialPoint('53.07478793449, 13.895089018465338'))
        self.assertEqual(point, Utils.parseSpatialPoint('53.07478793449,13.895089018465338'))
        self.assertEqual(point, Utils.parseSpatialPoint('53.07478793449 13.895089018465338'))
        self.assertEqual(point, Utils.parseSpatialPoint('13.895089018465338, 53.07478793449 [EPSG:4326]'))
        self.assertEqual(point, Utils.parseSpatialPoint('13.895089018465338,53.07478793449,[EPSG:4326]'))
        self.assertEqual(point, Utils.parseSpatialPoint('13.895089018465338 53.07478793449 [EPSG:4326]'))
        self.assertEqual(13.895, round(Utils.parseSpatialPoint('''53°04'29.2"N, 13°53'42.3"E''').x(), 3))
        self.assertEqual(53.075, round(Utils.parseSpatialPoint('''53°04'29.2"N, 13°53'42.3"E''').y(), 3))

        try:
            Utils.parseSpatialPoint('dummy')
        except ValueError:
            pass
        try:
            Utils.parseSpatialPoint('1,1,[123]')
        except ValueError:
            pass

    def test_parseSpatialExtent(self):
        def rectangleEqual(r1: QgsRectangle, r2: QgsRectangle):
            return all([
                r1.xMinimum() == r2.xMinimum(), r1.xMaximum() == r2.xMaximum(),
                r1.yMinimum() == r2.yMinimum(), r1.yMaximum() == r2.yMaximum(),
            ])

        self.assertTrue(rectangleEqual(
            SpatialExtent(QgsCoordinateReferenceSystem.fromEpsgId(4326), QgsRectangle(1, 1, 1, 1)),
            Utils.parseSpatialExtent('POINT(1 1)')
        ))
        self.assertTrue(rectangleEqual(
            SpatialExtent(QgsCoordinateReferenceSystem.fromEpsgId(4326), QgsRectangle(1, 1, 1, 1)),
            Utils.parseSpatialExtent('POINT(1 1)[EPSG:4326]')
        ))
        self.assertTrue(rectangleEqual(
            SpatialExtent(QgsCoordinateReferenceSystem.fromEpsgId(4326), QgsRectangle(1, 1, 1, 1)),
            Utils.parseSpatialExtent('POINT(1 1) [EPSG:4326] ')
        ))
        self.assertTrue(rectangleEqual(
            SpatialExtent(QgsCoordinateReferenceSystem.fromEpsgId(4326), QgsRectangle(0, 10, 1, 11)),
            Utils.parseSpatialExtent('LINESTRING(0 10, 1 11)')
        ))
        self.assertTrue(rectangleEqual(
            SpatialExtent(QgsCoordinateReferenceSystem.fromEpsgId(4326), QgsRectangle(0, 10, 1, 11)),
            Utils.parseSpatialExtent('LINESTRING(0 10, 1 11) [EPSG:4326] ')
        ))

        try:
            Utils.parseSpatialPoint('dummy')
        except ValueError:
            pass
        try:
            Utils.parseSpatialPoint('1,1,[123]')
        except ValueError:
            pass

    def test_parseDateTime(self):
        self.assertEqual(QDateTime(1970, 1, 1, 0, 0), Utils.parseDateTime(QDateTime(1970, 1, 1, 0, 0)))
        self.assertEqual(QDateTime(1970, 1, 1, 0, 0), Utils.parseDateTime(0))
        self.assertEqual(QDateTime(1970, 1, 1, 0, 0), Utils.parseDateTime('0'))
        self.assertEqual(QDateTime(1970, 1, 1, 12, 0), Utils.parseDateTime('1970-01-01'))
        self.assertEqual(QDateTime(1970, 1, 1, 12, 30, 42), Utils.parseDateTime('1970-01-01T12:30:42.123'))
        self.assertEqual(QDateTime(), Utils.parseDateTime(''))
        try:
            Utils.parseDateTime('dummy')
        except ValueError:
            pass

    def test_msecToDateTime(self):
        self.assertEqual(QDateTime(1970, 1, 1, 0, 0), Utils.msecToDateTime(0))

    def test_prepareCategories(self):
        # remove last if empty
        categories, valueLookup = Utils.prepareCategories(
            [Category(42, 'A', '#000000'), Category(0, '', '#000000')],
            removeLastIfEmpty=True
        )
        self.assertEqual([Category(42, 'A', '#000000')], categories)
        self.assertEqual({42: 42}, valueLookup)

        # int to int (nothing should change)
        categories, valueLookup = Utils.prepareCategories([Category(42, 'A', '#000000')])
        self.assertEqual([Category(42, 'A', '#000000')], categories)
        self.assertEqual({42: 42}, valueLookup)

        # decimal-string to int (value is just casted to int)
        categories, valueLookup = Utils.prepareCategories([Category('42', 'A', '#000000')], valuesToInt=True)
        self.assertEqual([Category(42, 'A', '#000000')], categories)
        self.assertEqual({'42': 42}, valueLookup)

        # none-decimal-string to int (value is replaced by category position)
        categories, valueLookup = Utils.prepareCategories([Category('name', 'A', '#000000')], valuesToInt=True)
        self.assertEqual([Category(1, 'A', '#000000')], categories)
        self.assertEqual({'name': 1}, valueLookup)

    def test_smallesUIntDataType(self):
        self.assertEqual(Qgis.DataType.Byte, Utils.smallesUIntDataType(0))
        self.assertEqual(Qgis.DataType.Byte, Utils.smallesUIntDataType(255))
        self.assertEqual(Qgis.DataType.UInt16, Utils.smallesUIntDataType(256))
        self.assertEqual(Qgis.DataType.UInt16, Utils.smallesUIntDataType(65535))
        self.assertEqual(Qgis.DataType.UInt32, Utils.smallesUIntDataType(65536))
        self.assertEqual(Qgis.DataType.UInt32, Utils.smallesUIntDataType(4294967295))
        try:
            Utils.smallesUIntDataType(4294967296)
        except ValueError:
            pass

    def test_snapExtentToRaster(self):
        writer = self.rasterFromArray(np.zeros((1, 10, 10)), None, QgsRectangle(0, 0, 100, 100))
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QSizeF(10, 10), reader.rasterUnitsPerPixel())
        self.assertEqual(QgsRectangle(0, 0, 10, 10), Utils.snapExtentToRaster(QgsRectangle(1, 1, 11, 11), reader.layer))
        self.assertEqual(QgsRectangle(0, 0, 10, 10), Utils.snapExtentToRaster(QgsRectangle(-1, -1, 9, 9), reader.layer))
        self.assertEqual(
            QgsRectangle(-10, -10, 20, 20),
            Utils.snapExtentToRaster(QgsRectangle(-6, -6, 16, 16), reader.layer)
        )

    def test_gdalResampleAlgToGdalWarpFormat(self):
        self.assertEqual('average', Utils.gdalResampleAlgToGdalWarpFormat(gdal.GRA_Average))

    def test_tmpFilename(self):
        root = self.filename('afile.tif')
        basename = 'tmp.txt'
        filename = Utils.tmpFilename(root, basename)
        self.assertEqual(join(dirname(root), '_temp_afile.tif', basename), filename)

    def test_sidecarFilename(self):
        self.assertEqual('test.abc', Utils.sidecarFilename('test.tif', '.abc'))
        self.assertEqual('test.tif.abc', Utils.sidecarFilename('test.tif', '.abc', False))

    def test_pickleDump_andLoad(self):
        obj = dict(a=1, b='text')
        filename = self.filename('dump.pkl')
        Utils.pickleDump(obj, filename)
        self.assertDictEqual(obj, Utils.pickleLoad(filename))

    def test_jsonDump_andLoad(self):
        obj = dict(a=1, b='text')
        filename = self.filename('dump.json')
        Utils.jsonDump(obj, filename)
        self.assertDictEqual(obj, Utils.jsonLoad(filename))

    def test_jsonDumps(self):
        self.assertEqual('1', Utils.jsonDumps(1))
        self.assertEqual('[\n  1\n]', Utils.jsonDumps(np.array([1])))

    def test_isPolygonGeometry(self):
        self.assertTrue(Utils.isPolygonGeometry(QgsWkbTypes.Type.Polygon))

    def test_isPointGeometry(self):
        self.assertTrue(Utils.isPointGeometry(QgsWkbTypes.Type.Point))

    def test_makeIdentifier(self):
        self.assertEqual('a', Utils.makeIdentifier('a'))
        self.assertEqual('_a', Utils.makeIdentifier('_a'))
        self.assertEqual('_a', Utils.makeIdentifier('1a'))
        self.assertEqual('a_b', Utils.makeIdentifier('a,b'))

    def test_makeBasename(self):
        self.assertEqual('a_b__.txt', Utils.makeBasename('a?b,!.txt'))

    def test_wavelengthUnitsShortName(self):
        for unit in ['nm', 'nanometers']:
            self.assertEqual('nm', Utils.wavelengthUnitsShortName(unit))
        for unit in ['μm', 'um', 'micrometers']:
            self.assertEqual('μm', Utils.wavelengthUnitsShortName(unit))
        for unit in ['mm', 'millimeters']:
            self.assertEqual('mm', Utils.wavelengthUnitsShortName(unit))
        for unit in ['cm', 'centimeters']:
            self.assertEqual('cm', Utils.wavelengthUnitsShortName(unit))
        for unit in ['m', 'meters']:
            self.assertEqual('m', Utils.wavelengthUnitsShortName(unit))

        self.assertIsNone(Utils.wavelengthUnitsShortName('dummy'))

    def test_wavelengthUnitsLongName(self):
        for unit in ['nm', 'nanometers']:
            self.assertEqual('Nanometers', Utils.wavelengthUnitsLongName(unit))
        for unit in ['μm', 'um', 'micrometers']:
            self.assertEqual('Micrometers', Utils.wavelengthUnitsLongName(unit))
        for unit in ['mm', 'millimeters']:
            self.assertEqual('Millimeters', Utils.wavelengthUnitsLongName(unit))
        for unit in ['cm', 'centimeters']:
            self.assertEqual('Centimeters', Utils.wavelengthUnitsLongName(unit))
        for unit in ['m', 'meters']:
            self.assertEqual('Meters', Utils.wavelengthUnitsLongName(unit))

        self.assertIsNone(Utils.wavelengthUnitsLongName('dummy'))

    def test_wavelengthUnitsConversionFactor(self):
        self.assertEqual(1e3, Utils.wavelengthUnitsConversionFactor('Micrometers', 'Nanometers'))
        self.assertEqual(1e-3, Utils.wavelengthUnitsConversionFactor('Nanometers', 'Micrometers'))

    def test_transformExtent(self):
        # different CRS
        extent = QgsRasterLayer(enmap).extent()
        crs = QgsRasterLayer(enmap).crs()
        toCrs = QgsCoordinateReferenceSystem().fromEpsgId(4326)
        self.assertGeometriesEqual(
            QgsGeometry.fromRect(
                QgsRectangle(13.24539916899924208, 52.41260765598481441,
                             13.34667529330139502, 52.52184188795437336)),
            QgsGeometry.fromRect(Utils.transformExtent(extent, crs, toCrs))
        )

        # same CRS
        extent = QgsRasterLayer(enmap).extent()
        crs = QgsRasterLayer(enmap).crs()
        self.assertGeometriesEqual(
            QgsGeometry.fromRect(QgsRectangle(
                380952.36999999999534339, 5808372.34999999962747097,
                387552.36999999999534339, 5820372.34999999962747097
            )),
            QgsGeometry.fromRect(Utils.transformExtent(extent, crs, crs))
        )

    def test_mapCanvasCrs(self):
        crs = QgsCoordinateReferenceSystem().fromEpsgId(4326)
        mapCanvas = QgsMapCanvas()
        mapCanvas.setDestinationCrs(crs)
        self.assertEqual(crs, Utils.mapCanvasCrs(mapCanvas))

    def test_sortedBy(self):
        a = [1, 2, 3]
        b = [3, 2, 1]
        self.assertListEqual([a, b], Utils.sortedBy([a, b], [1, 2, 3]))
        self.assertListEqual([b, a], Utils.sortedBy([a, b], [1, 2, 3], True))
        self.assertListEqual([b, a], Utils.sortedBy([a, b], [3, 2, 1]))
        self.assertListEqual([a, b], Utils.sortedBy([a, b], [3, 2, 1], True))

    def test_defaultNoDataValue(self):
        self.assertEqual(255, Utils.defaultNoDataValue(np.uint8))
        self.assertEqual(65535, Utils.defaultNoDataValue(np.uint16))
        self.assertEqual(4294967295, Utils.defaultNoDataValue(np.uint32))
        self.assertEqual(-32768, Utils.defaultNoDataValue(np.int16))
        self.assertEqual(-2147483648, Utils.defaultNoDataValue(np.int32))
        self.assertEqual(-3.4028234663852886e+38, Utils.defaultNoDataValue(np.float32))
        self.assertEqual(-3.4028234663852886e+38, Utils.defaultNoDataValue(np.float64))

    def test_setLayerDataSource(self):
        layer = QgsRasterLayer(enmap)
        Utils.setLayerDataSource(layer, 'dgal', hires, layer.extent())
        self.assertEqual(hires, layer.source())

    def test_getTempDirInTempFolder(self):
        print(Utils.getTempDirInTempFolder())
