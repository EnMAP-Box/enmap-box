import unittest
from enmapbox.testing import EnMAPBoxTestCase


class TestCasesAboutDialog(EnMAPBoxTestCase):

    def test_AboutDialog(self):
        from enmapbox.gui.about import AboutDialog
        d = AboutDialog()
        self.assertIsInstance(d, AboutDialog)
        self.showGui(d)


if __name__ == '__main__':
    unittest.main()
