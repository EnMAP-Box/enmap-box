import unittest

from qgis.PyQt.QtWidgets import QWidget

from enmapbox import initAll
from enmapbox.gui.dataviews.docks import DockArea
from enmapbox.gui.dataviews.textdock import TextDock, TextDockWidget
from enmapbox.testing import TestCase, start_app

app = start_app()
initAll()


class TextDockTextCases(TestCase):

    def test_widgets(self):
        w = QWidget()
        w.show()

        app.exec()

    def test_TextDock(self):
        da = DockArea()
        self.showGui(da)
        dock = TextDock()
        self.assertIsInstance(dock, TextDock)
        tw = dock.textDockWidget()
        self.assertIsInstance(tw, TextDockWidget)

        testText = """
        foo
        bar
        """
        tw.setText(testText)
        self.assertEqual(testText, tw.text())

        tmp = self.createTestOutputDirectory()
        pathTxt = tmp / 'testfile.txt'
        tw.saveFile(pathTxt)

        with open(pathTxt, encoding='utf-8') as f:
            checkTxt = f.read()
        self.assertEqual(checkTxt, testText)

        tw.setText('')
        self.assertEqual(tw.text(), '')
        tw.setFile(pathTxt)
        self.assertEqual(checkTxt, tw.text())

        da.addDock(dock)
        self.showGui(da)


if __name__ == '__main__':
    unittest.main()
