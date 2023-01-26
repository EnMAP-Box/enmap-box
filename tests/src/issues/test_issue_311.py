"""
This is a template to create an EnMAP-Box test
"""
import unittest

from qgis.gui import QgsDualView

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.dataviews.docks import SpectralLibraryDock
from enmapbox.testing import EnMAPBoxTestCase
from qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget


class EnMAPBoxTestCaseIssue311(EnMAPBoxTestCase):

    def test_with_enmapbox(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)

        self.assertIsInstance(enmapBox, EnMAPBox)
        self.assertEqual(enmapBox, EnMAPBox.instance())
        dock: SpectralLibraryDock = enmapBox.createDock(SpectralLibraryDock, name='MySpeclib')

        slw: SpectralLibraryWidget = dock.speclibWidget()

        self.assertEqual(slw.actionShowAttributeTable.isChecked(),
                         slw.centralWidget().isVisibleTo(
                             slw) and slw.mMainView.view() == QgsDualView.ViewMode.AttributeTable)
        self.assertEqual(slw.actionShowFormView.isChecked(),
                         slw.centralWidget().isVisibleTo(
                             slw) and slw.mMainView.view() == QgsDualView.ViewMode.AttributeEditor)
        self.assertEqual(slw.actionShowProfileView.isChecked(), slw.mSpeclibPlotWidget.isVisibleTo(slw))
        self.assertEqual(slw.actionShowProfileView.isChecked(), slw.mSpeclibPlotWidget.plotWidget.isVisibleTo(slw))
        self.assertEqual(slw.actionShowProfileView.isChecked()
                         and slw.actionShowProfileViewSettings.isChecked(),
                         slw.mSpeclibPlotWidget.treeView.isVisibleTo(slw))
        self.showGui(enmapBox.ui)


if __name__ == '__main__':
    unittest.main(buffer=False)
