import enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.examples
from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from geetimeseriesexplorerapp import GeeTimeseriesExplorerApp
from qgis.core import QgsVectorLayer
from tests.testdata import landcover_berlin_point_singlepart_3035_gpkg

enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.examples.run()

qgsApp = start_app()
initAll()
enmapBox = EnMAPBox(None)

app = GeeTimeseriesExplorerApp.instance()

# init GUI
app.actionToggleMainDock.trigger()
app.actionToggleProfileDock.trigger()

locations = QgsVectorLayer(landcover_berlin_point_singlepart_3035_gpkg, 'landcover_berlin_point.gpkg')
enmapBox.onDataDropped([locations])

app.mainDock.mLANDSAT_LC08_C02_T1_L2.clicked.emit()
app.profileDock.mLayer.setLayer(locations)
app.profileDock.mDownloadFolder.setFilePath(r'C:\Users\Andreas\Downloads\Profiles')

# app.mainDock.mCOPERNICUS_S1_GRD.clicked.emit()

# app.dockWidget.mCompositeDateStart.setDate(QDate(2020, 8, 1))
# app.dockWidget.mCompositeDateEnd.setDate(QDate(2020, 8, 2))
# app.dockWidget.mCreateComposite.clicked.emit()
qgsApp.exec_()

# use this code for the QGIS version!!!
"""class EventFilter(QObject):
    currentLocation = None
    def eventFilter(self, mapCanvas, event):
        if not isinstance(event, QInputMethodQueryEvent ):
            return False
        location = mapCanvas.mouseLastXY()
        if self.currentLocation != location:
            print(location)
            self.currentLocation = location
        return False

eventFilter = EventFilter()
iface.mapCanvas().installEventFilter(eventFilter)"""

# TASKS
""""
# class Task(QgsTask):
    ...
    def run(self):
        from time import sleep
        sleep(3)
        return True

tasks = [Task() for i in range(1000)]
[QgsApplication.taskManager().addTask(task) for task in tasks]
"""
