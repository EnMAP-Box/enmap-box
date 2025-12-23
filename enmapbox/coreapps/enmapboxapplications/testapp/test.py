from enmapboxapplications.widgets.core import *
from enmapboxapplications.testapp.core import TestWorkflow

if __name__ == '__main__':

    import qgisresources.images
    qgisresources.images.qInitResources()

    qgsApp = QgsApplication([], True)
    qgsApp.initQgis()



    try:
        widget = TestWorkflow()
        widget.show()

        qgsApp.exec_()
        qgsApp.exitQgis()

    except:
        import traceback
        traceback.print_exc()

