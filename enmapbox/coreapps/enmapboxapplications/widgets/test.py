import os
import tempfile

from qgis.core import QgsProject

from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtXml import QDomDocument
from PyQt5 import uic
import enmapboxtestdata
import _classic.hubdc.core

from enmapboxapplications.widgets.core import *
from enmapboxapplications.synthmixapp.core import SynthmixApp
from enmapboxapplications.scatterplotapp.core import ScatterPlotApp


if __name__ == '__main__':

    qgsApp = QgsApplication([], True)
    qgsApp.initQgis()

    import qgisresources.images
    qgisresources.images.qInitResources()

    #enmapBox = EnMAPBox(None)
    #enmapBox.run()
    #enmapBox.openExampleData(mapWindows=1)
#    enmapBox.addSource(r'C:\Work\EnMAP-Box\enmapProject\lib\hubAPI\resource\testData\speclib\EndmemberSpeclib')
#    enmapBox.addSource(enmapboxtestdata.speclib)

#    widget = UiLibrary()
    #widget = UiLabeledLibrary()
    #widget = ScatterPlotApp()
    widget = UiWorkflowMainWindow()
    widget.show()

    qgsApp.exec_()
    qgsApp.exitQgis()
