from qgis.PyQt.QtWidgets import QFormLayout, QDialog
from qgis.core import QgsRasterLayer, Qgis
from qgis.gui import QgsMapLayerComboBox

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.widgets.spectralrasterbandcombobox.spectralrasterbandcombobox import SpectralRasterBandComboBox
from enmapbox.testing import start_app
from enmapboxtestdata import fraction_map_l3

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
enmapBox.loadExampleData()
enmapBox.onDataDropped([QgsRasterLayer(fraction_map_l3, 'fraction')])


class TestDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Raster Band Selection")

        # Raster layer combo box
        self.layerCombo = QgsMapLayerComboBox()
        self.layerCombo.setAllowEmptyLayer(True)
        self.layerCombo.setFilters(Qgis.LayerFilter.RasterLayer)
        self.layerCombo.setProject(enmapBox.project())

        # Raster band combo box
        self.bandCombo = SpectralRasterBandComboBox()
        self.bandCombo.initBandButtons()

        # Connect layer selection to band selection
        self.layerCombo.layerChanged.connect(self.bandCombo.setLayer)

        # Layout
        layout = QFormLayout(self)
        layout.addRow("Raster layer:", self.layerCombo)
        layout.addRow("Band:", self.bandCombo)


dlg = TestDialog()
dlg.show()

qgsApp.exec()
