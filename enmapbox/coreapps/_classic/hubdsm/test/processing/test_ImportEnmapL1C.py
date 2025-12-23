from _classic.hubdsm.processing.importenmapl1c import ImportEnmapL1C
from _classic.hubdsm.test.processing.testcase import TestCase


class TestImportEnmapL1C(TestCase):

    def test(self):
        alg = ImportEnmapL1C()
        io = {
            alg.P_FILE: r'C:\Users\janzandr\Downloads\L1C_Alps_1\ENMAP01-____L1C-DT000326721_20170626T102020Z_001_V000204_20200406T180016Z-METADATA.XML',
            alg.P_OUTRASTER: '/vsimem/spectral.vrt',
        }
        result = self.runalg(alg=alg, io=io)
