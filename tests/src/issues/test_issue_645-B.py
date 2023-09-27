import pathlib
import sys
from PyQt5.QtWidgets import QWidget, QHBoxLayout

from enmapbox import initAll, DIR_UNITTESTS
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import \
    SpectralProcessingModelCreatorAlgorithmWrapper
from enmapbox.testing import start_app

library_berlin = r'F:\Repositories\QGIS-Plugins\enmap-box\tests\testdata\exampledata\berlin\library_berlin.gpkg'
from qgis.core import QgsProcessingContext, QgsProject, QgsProcessingRegistry, QgsApplication, QgsProcessingAlgorithm
from qgis.core import QgsVectorLayer

app = None
if not isinstance(QgsApplication.instance(), QgsApplication):
    app = start_app()
    initAll()
a = 'enmapbox:TranslateRasterLayer'
# a = 'enmapbox:SpectralResamplingToWavelength'
# a = 'gdal:translate'
reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
alg: QgsProcessingAlgorithm = reg.algorithmById(a)
assert isinstance(alg, QgsProcessingAlgorithm)
sl = QgsVectorLayer(library_berlin)
sl.startEditing()
context = QgsProcessingContext()
project = QgsProject()
context.setProject(project)

p = QWidget()
w = SpectralProcessingModelCreatorAlgorithmWrapper(alg, sl, context, parent=p)
# w.initWidgets()
p.setLayout(QHBoxLayout())
p.layout().addWidget(w)
p.show()

if app:
    app.exec_()



