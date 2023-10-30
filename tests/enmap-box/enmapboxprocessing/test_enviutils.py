from enmapboxprocessing.enviutils import EnviUtils
from enmapboxprocessing.testcase import TestCase
from tests.enmapboxtestdata import enmap_berlin


class TestEnviUtils(TestCase):

    def test_readEnviHeader(self):
        filename = enmap_berlin.replace('.bsq', '.hdr')
        metadata = EnviUtils().readEnviHeader(filename)
        self.assertEqual(21, len(metadata))
        self.assertIsInstance(metadata['wavelength'], list)
        self.assertEqual(177, len(metadata['wavelength']))
