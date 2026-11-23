import unittest

from qgis.PyQt.QtWidgets import QMainWindow

from enmapbox import initAll
from enmapbox.gui.dataviews.dockarea import DockArea
from enmapbox.gui.dataviews.textdock import TextDock, TextDockWidget
from enmapbox.testing import TestCase, start_app

app = start_app()
initAll()


class TextDockTestCases(TestCase):

    def test_widget_title(self):
        da = DockArea()
        w = QMainWindow()
        w.setCentralWidget(da)

        dock = TextDock()

        dock.setTitle('MyDock')
        self.assertEqual(dock.title(), 'MyDock')

        tmp = self.createTestOutputDirectory()
        path1 = tmp / 'testfile1.txt'
        path2 = tmp / 'testfile2.txt'

        with open(path1, 'w', encoding='utf-8') as f:
            f.write('foo')
        with open(path2, 'w', encoding='utf-8') as f:
            f.write('bar')

        dock.textDockWidget().setFile(path1)
        self.assertEqual(dock.title(), path1.name)

        dock.textDockWidget().setFile(path2)
        self.assertEqual(dock.title(), path2.name)

        da.addDock(dock)
        self.showGui(w)

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
