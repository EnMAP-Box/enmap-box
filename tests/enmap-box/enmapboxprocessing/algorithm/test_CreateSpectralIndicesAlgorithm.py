from os import chdir
from os.path import dirname

from osgeo import gdal

from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap
from qgis.core import QgsProcessingException


class TestCreateSpectralIndicesAlgorithm(TestCase):

    def test_single_predefined_index(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'NDVI',
            alg.P_OUTPUT_RASTER: self.filename('ndvi.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual('NDVI', reader.metadataItem('short_name', '', 1))
        self.assertEqual('Normalized Difference Vegetation Index', reader.metadataItem('long_name', '', 1))
        self.assertEqual('(N - R)/(N + R)', reader.metadataItem('formula', '', 1))

    def test_single_custom_index(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'MY_NDVI = (N - R)/(N + R)',
            alg.P_OUTPUT_RASTER: self.filename('my_ndvi.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual('MY_NDVI', reader.metadataItem('short_name', '', 1))
        self.assertIsNone(reader.metadataItem('long_name', '', 1))
        self.assertEqual('(N - R)/(N + R)', reader.metadataItem('formula', '', 1))

    def test_multi_indices(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'NDVI, EVI, MY_NDVI = (N - R)/(N + R)',
            alg.P_OUTPUT_RASTER: self.filename('ndvi.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual('NDVI', reader.metadataItem('short_name', '', 1))
        self.assertEqual('EVI', reader.metadataItem('short_name', '', 2))
        self.assertEqual('MY_NDVI', reader.metadataItem('short_name', '', 3))

    def test_unknown_index(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'NOT_AN_INDEX',
            alg.P_OUTPUT_RASTER: self.filename('evi.vrt'),
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('unknown index: NOT_AN_INDEX', str(error))

    def test_relativeInputPath(self):

        filename = self.filename('enmap.tif')
        gdal.Translate(filename, enmap)  # copy enmap_berlin to output folder
        chdir(dirname(filename))  # set output folder the current workdir

        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: 'enmap.tif',
            alg.P_INDICES: 'NDVI, EVI',
            alg.P_OUTPUT_RASTER: self.filename('vi.vrt'),
        }
        result = self.runalg(alg, parameters)

    def test_single_custom_narrowband_index(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'CUSTOM = (B + r555 - r1640) / (r555 + r1640)',
            alg.P_OUTPUT_RASTER: self.filename('custom.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual('CUSTOM', reader.metadataItem('short_name', '', 1))
        self.assertIsNone(reader.metadataItem('long_name', '', 1))
        self.assertEqual('(B + r555 - r1640) / (r555 + r1640)', reader.metadataItem('formula', '', 1))

    def test_saveAsTif(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'NDVI',
            alg.P_OUTPUT_RASTER: self.filename('ndvi.tif'),
        }
        result = self.runalg(alg, parameters)
        ds: gdal.Dataset = gdal.Open(result[alg.P_OUTPUT_RASTER])
        driver: gdal.Driver = ds.GetDriver()
        self.assertEqual('GeoTIFF', driver.LongName)
