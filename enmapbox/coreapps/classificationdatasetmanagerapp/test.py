from classificationdatasetmanagerapp import ClassificationDatasetManagerGui
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.utils import Utils
from tests.enmapboxtestdata import classifierDumpPkl

qgsApp = start_app()
enmapBox = EnMAPBox()
enmapBox.run()

Utils.pickleDump(Utils.pickleLoad(classifierDumpPkl), 'classifier.pkl')
enmapBox.addSource('classifier.pkl')

widget = ClassificationDatasetManagerGui(enmapBox.ui)
widget.show()

qgsApp.exec_()
