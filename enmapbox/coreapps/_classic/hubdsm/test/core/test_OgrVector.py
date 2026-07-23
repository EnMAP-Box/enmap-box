from unittest.case import TestCase

from osgeo import ogr

from enmapbox.exampledata import landcover_polygons
from _classic.hubdsm.core.geometry import Geometry
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.ogrdriver import MEMORY_DRIVER
from _classic.hubdsm.core.ogrlayer import OgrLayer
from _classic.hubdsm.core.ogrvector import OgrVector
from _classic.hubdsm.core.projection import WGS84_PROJECTION


class TestOgrVector(TestCase):

    def test_filename(self):
        ogrVector = OgrVector.open(landcover_polygons)
        self.assertEqual(ogrVector.filename, landcover_polygons)

    def test_layer(self):
        ogrVector = OgrVector.open(landcover_polygons)
        self.assertIsInstance(ogrVector.layer(), OgrLayer)
        self.assertIsInstance(ogrVector.layer(0), OgrLayer)
        self.assertIsInstance(ogrVector.layer('landcover_berlin_polygon'), OgrLayer)

    def test_createLayer(self):
        ogrVector = MEMORY_DRIVER.createVector()
        ogrLayer = ogrVector.createLayer(name='layer', projection=WGS84_PROJECTION, geometryType=ogr.wkbPoint)
        self.assertIsInstance(ogrLayer, OgrLayer)
        self.assertEqual(ogrLayer.name, 'layer')
        self.assertEqual(ogrLayer.projection, WGS84_PROJECTION)
        self.assertEqual(ogrLayer.geometryType, ogr.wkbPoint)

    def test_copyLayer(self):
        ogrVector = MEMORY_DRIVER.createVector()
        ogrLayer = ogrVector.createLayer(name='layer', projection=WGS84_PROJECTION, geometryType=ogr.wkbPoint)
        ogrLayer.createField(name='text', oft=ogr.OFTString)
        geometry = Geometry.fromLocation(location=Location(x=0, y=0))
        ogrLayer.createFeature(geometry=geometry, text='hello')
        self.assertEqual(ogrLayer.featureCount, 1)
        self.assertEqual(ogrLayer.fieldCount, 1)
        ogrLayerCopy = ogrVector.copyLayer(layer=ogrLayer, name='copy', fieldNames=['text'])
        self.assertEqual(ogrLayerCopy.featureCount, 1)
        self.assertEqual(ogrLayerCopy.fieldCount, 1)
        self.assertEqual(ogrLayerCopy.name, 'copy')
        for g1, g2 in zip(ogrLayer.geometries, ogrLayerCopy.geometries):
            self.assertEqual(g1, g2)
        for v1, v2 in zip(ogrLayer.fieldValues(['text']), ogrLayerCopy.fieldValues(['text'])):
            self.assertTupleEqual(v1, v2)

        # copy only geometries
        ogrLayerCopy2 = ogrVector.copyLayer(layer=ogrLayer)
        self.assertEqual(ogrLayerCopy2.featureCount, 1)
        self.assertEqual(ogrLayerCopy2.fieldCount, 0)
        self.assertEqual(ogrLayerCopy2.name, 'layer')
        self.assertSequenceEqual(list(ogrLayer.geometries), list(ogrLayerCopy2.geometries))

    def test_flushCache(self):
        pass
    #
    #     OgrVector
    #     gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1]], [[0]]]))
    #     gdalRaster.flushCache()
    #
    # def test_readAsArray(self):
    #     gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1, 2]]]))
    #     self.assertTrue(np.all(np.equal(gdalRaster.readAsArray(), [[[1, 2]]])))
    #     self.assertTrue(np.all(np.equal(gdalRaster.readAsArray(), gdalRaster.readAsArray(grid=gdalRaster.grid))))
    #     try:
    #         grid = GdalRaster.open(enmap).grid
    #         gdalRaster.readAsArray(grid=grid)
    #     except ProjectionMismatchError:
    #         pass
    #
    # def test_metadata(self):
    #     gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1, 2]]]))
    #     gdalRaster.setMetadataDict(metadataDict={'A': {'a': 1}, 'B': {'b': None}})
    #     self.assertDictEqual(gdalRaster.metadataDict['A'], {'a': '1'})
    #     self.assertIsNone(gdalRaster.metadataItem(key='b', domain='B'))
    #     gdalRaster.setMetadataDict(metadataDict={})
    #
    # def test_grid(self):
    #     gdalRaster = GdalRaster.open(enmap)
    #     gdalRaster2 = MEM_DRIVER.createFromArray(array=gdalRaster.readAsArray())
    #     self.assertFalse(gdalRaster.grid.equal(other=gdalRaster2.grid))
    #     gdalRaster2.setGrid(grid=gdalRaster.grid)
    #     self.assertTrue(gdalRaster.grid.equal(other=gdalRaster2.grid))
    #
    # def test_translate(self):
    #     gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1, 2]]]))
    #     gdalRaster2 = gdalRaster.translate()
    #     self.assertTrue(np.all(np.equal(gdalRaster2.readAsArray(), [[[1, 2]]])))
