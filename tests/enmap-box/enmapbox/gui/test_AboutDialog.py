import unittest

from enmapbox.testing import EnMAPBoxTestCase, start_app

start_app()


class TestCasesAboutDialog(EnMAPBoxTestCase):

    def test_AboutDialog(self):
        from enmapbox.gui.about import AboutDialog
        d = AboutDialog()
        self.assertIsInstance(d, AboutDialog)
        self.showGui(d)


if __name__ == '__main__':
    unittest.main()
