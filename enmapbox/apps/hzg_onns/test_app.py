from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from hzg_onns import OnnsApp

if __name__ == '__main__':

    qgsApp = start_app()
    enmapBox = EnMAPBox(None)
    enmapBox.run()
    enmapBox.openExampleData(mapWindows=1)
    enmapBox.addApplication(OnnsApp(enmapBox=enmapBox))
    qgsApp.exec_()
    qgsApp.exitQgis()
