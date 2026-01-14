from _classic.hubdsm.processing.importenmapl2a import ImportEnmapL2A
from _classic.hubdsm.test.processing.testcase import TestCase


class TestImportEnmapL2A(TestCase):

    def test(self):
        alg = ImportEnmapL2A()
        io = {
            alg.P_FILE: r'C:\Users\janzandr\Downloads\L2A_Alps_1_land\ENMAP01-____L2A-DT000326721_20170626T102020Z_001_V000204_20200406T201930Z-METADATA.XML',
            alg.P_OUTRASTER: '/vsimem/spectral.vrt',
        }
        result = self.runalg(alg=alg, io=io)
