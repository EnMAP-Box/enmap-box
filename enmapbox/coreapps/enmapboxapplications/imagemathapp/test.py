from enmapbox.testing import start_app
from enmapboxapplications.widgets.core import *
from enmapboxapplications.imagemathapp.core import *

if __name__ == '__main__':

    qgsApp = start_app()

#    import qgisresources.images
#    qgisresources.images.qInitResources()

    enmapBox = EnMAPBox(None)
#    enmapBox.loadExampleData()
    enmapBox.run()


#    openTestdata()
#    import enmapboxtestdata
#    enmap = QgsRasterLayer(enmapboxtestdata.enmap, baseName=os.path.basename(enmapboxtestdata.enmap))
#    landcover = QgsVectorLayer(enmapboxtestdata.landcover_polygons, baseName=os.path.basename(enmapboxtestdata.landcover_polygons))

    widget = ImageMathApp()
#    widget.addInput(name='enmap', layer=enmap)
#    widget.addInput(name='mask', layer=landcover)
    widget.addOutput(name='result', filename='/vsimem/result.bsq')

    code = \
'''result = enmap
result[:, mask[0] == 0] = noDataValue(enmap)
setNoDataValue(result, noDataValue(enmap))
setMetadata(result, metadata(enmap))
'''
    widget.setCode(code=code)

    widget.show()

    qgsApp.exec_()
    qgsApp.exitQgis()












