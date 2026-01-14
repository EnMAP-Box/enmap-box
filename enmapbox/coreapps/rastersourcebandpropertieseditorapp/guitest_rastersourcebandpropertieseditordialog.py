from rastersourcebandpropertieseditorapp.rastersourcebandpropertieseditordialog import \
    RasterSourceBandPropertiesEditorDialog
from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.exampledata import enmap
from enmapbox.testing import start_app

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
enmapBox.addSource(enmap)

widget = RasterSourceBandPropertiesEditorDialog()
widget.show()

qgsApp.exec_()
