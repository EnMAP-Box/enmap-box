from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import initQgisApplication
from hzg_onns import OnnsApp

if __name__ == '__main__':

    qgsApp = initQgisApplication()
    enmapBox = EnMAPBox(None)
    enmapBox.run()
    enmapBox.openExampleData(mapWindows=1)
    enmapBox.addApplication(OnnsApp(enmapBox=enmapBox))
    qgsApp.exec_()
    qgsApp.exitQgis()
