"""
This is a template to create an EnMAP-Box test
"""
import unittest

from enmapbox.gui.dataviews.docks import SpectralLibraryDock
from qgis.PyQt.QtWidgets import QApplication
from qgis._gui import QgsDualView
from qgis.core import QgsApplication, QgsRasterLayer, QgsVectorLayer
from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from enmapbox import EnMAPBox
from qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget


class EnMAPBoxTestCaseIssue311(EnMAPBoxTestCase):

    def test_with_enmapbox(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)

        self.assertIsInstance(enmapBox, EnMAPBox)
        self.assertEqual(enmapBox, EnMAPBox.instance())
        dock: SpectralLibraryDock = enmapBox.createDock(SpectralLibraryDock, name='MySpeclib')

        slw: SpectralLibraryWidget = dock.speclibWidget()

        QgsApplication.processEvents()

        self.assertEqual(slw.actionShowAttributeTable.isChecked(),
                         slw.mMainView.isVisible() and slw.mMainView.view() == QgsDualView.ViewMode.AttributeTable)
        self.assertEqual(slw.actionShowFormView.isChecked(),
                         slw.mMainView.isVisible() and slw.mMainView.view() == QgsDualView.ViewMode.AttributeEditor)
        self.assertEqual(slw.actionShowProfileView.isChecked(), slw.mSpeclibPlotWidget.isVisible())
        self.assertEqual(slw.actionShowProfileView.isChecked(), slw.mSpeclibPlotWidget.plotWidget.isVisible())
        self.assertEqual(slw.actionShowProfileViewSettings.isChecked(), slw.mSpeclibPlotWidget.treeView.isVisble())
        self.showGui(enmapBox.ui)

if __name__ == '__main__':
    unittest.main(buffer=False)
