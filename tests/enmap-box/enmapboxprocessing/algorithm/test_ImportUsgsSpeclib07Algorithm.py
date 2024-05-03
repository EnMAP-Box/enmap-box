from enmapbox import initAll
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.importusgsspeclib07algorithm import ImportUsgsSpeclib07Algorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import SensorProducts, sensorProductsRoot


class TestImportUsgsSpeclib07Algorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        start_app()
        initAll()
        alg = ImportUsgsSpeclib07Algorithm()
        parameters = {
            alg.P_FOLDER: SensorProducts.UsgsSplib07.folder,
            alg.P_OUTPUT_LIBRARY: self.filename('usgsSplib07.gpkg')
        }
        self.runalg(alg, parameters)
