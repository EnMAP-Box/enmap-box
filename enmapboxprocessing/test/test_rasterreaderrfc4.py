import numpy as np

import processing
from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase


class TestRasterReaderRfc4(TestCase):

    def test_rfc4(self):  # RFC 3: Band Properties
        reader = RasterReader(enmap)

        # get band properties
        self.assertEqual('band 49 (0.685000 Micrometers)', reader.bandName(42))
        self.assertEqual(0, reader.bandOffset(42))
        self.assertEqual(1, reader.bandScale(42))
        self.assertEqual(-99.0, reader.noDataValue(42))
        self.assertIsNone(reader.userBandOffset(42))
        self.assertIsNone(reader.userBandScale(42))

        # change user band name
        reader.setUserBandName('band 42 (685 Nanometers)', 42)
        self.assertEqual('band 42 (685 Nanometers)', reader.userBandName(42))
        self.assertEqual('band 49 (0.685000 Micrometers)', reader.bandName(42))  # isn't altering the original name

        # scale data
        yoff, xoff = 65, 50  # just a pixel location
        self.assertEqual(4503, reader.array(xoff, yoff, 1, 1, [42])[0][0, 0])  # unscaled
        reader.setUserBandScale(1e-4, 42)
        self.assertAlmostEqual(0.4503, reader.array(xoff, yoff, 1, 1, [42])[0][0, 0], 4)  # with scale
        reader.setUserBandOffset(123, 42)
        self.assertAlmostEqual(123.4503, reader.array(xoff, yoff, 1, 1, [42])[0][0, 0], 4)  # with scale and offset
        self.assertEqual(-99.0, np.min(reader.array(bandList=[42])))  # note that no data values aren't scaled

        # changes can be stored to new GDAL source by creating a VRT copy
        alg = SaveRasterAsAlgorithm()
        parameters = {
            alg.P_RASTER: reader.layer,
            alg.P_CREATION_PROFILE: alg.DefaultVrtCreationProfile,
            alg.P_COPY_METADATA: True,
            alg.P_OUTPUT_RASTER: self.filename('enmap.vrt')
        }
        result = processing.run(alg, parameters)
        reader2 = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual('band 42 (685 Nanometers)', reader2.bandName(42))
        self.assertEqual(123, reader2.bandOffset(42))
        self.assertEqual(1e-4, reader2.bandScale(42))
        self.assertAlmostEqual(123.4503, reader2.array(xoff, yoff, 1, 1, [42])[0][0, 0], 3)
