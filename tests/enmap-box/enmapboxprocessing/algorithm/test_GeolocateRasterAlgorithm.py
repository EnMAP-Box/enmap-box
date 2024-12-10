from osgeo import gdal

from enmapboxprocessing.algorithm.geolocaterasteralgorithm import GeolocateRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import sensorProductsRoot, SensorProducts
from qgis.core import QgsRasterLayer


class TestGeolocateRasterAlgorithm(TestCase):

    def test_prisma(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = GeolocateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(
                f'HDF5:"{SensorProducts.Prisma.L1}"://HDFEOS/SWATHS/PRS_L1_HCO/Data_Fields/LandCover_Mask'),
            alg.P_X_RASTER: QgsRasterLayer(
                f'HDF5:"{SensorProducts.Prisma.L1}"""://HDFEOS/SWATHS/PRS_L1_HCO/Geolocation_Fields/Longitude_VNIR'),
            alg.P_Y_RASTER: QgsRasterLayer(
                f'HDF5:"{SensorProducts.Prisma.L1}"""://HDFEOS/SWATHS/PRS_L1_HCO/Geolocation_Fields/Latitude_VNIR'),
            alg.P_NO_DATA_VALUE: 255,
            alg.P_OUTPUT_RASTER: self.filename('landcoverOrig.vrt')
        }

        # with default grid
        self.runalg(alg, parameters)

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = GeolocateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(
                f'HDF5:"{SensorProducts.Prisma.L1}"://HDFEOS/SWATHS/PRS_L1_HCO/Data_Fields/LandCover_Mask'),
            alg.P_X_RASTER: QgsRasterLayer(
                f'HDF5:"{SensorProducts.Prisma.L1}"""://HDFEOS/SWATHS/PRS_L1_HCO/Geolocation_Fields/Longitude_VNIR'),
            alg.P_Y_RASTER: QgsRasterLayer(
                f'HDF5:"{SensorProducts.Prisma.L1}"""://HDFEOS/SWATHS/PRS_L1_HCO/Geolocation_Fields/Latitude_VNIR'),
            alg.P_NO_DATA_VALUE: 255,
            alg.P_OUTPUT_RASTER: self.filename('landcoverOrig.tif')
        }

        # with default grid
        result = self.runalg(alg, parameters)
        ds: gdal.Dataset = gdal.Open(result[alg.P_OUTPUT_RASTER])
        driver: gdal.Driver = ds.GetDriver()
        self.assertEqual('GeoTIFF', driver.LongName)
