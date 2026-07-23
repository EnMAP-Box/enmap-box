from unittest.case import TestCase

from osgeo import ogr

from enmapbox.exampledata import landcover_polygons
from _classic.hubdsm.core.geometry import Geometry
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.ogrdriver import MEMORY_DRIVER
from _classic.hubdsm.core.ogrlayer import OgrLayer
from _classic.hubdsm.core.ogrvector import OgrVector
from _classic.hubdsm.core.projection import WGS84_PROJECTION, Projection


class TestOgrLayer(TestCase):

    def test_openAndMinorGetters(self):
        self.assertIsInstance(OgrLayer.open(filename=landcover_polygons), OgrLayer)
        self.assertIsInstance(OgrLayer.open(filename=landcover_polygons, layerNameOrIndex=0), OgrLayer)
        self.assertIsInstance(OgrLayer.open(
            filename=landcover_polygons, layerNameOrIndex='landcover_berlin_polygon'), OgrLayer
        )
        ogrLayer = OgrLayer.open(filename=landcover_polygons)
        self.assertEqual(ogrLayer.featureCount, 6)
        self.assertEqual(ogrLayer.fieldCount, 6)
        self.assertListEqual(
            ogrLayer.fieldNames,
            ['level_1_id', 'level_1', 'level_2_id', 'level_2', 'level_3_id', 'level_3']
        )
        self.assertListEqual(
            ogrLayer.fieldTypeNames,
            ['Integer64', 'String', 'Integer64', 'String', 'Integer64', 'String']
        )
        self.assertListEqual(
            ogrLayer.fieldTypes,
            [ogr.OFTInteger64, ogr.OFTString, ogr.OFTInteger64, ogr.OFTString, ogr.OFTInteger64, ogr.OFTString]
        )
        self.assertEqual(ogrLayer.fieldType(name='level_1_id'), ogr.OFTInteger64)

    def test_vector(self):
        self.assertIsInstance(OgrLayer.open(filename=landcover_polygons).vector, OgrVector)

    def test_name(self):
        self.assertEqual(OgrLayer.open(filename=landcover_polygons).name, 'landcover_berlin_polygon')

    def test_projection(self):
        self.assertEqual(OgrLayer.open(filename=landcover_polygons).projection, Projection.fromEpsg(epsg=32633))

    def test_geometryType(self):
        self.assertEqual(OgrLayer.open(filename=landcover_polygons).geometryType, ogr.wkbPolygon)

    def test_extent(self):
        self.assertEqual(
            str(OgrLayer.open(filename=landcover_polygons).extent),
            'Extent(ul=Location(x=383638.15720000025, y=5820133.9838), size=Size(x=1245.0624000004027, y=11521.63379999809))'
        )

    def test_createField(self):
        ogrLayer = MEMORY_DRIVER.createVector().createLayer()
        ogrLayer.createField(name='id', oft=ogr.OFTInteger)
        self.assertListEqual(ogrLayer.fieldNames, ['id'])
        self.assertListEqual(ogrLayer.fieldTypes, [ogr.OFTInteger])

    def test_createFeatureAndIteratorsOverfeatures(self):
        ogrLayer = MEMORY_DRIVER.createVector().createLayer(geometryType=ogr.wkbPoint)
        ogrLayer.createField(name='id', oft=ogr.OFTInteger)
        geometry = Geometry.fromLocation(location=Location(x=0, y=0))
        ogrLayer.createFeature(geometry=geometry, id=42)
        for g in ogrLayer.geometries:
            self.assertEqual(g, geometry)
        for v in ogrLayer.fieldValues(fieldNames=ogrLayer.fieldNames):
            self.assertTupleEqual(v, (42,))
        for g, v in ogrLayer.features(fieldNames=ogrLayer.fieldNames):
            self.assertEqual(g, geometry)
            self.assertTupleEqual(v, (42,))
