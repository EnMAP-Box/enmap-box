from classificationworkflowapp.classificationworkflowgui import ClassificationWorkflowGui
from enmapbox import EnMAPBox
from enmapbox.testing import initQgisApplication
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer

if __name__ == '__main__':

    qgsApp = initQgisApplication()
    enmapBox = EnMAPBox(load_other_apps=False, load_core_apps=False)
    enmapBox.run()
    # enmapBox.ui.hide()
    # enmapBox.openExampleData(mapWindows=1)

    layers = [
        QgsVectorLayer(r'C:\Work\data\_showcase\landcover_berlin_point.shp', 'landcover_berlin_point'),
        QgsVectorLayer(r'C:\Work\data\_showcase\landcover_berlin_polygon.shp', 'landcover_berlin_polygon'),
        QgsRasterLayer(r'C:\Work\data\_showcase\enmap_berlin.bsq', 'enmap_berlin')
    ]

    enmapBox.addSource(r'C:\Work\data\_showcase\landcover_berlin_point.shp')
    enmapBox.addSource(r'C:\Work\data\_showcase\landcover_berlin_polygon.shp')
    enmapBox.addSource(r'C:\Work\data\_showcase\enmap_berlin.bsq')

    QgsProject.instance().addMapLayers(layers)

    try:
        widget = ClassificationWorkflowGui(enmapBox.ui)
        widget.show()
        # widget.mFileClassifierFitted.setFilePath(classifierDumpPkl)
        # widget.mFileDataset.setFilePath(classifierDumpPkl)
        # widget.onDatasetChanged()
        qgsApp.exec_()
        qgsApp.exitQgis()
    except Exception:
        import traceback

        traceback.print_exc()
