import unittest

from enmapbox.coreapps.bandstatisticsapp.bandstatisticsdialog import BandStatisticsDialog
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapbox.testing import EnMAPBoxTestCase, TestObjects, start_app
from qgis.PyQt.QtWidgets import QApplication, QLabel
from qgis.core import QgsMapLayer
from qgis.core import QgsProject
from qgis.gui import QgsMapLayerComboBox

start_app()


class BandStatisticsAppTests(EnMAPBoxTestCase):

    def test_bandstatisticsDialog(self):
        # 1. Setup EnMAP-Box
        # We need an EnMAPBox instance because BandStatisticsDialog calls EnMAPBox.instance()
        eb = EnMAPBox()
        rl = TestObjects.createRasterLayer(ns=10, nl=10, nb=2)
        eb.project().addMapLayer(rl)
        eb.setCurrentLayer(rl)
        EnMAPBox._instance = eb
        p = QgsProject()
        try:
            # 2. Create a test raster layer
            # Create a 10x10, 2 band raster with some values

            # 3. Instantiate the dialog
            dialog = BandStatisticsDialog()
            cb = dialog.mLayer
            self.assertIsInstance(cb, QgsMapLayerComboBox)
            cLyr = None
            for i in range(cb.count()):
                lyr = cb.layer(i)
                if lyr == rl:
                    cLyr = lyr
                    cb.setCurrentIndex(i)
            self.assertTrue(isinstance(cLyr, QgsMapLayer))

            dialog.show()

            try:
                # 4. Select the layer
                # Explicitly set the project to the combobox

                QApplication.processEvents()

                # Mock currentExtent to avoid issues with missing MapCanvas (self.mMapCanvas is None)

                dialog.currentExtent = lambda: SpatialExtent(rl.crs(), rl.extent())

                # 5. Add all bands
                # We need a layer for onAddAllBandsClicked to work.
                # Let's ensure dialog.mLayer.currentLayer() returns rl.
                self.assertEqual(dialog.mLayer.currentLayer(), rl)

                dialog.onAddAllBandsClicked()
                self.assertEqual(dialog.mTable.rowCount(), 2)

                # 6. Run statistics calculation
                dialog.onApplyClicked()
                QApplication.processEvents()

                # 7. Verify the results in the table
                # Band | Histogram | Min | Max | Mean | StdDev
                # Columns 2, 3, 4, 5 are Labels with Min, Max, Mean, StdDev
                for row in range(dialog.mTable.rowCount()):
                    # Min column (index 2)
                    min_label = dialog.mTable.cellWidget(row, 2)
                    self.assertIsInstance(min_label, QLabel)
                    self.assertTrue(len(min_label.text()) > 0)
                    self.assertTrue(float(min_label.text()) >= 0)

                    # Max column (index 3)
                    max_label = dialog.mTable.cellWidget(row, 3)
                    self.assertIsInstance(max_label, QLabel)
                    self.assertTrue(len(max_label.text()) > 0)
                    self.assertTrue(float(max_label.text()) >= 0)

                # 8. Test removing a band
                dialog.mTable.selectRow(0)
                dialog.onRemoveBandClicked()
                self.assertEqual(dialog.mTable.rowCount(), 1)

                # 9. Test deleting all bands
                dialog.onDeleteAllBandsClicked()
                self.assertEqual(dialog.mTable.rowCount(), 0)

            finally:
                dialog.close()
                QApplication.processEvents()

            # Clean up layers
            p.removeAllMapLayers()
            QgsProject.instance().removeMapLayer(rl)

        finally:
            eb.close()
            EnMAPBox._instance = None
            QApplication.processEvents()


if __name__ == '__main__':
    unittest.main()
