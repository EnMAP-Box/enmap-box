"""
This is a template to create an EnMAP-Box test
"""
import re
import typing
import unittest

import numpy as np
from osgeo import gdal, gdal_array

from enmapbox.testing import EnMAPBoxTestCase
from qgis.core import QgsMultiBandColorRenderer
from qgis.core import QgsRasterLayer, StyleCategories


class EnMAPBoxTestCaseExample(EnMAPBoxTestCase):

    def test_default_bands_ENVI(self):
        testDir = self.tempDir(cleanup=True)

        # create ENVI file
        path_example = testDir / 'envi_example.bsq'

        array = np.ones((25, 10, 20))
        ds: gdal.Dataset = gdal_array.SaveArray(array, path_example.as_posix(), format='ENVI')
        self.assertIsInstance(ds, gdal.Dataset)
        path_hdr = [p for p in ds.GetFileList() if p.endswith(r'.hdr')][0]
        ds.SetMetadataItem('default bands', '{10, 5, 1}', 'ENVI')
        ds.FlushCache()
        del ds
        with open(path_hdr, 'r') as f:
            lines = f.read()
            match = re.search(r'default bands = \{10, 5, 1\}\n', lines)
            self.assertIsInstance(match, typing.Match)

        def getRGB(layer: QgsRasterLayer):
            self.assertTrue(layer.isValid())
            self.assertIsInstance(layer.renderer(), QgsMultiBandColorRenderer)
            r: QgsMultiBandColorRenderer = layer.renderer()
            return [r.redBand(), r.greenBand(), r.blueBand()]

        lyr = QgsRasterLayer(path_example.as_posix())
        lyr.loadDefaultStyle()
        rgb = getRGB(lyr)

        # ENVI header default band is not taken into account.
        # See https://github.com/OSGeo/gdal/issues/6339
        self.assertEqual(rgb, [1, 2, 3])

        # set bands explicitly
        lyr.renderer().setRedBand(10)
        lyr.renderer().setGreenBand(5)
        lyr.renderer().setBlueBand(1)

        # write to *.qml
        msg, success = lyr.saveDefaultStyle(
            StyleCategories.StyleCategory.Symbology | StyleCategories.StyleCategory.Rendering)
        del lyr

        # reload layer
        self.assertEqual(getRGB(QgsRasterLayer(path_example.as_posix())), [10, 5, 1])


if __name__ == '__main__':
    unittest.main(buffer=False)
