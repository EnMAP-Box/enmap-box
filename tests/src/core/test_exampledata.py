"""
Tests to ensure that module testfiles exist
"""
import pathlib
import re
import unittest
from os.path import exists
from typing import List

rx_skipped_sources = re.compile(r'(.*url=https://.*)')  # skip URLs


class EnMAPBoxTestCaseExample(unittest.TestCase):
    """
    Tests to ensure that module test files exist
    """

    def checkModule(self, module, excluded: List = []):
        for a in module.__dict__.keys():
            if a.startswith('__') or a in excluded:
                continue
            filepath = getattr(module, a)
            if rx_skipped_sources.search(str(filepath)):
                continue
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
