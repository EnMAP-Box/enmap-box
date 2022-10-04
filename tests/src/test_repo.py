import pathlib
import re
import typing
import unittest

from enmapbox.qgispluginsupport.qps.utils import file_search, loadUi
from enmapbox.testing import TestCase

DIR_REPO = pathlib.Path(__file__).parents[1]

DIR_DOCS = DIR_REPO / 'doc'
DIR_CODE = DIR_REPO / 'enmapbox'


class TestRepository(TestCase):

    def test_ui_files(self):

        rx = re.compile(r'.*\.ui$')
        ERRORS: typing.Dict[str, Exception] = dict()
        for uifile in file_search(DIR_REPO, rx, recursive=True):
            try:
                fmt = loadUi(uifile)
            except Exception as ex:
                ERRORS[uifile] = ex
        messages = []
        for path, ex in ERRORS.items():
            ex: Exception
            messages.append(f'\t{path}: {ex}')
        messages = '\n'.join(messages)
        self.assertTrue(len(ERRORS) == 0, msg=f'Unable to loads {len(ERRORS)} *.ui files:\n\t{messages}')


if __name__ == '__main__':
    unittest.main(buffer=False)
