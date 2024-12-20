from qgis.core import QgsVectorLayer

from enmapboxprocessing.algorithm.importusgsspeclib07algorithm import ImportUsgsSpeclib07Algorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import SensorProducts, speclibProductsRoot


class TestImportUsgsSpeclib07Algorithm(TestCase):

    def test_AsdAndVegetation_only(self):
        if speclibProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportUsgsSpeclib07Algorithm()
        parameters = {
            alg.P_FOLDER: SensorProducts.UsgsSplib07.folder,
            alg.P_SPECTROMETER: [alg.AsdSpectrometer],
            alg.P_CHAPTER: [alg.VegetationChapter],
            alg.P_OUTPUT_LIBRARY: self.filename('usgsSplib07.gpkg')
        }
        self.runalg(alg, parameters)
        library = QgsVectorLayer(parameters[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(218, library.featureCount())

    def test_all(self):
        if speclibProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportUsgsSpeclib07Algorithm()
        parameters = {
            alg.P_FOLDER: SensorProducts.UsgsSplib07.folder,
            alg.P_SPECTROMETER: alg.AllSpectrometers,
            alg.P_CHAPTER: alg.AllChapters,
            alg.P_OUTPUT_LIBRARY: self.filename('usgsSplib07_3.gpkg')
        }
        self.runalg(alg, parameters)
        library = QgsVectorLayer(parameters[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(2457, library.featureCount())
