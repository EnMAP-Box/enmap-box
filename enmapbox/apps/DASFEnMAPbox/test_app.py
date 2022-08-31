from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import initQgisApplication
from DASFEnMAPbox import DASFretrievalApp

if __name__ == '__main__':

    qgsApp = initQgisApplication()
    enmapBox = EnMAPBox(None)
    enmapBox.run()
    enmapBox.openExampleData(mapWindows=1)
    enmapBox.addApplication(DASFretrievalApp(enmapBox=enmapBox))
    qgsApp.exec_()
    qgsApp.exitQgis()
