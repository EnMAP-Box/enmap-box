from classificationdatasetmanagerapp import ClassificationDatasetManagerGui
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import initQgisApplication
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classifierDumpPkl

qgsApp = initQgisApplication()
enmapBox = EnMAPBox()
enmapBox.run()

Utils.pickleDump(Utils.pickleLoad(classifierDumpPkl), 'classifier.pkl')
enmapBox.addSource('classifier.pkl')

widget = ClassificationDatasetManagerGui(enmapBox.ui)
widget.show()

qgsApp.exec_()
