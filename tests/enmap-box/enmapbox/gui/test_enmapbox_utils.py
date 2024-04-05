# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'
__date__ = '2017-07-17'
__copyright__ = 'Copyright 2017, Benjamin Jakimow'

import pickle
import unittest

from osgeo import gdal

from enmapbox.exampledata import enmap
from enmapbox.gui.utils import dataTypeName
from enmapbox.qgispluginsupport.qps.utils import gdalDataset, displayBandNames, geo2px, layerGeoTransform, SpatialPoint
from enmapbox.testing import EnMAPBoxTestCase
from enmapbox.utils import findBroadBand
from qgis.core import Qgis, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsPointXY


class TestEnMAPBoxUtils(EnMAPBoxTestCase):
    """Test resources work."""
    wmsUri = r'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'

    def test_spatialObjects(self):

        pt1 = SpatialPoint('EPSG:4326', 300, 300)
        self.assertIsInstance(pt1, SpatialPoint)
        d = pickle.dumps(pt1)
        pt2 = pickle.loads(d)

        self.assertEqual(pt1, pt2)

    def test_gdalDataset(self):
        ds1 = gdalDataset(enmap)
        self.assertIsInstance(ds1, gdal.Dataset)
        ds2 = gdalDataset(ds1)
        self.assertEqual(ds1, ds2)

    def test_dataTypeName(self):
        self.assertEqual(dataTypeName(Qgis.Byte), 'Byte')
        self.assertEqual(dataTypeName(Qgis.ARGB32_Premultiplied), 'ARGB32_Premultiplied')

    def test_bandNames(self):
        validSources = [enmap, QgsRasterLayer(enmap), gdal.Open(enmap)]

        for src in validSources:
            names = displayBandNames(src, leadingBandNumber=True)
            self.assertIsInstance(names, list, msg='Unable to derive band names from {}'.format(src))
            self.assertTrue(len(names) > 0)

    def test_coordinateTransformations(self):
        ds = gdalDataset(enmap)
        lyr = QgsRasterLayer(enmap)

        self.assertEqual(ds.GetGeoTransform(), layerGeoTransform(lyr))

        self.assertIsInstance(ds, gdal.Dataset)
        self.assertIsInstance(lyr, QgsRasterLayer)
        gt = ds.GetGeoTransform()
        crs = QgsCoordinateReferenceSystem(ds.GetProjection())

        # self.assertTrue(crs.isValid())

        geoCoordinate = QgsPointXY(gt[0], gt[3])
        pxCoordinate = geo2px(geoCoordinate, gt)
        pxCoordinate2 = geo2px(geoCoordinate, lyr)
        self.assertEqual(pxCoordinate.x(), 0)
        self.assertEqual(pxCoordinate.y(), 0)
        # self.assertTrue(px2geo(pxCoordinate, gt) == geoCoordinate)

        spatialPoint = SpatialPoint(crs, geoCoordinate)
        pxCoordinate = geo2px(spatialPoint, gt)
        self.assertEqual(pxCoordinate.x(), 0)
        self.assertEqual(pxCoordinate.y(), 0)
        # self.assertTrue(px2geo(pxCoordinate, gt) == geoCoordinate)

    def test_FindBroadBand(self):

        lyr = QgsRasterLayer(enmap)
        for b in ['R', 'G', 'B']:
            band = findBroadBand(lyr, b)
            self.assertIsInstance(band, int)


if __name__ == "__main__":
    unittest.main(buffer=False)
