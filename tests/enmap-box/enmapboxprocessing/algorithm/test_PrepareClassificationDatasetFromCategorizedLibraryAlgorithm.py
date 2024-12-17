from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsMapLayer, QgsPointXY, QgsProcessingException, \
    QgsVectorLayer

from enmapbox import initAll
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedlibraryalgorithm import \
    PrepareClassificationDatasetFromCategorizedLibraryAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.librarydriver import LibraryDriver
from enmapboxprocessing.typing import Category, ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import library_gpkg, libraryWithBadBands

start_app()
initAll()


class TestPrepareClassificationDatasetFromCategorizedLibrary(TestCase):

    def test_default(self):
        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: library_gpkg,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((75, 177), dump.X.shape)
        self.assertEqual((75, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))

    def test_selectBinaryField(self):
        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: library_gpkg,
            alg.P_FIELD: 'profiles',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((75, 177), dump.X.shape)
        self.assertEqual((75, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))

    def test_wrongCategoryField(self):
        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: library_gpkg,
            # alg.P_FIELD: 'profiles',
            alg.P_CATEGORY_FIELD: 'profiles',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('Unable to derive categories from field: profiles', str(error))

    def test_wrongProfileField(self):
        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: library_gpkg,
            alg.P_FIELD: 'level_1',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('Not a valid Profiles field: level_1', str(error))

    def test_excludeBadBands(self):

        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: libraryWithBadBands,
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((1, 2), dump.X.shape)
        self.assertEqual(2, len(dump.features))

    def test_notExcludeBadBands(self):

        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: libraryWithBadBands,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((2, 4), dump.X.shape)
        self.assertEqual(4, len(dump.features))

    def test_locations(self):

        # create datagit
        values = {'profiles': {'y': [1, 2, 3]}, 'class': 1}
        geometry = QgsGeometry.fromPointXY(QgsPointXY(1, 2))
        writer = LibraryDriver().createFromData([values], [geometry])
        filename = self.filename('library2.geojson')
        writer.writeToSource(filename)
        layer = QgsVectorLayer(filename)
        renderer = Utils().categorizedSymbolRendererFromCategories('class', [Category(1, 'class 1', '#f00')])
        layer.setRenderer(renderer)
        layer.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: layer,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(
            QgsCoordinateReferenceSystem.fromEpsgId(4326), QgsCoordinateReferenceSystem.fromWkt(dump.crs)
        )
        self.assertEqual((1, 2), tuple(dump.locations[0]))

    def _test_BUG(self):
        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: r'C:\Users\Andreas\Downloads\data_austausch_unmixing\endm_w_gv_npv_2023_06_library.gpkg',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(
            QgsCoordinateReferenceSystem.fromEpsgId(4326), QgsCoordinateReferenceSystem.fromWkt(dump.crs)
        )
        self.assertEqual((1, 2), tuple(dump.locations[0]))
