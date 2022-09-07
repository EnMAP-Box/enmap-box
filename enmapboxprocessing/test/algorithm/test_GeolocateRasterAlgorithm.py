import numpy as np

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.geolocaterasteralgorithm import GeolocateRasterAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from qgis.core import QgsRasterLayer, QgsRectangle, QgsCoordinateReferenceSystem


class TestTranslateAlgorithm(TestCase):

    def test_prisma(self):
        alg = GeolocateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(
                'HDF5:"D:/data/sensors/prisma/PRS_L1_STD_OFFL_20201107101404_20201107101408_0001.he5"://HDFEOS/SWATHS/PRS_L1_HCO/Data_Fields/LandCover_Mask'),
            alg.P_X_RASTER: QgsRasterLayer(
                'HDF5:"D:/data/sensors/prisma/PRS_L1_STD_OFFL_20201107101404_20201107101408_0001.he5"""://HDFEOS/SWATHS/PRS_L1_HCO/Geolocation_Fields/Longitude_VNIR'),
            alg.P_Y_RASTER: QgsRasterLayer(
                'HDF5:"D:/data/sensors/prisma/PRS_L1_STD_OFFL_20201107101404_20201107101408_0001.he5"""://HDFEOS/SWATHS/PRS_L1_HCO/Geolocation_Fields/Latitude_VNIR'),
            alg.P_NO_DATA_VALUE: 255,
            alg.P_OUTPUT_RASTER: self.filename('landcoverOrig.vrt')
        }

        # with default grid
        result = self.runalg(alg, parameters)
        self.assertEqual(90160659, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()))
        self.assertEqual(
            QgsRectangle(13.00112533569335938, 52.39900433314565475, 13.55388951447342549, 52.72693634033203125),
            RasterReader(result[alg.P_OUTPUT_RASTER]).extent()
        )
        self.assertEqual(QgsCoordinateReferenceSystem.fromEpsgId(4326), RasterReader(result[alg.P_OUTPUT_RASTER]).crs())

        # with default grid
        parameters[alg.P_GRID] = enmap
        result = self.runalg(alg, parameters)
        self.assertEqual(2083434, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()))
        self.assertEqual(
            RasterReader(enmap).extent(),
            RasterReader(result[alg.P_OUTPUT_RASTER]).extent()
        )
        self.assertEqual(RasterReader(enmap).crs(), RasterReader(result[alg.P_OUTPUT_RASTER]).crs())
