"""
This is a template to create an EnMAP-Box test
"""
import unittest

from osgeo import gdal

from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis.PyQt.QtCore import QPoint
from qgis.core import QgsCoordinateReferenceSystem, QgsRasterLayer

start_app()


class EnMAPBoxTestCaseExample(EnMAPBoxTestCase):

    def test_issue_88(self):
        from enmapbox.exampledata import enmap
        from enmapbox.qgispluginsupport.qps.utils import SpatialPoint

        ds = gdal.Open(enmap)
        # Get image dimensions
        width = ds.RasterXSize
        height = ds.RasterYSize

        # Calculate center pixel coordinates
        px_x = width // 2
        px_y = height // 2

        px_x = 1
        px_y = 1
        gt = ds.GetGeoTransform()

        # Convert pixel coordinates to geographic coordinates
        geo_x = gt[0] + px_x * gt[1] + px_y * gt[2]
        geo_y = gt[3] + px_x * gt[4] + px_y * gt[5]

        layer = QgsRasterLayer(enmap)

        pointA = SpatialPoint(layer.crs(), geo_x, geo_y)
        pixelA = pointA.toPixelPosition(layer)

        self.assertIsInstance(pixelA, QPoint)
        self.assertEqual(pixelA.x(), px_x)
        self.assertEqual(pixelA.y(), px_y)

        pointB = pointA.toCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
        pointA2 = pointB.toCrs(pointA.crs())

        # check raster corners
        e = layer.extent()
        c = layer.crs()
        dx = 0.5 * layer.rasterUnitsPerPixelX()
        dy = 0.5 * layer.rasterUnitsPerPixelY()
        geoCoords = [SpatialPoint(c, e.xMinimum() + dx, e.yMaximum() - dy),  # UL
                     SpatialPoint(c, e.xMaximum() - dx, e.yMaximum() - dy),  # UR
                     SpatialPoint(c, e.xMaximum() - dx, e.yMinimum() + dy),  # LR
                     SpatialPoint(c, e.xMinimum() + dx, e.yMinimum() + dy),  # LL
                     ]
        pxCoords = [QPoint(0, 0),
                    QPoint(layer.width() - 1, 0),
                    QPoint(layer.width() - 1, layer.height() - 1),
                    QPoint(0, layer.height() - 1)
                    ]

        for geoC, pxRef in zip(geoCoords, pxCoords):
            geoLL = geoC.toCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
            pxGeo = geoC.toPixelPosition(layer)
            pxLL = geoLL.toPixelPosition(layer)
            self.assertEqual(pxGeo, pxRef)
            self.assertEqual(pxLL, pxRef)


if __name__ == '__main__':
    unittest.main(buffer=False)
