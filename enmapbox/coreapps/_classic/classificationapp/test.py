from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import initQgisApplication
from _classic.classificationapp.core import ClassificationWorkflowApp

if __name__ == '__main__':

    qgsApp = initQgisApplication()

    #import qgisresources.images
    #qgisresources.images.qInitResources()

    enmapBox = EnMAPBox(load_other_apps=False, load_core_apps=False)
    enmapBox.run()
    enmapBox.openExampleData(mapWindows=0)


    enmapBox.addSource(r'C:\Users\janzandr\Desktop\classification.bsq')
    enmapBox.addSource(r'C:\Users\janzandr\Desktop\speclib.gpkg')
    enmapBox.addSource(r'C:\Users\janzandr\Desktop\points.gpkg')

    enmapBox.addSource(r'C:\Users\janzandr\Downloads\stack_data\stack_1999.tif')
    enmapBox.addSource(r'C:\Users\janzandr\Downloads\stack_data\Train_1999_all_groups.shp')



    #for source in [enmap, hires, landcover_polygons, landcover_points, library]:
    #    enmapBox.addSource(source=source)

    try:
        widget = ClassificationWorkflowApp()
        widget.show()

        qgsApp.exec_()
        qgsApp.exitQgis()

    except:
        import traceback
        traceback.print_exc()
