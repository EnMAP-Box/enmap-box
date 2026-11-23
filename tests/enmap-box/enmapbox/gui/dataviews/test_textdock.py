import unittest

from qgis.PyQt.QtWidgets import QMainWindow

from enmapbox import initAll
from enmapbox.gui.dataviews.dockarea import DockArea
from enmapbox.gui.dataviews.textdock import TextDock, TextDockWidget
from enmapbox.testing import TestCase, start_app

app = start_app()
initAll()


class TextDockTestCases(TestCase):

    def test_textdock_title(self):
        da = DockArea()
        w = QMainWindow()
        w.setCentralWidget(da)

        dock = TextDock()

        dock.setTitle('MyDock')
        self.assertEqual(dock.title(), 'MyDock')
        dock.textDockWidget().setText('Foobar')

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

    def test_textdockwidget(self):
        tw = TextDockWidget()
        tw.setText('Foobar')
        self.assertTrue(tw.btnLoadFile.isEnabled())
        self.assertFalse(tw.btnSaveFile.isEnabled())
        self.assertTrue(tw.btnSaveFileAs.isEnabled())

        tmp = self.createTestOutputDirectory()
        path1 = tmp / 'testfile1.txt'
        tw.saveFile(path1)

        self.assertEqual(tw.windowTitle(), path1.name)

        self.assertTrue(tw.btnLoadFile.isEnabled())
        self.assertTrue(tw.btnSaveFile.isEnabled())
        self.assertTrue(tw.btnSaveFileAs.isEnabled())

        self.showGui(tw)


if __name__ == '__main__':
    unittest.main()
