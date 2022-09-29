"""
This is a template to create an EnMAP-Box test
"""
import unittest

from qgis.PyQt.QtCore import QPoint

from enmapbox.testing import EnMAPBoxTestCase
from qgis.core import QgsCoordinateReferenceSystem, QgsRasterLayer


class EnMAPBoxTestCaseExample(EnMAPBoxTestCase):

    def test_issue_88(self):
        from enmapbox.exampledata import enmap
        from enmapbox.qgispluginsupport.qps.utils import SpatialPoint

        layer = QgsRasterLayer(enmap)
        pointA = SpatialPoint(layer.crs(), layer.extent().center())
        pixelA = pointA.toPixelPosition(layer)

        self.assertIsInstance(pixelA, QPoint)
        self.assertEqual(pixelA.x(), int(layer.width() * 0.5))
        self.assertEqual(pixelA.y(), int(layer.height() * 0.5))

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
