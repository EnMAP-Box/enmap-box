from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from qgis.core import QgsProcessingException


class TestCreateSpectralIndicesAlgorithm(TestCase):

    def test_single_predefined_index(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'NDVI',
            alg.P_OUTPUT_VRT: self.filename('ndvi.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_VRT])
        self.assertEqual('NDVI', reader.metadataItem('short_name', '', 1))
        self.assertEqual('Normalized Difference Vegetation Index', reader.metadataItem('long_name', '', 1))
        self.assertEqual('(N - R)/(N + R)', reader.metadataItem('formula', '', 1))

    def test_single_custom_index(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'MY_NDVI = (N - R)/(N + R)',
            alg.P_OUTPUT_VRT: self.filename('my_ndvi.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_VRT])
        self.assertEqual('MY_NDVI', reader.metadataItem('short_name', '', 1))
        self.assertIsNone(reader.metadataItem('long_name', '', 1))
        self.assertEqual('(N - R)/(N + R)', reader.metadataItem('formula', '', 1))

    def test_multi_indices(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'NDVI, EVI, MY_NDVI = (N - R)/(N + R)',
            alg.P_OUTPUT_VRT: self.filename('ndvi.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_VRT])
        self.assertEqual('NDVI', reader.metadataItem('short_name', '', 1))
        self.assertEqual('EVI', reader.metadataItem('short_name', '', 2))
        self.assertEqual('MY_NDVI', reader.metadataItem('short_name', '', 3))

    def test_unknown_index(self):
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_INDICES: 'NOT_AN_INDEX',
            alg.P_OUTPUT_VRT: self.filename('evi.vrt'),
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('unknown index: NOT_AN_INDEX', str(error))
