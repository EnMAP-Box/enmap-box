import os.path

from enmapbox.qgispluginsupport.qps.speclib.io.envi import readENVIHeader
from enmapbox.testing import EnMAPBoxTestCase, start_app

start_app()


class TestCaseIssue622(EnMAPBoxTestCase):

    def test_loadENVI(self):
        from tests.enmapboxtestdata import enmap_berlin as path
        path = path.replace('.bsq', '.hdr')
        self.assertTrue(os.path.isfile(path))
        hdr = readENVIHeader(path)
        self.assertIsInstance(hdr, dict)
