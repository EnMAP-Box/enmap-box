from sklearn.base import ClusterMixin, TransformerMixin

from enmapboxprocessing.algorithm.fitaffinitypropagationalgorithm import FitAffinityPropagationAlgorithm
from enmapboxprocessing.algorithm.fitbirchalgorithm import FitBirchAlgorithm
from enmapboxprocessing.algorithm.fitclustereralgorithmbase import FitClustererAlgorithmBase
from enmapboxprocessing.algorithm.fitkmeansalgorithm import FitKMeansAlgorithm
from enmapboxprocessing.algorithm.fitmeanshiftalgorithm import FitMeanShiftAlgorithm
from enmapboxprocessing.algorithm.predictclusteringalgorithm import PredictClusteringAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromrasteralgorithm import \
    PrepareUnsupervisedDatasetFromRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import ClustererDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classifierDumpPkl, classificationDatasetAsJsonFile
from enmapboxtestdata import enmap, enmap_potsdam
from qgis.core import Qgis


class FitTestClustererAlgorithm(FitClustererAlgorithmBase):

    def displayName(self) -> str:
        return ''

    def shortDescription(self) -> str:
        return ''

    def helpParameterCode(self) -> str:
        return ''

    def code(self) -> ClusterMixin:
        from sklearn.cluster import KMeans
        clusterer = KMeans(n_clusters=10, random_state=42, n_init=10)
        return clusterer


class TestFitClustererAlgorithm(TestCase):

    def test_fitted(self):
        alg = FitTestClustererAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpPkl,
            alg.P_CLUSTERER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_CLUSTERER: self.filename('clusterer.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClustererDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_CLUSTERER]))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertEqual((58, 177), dump.X.shape)
        self.assertIsInstance(dump.clusterer, TransformerMixin)
        self.assertEqual(10, dump.clusterer.n_clusters)

    def test_fit_json(self):
        alg = FitTestClustererAlgorithm()
        parameters = {
            alg.P_DATASET: classificationDatasetAsJsonFile,
            alg.P_CLUSTERER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_CLUSTERER: self.filename('clusterer.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClustererDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_CLUSTERER]))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertEqual((58, 177), dump.X.shape)
        self.assertIsInstance(dump.clusterer, TransformerMixin)
        self.assertEqual(10, dump.clusterer.n_clusters)

    def test_fit_and_predict(self):
        alg = FitKMeansAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpPkl,
            alg.P_CLUSTERER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_CLUSTERER: self.filename('clusterer.pkl')
        }
        self.runalg(alg, parameters)

        alg = PredictClusteringAlgorithm()
        parameters = {
            alg.P_CLUSTERER: self.filename('clusterer.pkl'),
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification2.tif')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_CLASSIFICATION])
        self.assertEqual(8, max(reader.uniqueValueCounts(1)[0]))
        self.assertEqual(Qgis.DataType.Byte, reader.dataType(1))

    def test_clusterers(self):
        algs = [
            FitKMeansAlgorithm(),
            FitMeanShiftAlgorithm(),
            FitBirchAlgorithm(),
            FitAffinityPropagationAlgorithm()
        ]
        for alg in algs:
            print(alg.displayName())
            alg.initAlgorithm()
            alg.shortHelpString()
            parameters = {
                alg.P_DATASET: classifierDumpPkl,
                alg.P_CLUSTERER: alg.defaultCodeAsString(),
                alg.P_OUTPUT_CLUSTERER: self.filename('clusterer.pkl')
            }
            self.runalg(alg, parameters)

    def test_badBandsHandling_withNameMatching(self):
        algDataset = PrepareUnsupervisedDatasetFromRasterAlgorithm()
        algDataset.initAlgorithm()
        parametersDataset = {
            algDataset.P_FEATURE_RASTER: enmap_potsdam,
            algDataset.P_EXCLUDE_BAD_BANDS: True,
            algDataset.P_SAMPLE_SIZE: 100,
            algDataset.P_OUTPUT_DATASET: self.filename('dataset.pkl'),
        }
        self.runalg(algDataset, parametersDataset)

        alg = FitKMeansAlgorithm()
        parameters = {
            alg.P_DATASET: parametersDataset[algDataset.P_OUTPUT_DATASET],
            alg.P_CLUSTERER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_CLUSTERER: self.filename('clusterer.pkl')
        }
        self.runalg(alg, parameters)

        alg = PredictClusteringAlgorithm()
        parameters = {
            alg.P_CLUSTERER: self.filename('clusterer.pkl'),
            alg.P_RASTER: enmap_potsdam,
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification2.tif')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_CLASSIFICATION])
        self.assertEqual(8, max(reader.uniqueValueCounts(1)[0]))
        self.assertEqual(Qgis.DataType.Byte, reader.dataType(1))

    def test_badBandsHandling_withoutNameMatching(self):
        algDataset = PrepareUnsupervisedDatasetFromRasterAlgorithm()
        algDataset.initAlgorithm()
        parametersDataset = {
            algDataset.P_FEATURE_RASTER: enmap_potsdam,
            algDataset.P_EXCLUDE_BAD_BANDS: True,
            algDataset.P_SAMPLE_SIZE: 100,
            algDataset.P_OUTPUT_DATASET: self.filename('dataset.pkl'),
        }
        self.runalg(algDataset, parametersDataset)

        alg = FitKMeansAlgorithm()
        parameters = {
            alg.P_DATASET: parametersDataset[algDataset.P_OUTPUT_DATASET],
            alg.P_CLUSTERER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_CLUSTERER: self.filename('clusterer.pkl')
        }
        self.runalg(alg, parameters)

        alg = PredictClusteringAlgorithm()
        parameters = {
            alg.P_CLUSTERER: self.filename('clusterer.pkl'),
            alg.P_RASTER: enmap_potsdam,
            alg.P_MATCH_BY_NAME: False,
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification2.tif')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_CLASSIFICATION])
        self.assertEqual(8, max(reader.uniqueValueCounts(1)[0]))
        self.assertEqual(Qgis.DataType.Byte, reader.dataType(1))
