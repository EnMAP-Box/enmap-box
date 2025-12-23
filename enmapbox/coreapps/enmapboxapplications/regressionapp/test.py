from enmapbox.testing import start_app
from enmapboxapplications.widgets.core import *
from enmapboxapplications.regressionapp.core import RegressionWorkflowApp
from enmapbox.exampledata import *

if __name__ == '__main__':

    qgsApp = start_app()

#    import qgisresources.images
#    qgisresources.images.qInitResources()

    enmapBox = EnMAPBox(None)
    enmapBox.run()
#    enmapBox.openExampleData(mapWindows=0)

    enmapBox.addSource(source=r'C:\Work\data\sam_cooper\enmap_subset.bsq')
    enmapBox.addSource(source=r'C:\Work\data\sam_cooper\biomass_training.shp')
    enmapBox.addSource(source=r"C:\Users\janzandr\Desktop\fraction.bsq")


    try:
        widget = RegressionWorkflowApp()
        widget.show()

        qgsApp.exec_()
        qgsApp.exitQgis()

    except:
        import traceback
        traceback.print_exc()
