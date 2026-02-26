from qgis.core import QgsVectorLayer

from enmapbox import initAll
from enmapboxprocessing.algorithm.importusgsspeclib07algorithm import ImportUsgsSpeclib07Algorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import speclibProductsRoot, SpeclibProducts


class TestImportUsgsSpeclib07Algorithm(TestCase):

    def test_AsdAndVegetation_only(self):
        if speclibProductsRoot() is None or self.skipProductImport:
            return

        initAll()

        alg = ImportUsgsSpeclib07Algorithm()
        parameters = {
            alg.P_FOLDER: SpeclibProducts.UsgsSplib07.folder,
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

        initAll()

        alg = ImportUsgsSpeclib07Algorithm()
        parameters = {
            alg.P_FOLDER: SpeclibProducts.UsgsSplib07.folder,
            alg.P_SPECTROMETER: alg.AllSpectrometers,
            alg.P_CHAPTER: alg.AllChapters,
            alg.P_OUTPUT_LIBRARY: self.filename('usgsSplib07.gpkg')
        }
        self.runalg(alg, parameters)
        library = QgsVectorLayer(parameters[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(2457, library.featureCount())

    def test_OversampledCubicSplineInterpolationCharacteristic(self):
        if speclibProductsRoot() is None or self.skipProductImport:
            return

        initAll()

        alg = ImportUsgsSpeclib07Algorithm()
        parameters = {
            alg.P_FOLDER: SpeclibProducts.UsgsSplib07.folder,
            alg.P_SPECTROMETER: alg.AllSpectrometers,
            alg.P_CHAPTER: alg.AllChapters,
            alg.P_SPECTRAL_CHARACTERISTIC: alg.OversampledCubicSplineInterpolationCharacteristic,
            alg.P_OUTPUT_LIBRARY: self.filename('usgsSplib07.gpkg')
        }
        self.runalg(alg, parameters)
        library = QgsVectorLayer(parameters[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(2457, library.featureCount())

    def test_Landsat8OLICharacteristic(self):
        if speclibProductsRoot() is None or self.skipProductImport:
            return

        initAll()

        alg = ImportUsgsSpeclib07Algorithm()
        parameters = {
            alg.P_FOLDER: SpeclibProducts.UsgsSplib07.folder,
            alg.P_SPECTROMETER: alg.AllSpectrometers,
            alg.P_CHAPTER: alg.AllChapters,
            alg.P_SPECTRAL_CHARACTERISTIC: alg.Landsat8OLICharacteristic,
            alg.P_OUTPUT_LIBRARY: self.filename('usgsSplib07.gpkg')
        }
        self.runalg(alg, parameters)
        library = QgsVectorLayer(parameters[alg.P_OUTPUT_LIBRARY])

    def test_all_characteristics(self):
        if speclibProductsRoot() is None or self.skipProductImport:
            return

        initAll()

        alg = ImportUsgsSpeclib07Algorithm()
        for characteristic in alg.AllCharacteristics:
            print('+++', alg.O_SPECTRAL_CHARACTERISTIC[characteristic], '+++')
            parameters = {
                alg.P_FOLDER: SpeclibProducts.UsgsSplib07.folder,
                alg.P_SPECTROMETER: alg.AllSpectrometers,
                alg.P_CHAPTER: alg.AllChapters,
                alg.P_SPECTRAL_CHARACTERISTIC: characteristic,
                alg.P_OUTPUT_LIBRARY: self.filename(
                    str(characteristic).zfill(2) + '_' + alg.O_SPECTRAL_CHARACTERISTIC[characteristic] + '.gpkg'
                )
            }
            self.runalg(alg, parameters)
            library = QgsVectorLayer(parameters[alg.P_OUTPUT_LIBRARY])
