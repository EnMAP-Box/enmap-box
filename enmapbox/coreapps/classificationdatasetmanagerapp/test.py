from classificationdatasetmanagerapp import ClassificationDatasetManagerGui
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.utils import Utils
from tests.enmapboxtestdata import classifierDumpSkops

qgsApp = start_app()
enmapBox = EnMAPBox()
enmapBox.run()

Utils.modelDump(Utils.modelLoad(classifierDumpSkops), 'classifier.skops')
enmapBox.addSource('classifier.skops')

widget = ClassificationDatasetManagerGui(enmapBox.ui)
widget.show()

qgsApp.exec_()
