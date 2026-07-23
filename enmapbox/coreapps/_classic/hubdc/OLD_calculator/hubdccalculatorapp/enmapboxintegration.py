import os, tempfile
from PyQt4.QtGui import QIcon
from enmapbox.gui.applications import EnMAPBoxApplication
import _classic.hubdc.calculator.gui

uidir = os.path.join(os.path.dirname(_classic.hubdc.calculator.gui.__file__))

class HubDatacubeCalculatorApp(EnMAPBoxApplication):

    def __init__(self, enmapBox, parent=None):
        EnMAPBoxApplication.__init__(self, enmapBox, parent=parent)
        self.name = 'imageMath Calculator'
        self.version = 'Version 0.1.1'
        self.licence = 'GPL-3'

    def icon(self):
        return QIcon(os.path.join(uidir, 'icons', 'numpy.png'))

    def menu(self, appMenu):
        appMenu = self.enmapbox.menu('Tools')
        a = self.utilsAddActionInAlphanumericOrder(appMenu, 'imageMath Calculator')
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return a

    def startGUI(self, *args):

        ui = _classic.hubdc.calculator.gui.CalculatorMainWindow(parent=self.enmapbox.ui)

        self.enmapbox.sigRasterSourceAdded.connect(lambda filename: ui.insertRasterInput(name=os.path.basename(filename), filename=filename))
        self.enmapbox.sigVectorSourceAdded.connect(lambda filename: ui.insertVectorInput(name=os.path.basename(filename), filename=filename))

        for uri in self.enmapbox.dataSources('RASTER'):
            ui.insertRasterInput(name=os.path.basename(uri), filename=uri)
        for uri in self.enmapbox.dataSources('VECTOR'):
            ui.insertVectorInput(name=os.path.basename(uri), filename=uri)
        ui.insertRasterOutput(name='result', filename=os.path.join(tempfile.gettempdir(), 'result.img'))
        ui.show()
