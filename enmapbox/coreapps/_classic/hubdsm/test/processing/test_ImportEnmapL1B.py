from _classic.hubdsm.processing.importenmapl1b import ImportEnmapL1B
from _classic.hubdsm.test.processing.testcase import TestCase


class TestImportEnmapL1B(TestCase):

    def test(self):
        alg = ImportEnmapL1B()
        io = {
            alg.P_FILE: r'C:\Users\janzandr\Downloads\L1B_Alps_1\ENMAP01-____L1B-DT000326721_20170626T102020Z_001_V000204_20200406T154119Z-METADATA.XML',
            alg.P_OUTRASTER_VNIR: '/vsimem/vnir.vrt',
            alg.P_OUTRASTER_SWIR: '/vsimem/swir.vrt'
        }
        result = self.runalg(alg=alg, io=io)
