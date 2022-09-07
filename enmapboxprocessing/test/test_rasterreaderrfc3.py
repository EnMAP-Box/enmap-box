import processing
from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase
from qgis.PyQt.QtCore import QDateTime


class TestRasterReaderRfc3(TestCase):

    def test_rfc3(self):  # RFC 3: Temporal Properties
        reader = RasterReader(enmap)

        # get temporal properties for raster
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.startTime())
        self.assertIsNone(reader.endTime())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.centerTime())

        # get temporal properties for band
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.startTime(42))
        self.assertIsNone(reader.endTime(42))
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.centerTime(42))

        # set temporal properties for raster
        reader.setTime(QDateTime(2009, 1, 1, 0, 0, 0))
        self.assertEqual(QDateTime(2009, 1, 1, 0, 0, 0), reader.startTime())
        reader.setTime(QDateTime(2009, 1, 1, 0, 0, 0), QDateTime(2010, 1, 1, 0, 0, 0))
        self.assertEqual(QDateTime(2010, 1, 1, 0, 0, 0), reader.endTime())
        self.assertEqual(QDateTime(2009, 7, 2, 13, 0, 0), reader.centerTime())

        # set temporal properties for band
        reader.setTime(QDateTime(2019, 1, 1, 0, 0, 0), None, 42)
        self.assertEqual(QDateTime(2019, 1, 1, 0, 0, 0), reader.startTime(42))
        reader.setTime(QDateTime(2019, 1, 1, 0, 0, 0), QDateTime(2020, 1, 1, 0, 0, 0), 42)
        self.assertEqual(QDateTime(2020, 1, 1, 0, 0, 0), reader.endTime(42))
        self.assertEqual(QDateTime(2019, 7, 2, 13, 0, 0), reader.centerTime(42))

        # find band by center time
        self.assertEqual(42, reader.findTime(QDateTime(2018, 1, 1, 1, 0, 0)))

        # note that this isn't altering the layer source
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), RasterReader(enmap).centerTime(42))

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
        self.assertEqual(QDateTime(2019, 7, 2, 13, 0, 0), reader2.centerTime(42))

        # remove temporal properties
        reader.setTime(None, None, 42)
        self.assertIsNone(reader.startTime(42))
        self.assertIsNone(reader.endTime(42))
