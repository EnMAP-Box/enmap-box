"""
Tests to ensure that module testfiles exist
"""
import pathlib
import unittest
from os.path import exists


class EnMAPBoxTestCaseExample(unittest.TestCase):
    """
    Tests to ensure that module testfiles exist
    """

    def checkModule(self, module):
        for a in module.__dict__.keys():
            if a.startswith('__'):
                continue
            if a == 'google_maps':
                continue
            filepath = getattr(module, a)
            if isinstance(filepath, (str, pathlib.Path)):
                self.assertTrue(exists(filepath), msg=f'Path does not exist: {filepath}')

    def test_enmapbox_exampledata(self):
        import enmapbox.exampledata
        self.checkModule(enmapbox.exampledata)

    def test_tests_testdata(self):
        import enmapboxtestdata
        self.checkModule(enmapboxtestdata)

    def test_qps_testdata(self):

        import enmapbox.qgispluginsupport.qpstestdata
        self.checkModule(enmapbox.qgispluginsupport.qpstestdata)


if __name__ == '__main__':
    unittest.main(buffer=False)
