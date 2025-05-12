from PyQt5.QtCore import QMetaType
from PyQt5.QtWidgets import QApplication
from qgis._core import QgsFields, QgsField, Qgis, QgsProject

from enmapbox import initAll
from enmapbox.exampledata import landcover_polygon
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import TestCase, start_app, TestObjects

start_app()
initAll()


class Issue887Tests(TestCase):

    def test_start_box(self):
        emb = EnMAPBox()
        self.showGui(emb)
        emb.addSource(landcover_polygon)
        emb.close()

    def test_kill_qgis_layer(self):
        # addresses https://github.com/EnMAP-Box/enmap-box/issues/1081
        fields = QgsFields()
        fields.append(QgsField('name', QMetaType.QString))
        lyr = TestObjects.createEmptyMemoryLayer(fields, wkbType=Qgis.WkbType.Point)

        self.assertTrue(lyr.isValid())

        QgsProject.instance().addMapLayer(lyr)

        emb = EnMAPBox()
        emb.ui.show()
        emb.addSource(lyr)
        QApplication.processEvents()
        self.assertTrue(len(emb.dataSources()) > 0)
        # QgsProject.instance().removeAllMapLayers()
        QApplication.processEvents()
        self.showGui(emb.ui)

        emb.close()
