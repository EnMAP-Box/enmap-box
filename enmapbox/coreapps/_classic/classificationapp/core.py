import inspect
import tempfile
import traceback

from PyQt5.uic import loadUi
from qgis.core import QgsPalettedRasterRenderer
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibrary
from enmapbox.qgispluginsupport.qps.speclib.core import is_spectral_library
from _classic.hubdsm.core.color import Color as HubdsmColor
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.qgsvectorclassificationscheme import QgsVectorClassificationScheme
from _classic.hubdsm.processing.savelayerasclassification import saveLayerAsClassification
from _classic.hubflow.core import *
from _classic.classificationapp.script import classificationWorkflow, ProgressBar

pathUi = join(dirname(__file__), 'ui')


class ClassificationWorkflowApp(QMainWindow):
    uiTrainingType_: QComboBox
    uiType0Raster_: QgsMapLayerComboBox
    uiType0Classification_: QgsMapLayerComboBox
    uiType1Raster_: QgsMapLayerComboBox
    uiType1VectorClassification_: QgsMapLayerComboBox
    uiType1Dialog_: QToolButton
    uiType2Library_: QgsMapLayerComboBox

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        loadUi(join(pathUi, 'main.ui'), self)
        self.uiInfo_ = QLabel()
        self.statusBar().addWidget(self.uiInfo_, 1)

        self.initMaps()
        self.initClassifier()
        self.initOutputs()

        self.uiTrainingType_.currentIndexChanged.connect(self.clearTrainingData)
        self.uiType0Raster_.layerChanged.connect(self.initClasses)
        self.uiType0Classification_.layerChanged.connect(self.initClasses)
        self.uiType1Dialog_.clicked.connect(self.openType1Dialog)
        self.uiType1Raster_.layerChanged.connect(self.initClasses)
        self.uiType1VectorClassification_.layerChanged.connect(self.initClasses)
        self.uiType2Library_.layerChanged.connect(self.initClasses)

        self.uiSampleSizePercent_.valueChanged.connect(self.updateSpinboxes)
        self.uiSampleSizePixel_.valueChanged.connect(self.updateSpinboxes)
        self.uiApply_.clicked.connect(self.updateSpinboxes)

        self.uiExecute_.clicked.connect(self.execute)

        self.spinboxes = None

    def openType1Dialog(self):
        layer = self.uiType1VectorClassification_.currentLayer()
        if layer is not None:
            CategoryFieldSelectionDialog.openLayerPropertiesDialog(layer=layer, parent=self)
        self.uiType1VectorClassification_.setLayer(layer=None)
        self.uiType1VectorClassification_.setLayer(layer=layer)

    def clearTrainingData(self):
        self.uiType0Raster_.setLayer(None)
        self.uiType0Classification_.setLayer(None)
        self.uiType1Raster_.setLayer(None)
        self.uiType1VectorClassification_.setLayer(None)
        self.uiType2Library_.setLayer(None)

    def initMaps(self):
        self.uiType0Raster_.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.uiType0Classification_.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.uiType1Raster_.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.uiType1VectorClassification_.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.uiType2Library_.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.uiRaster2_.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def progressBar(self):
        return ProgressBar(bar=self.uiProgressBar())

    def log(self, text):
        self.uiInfo_.setText(str(text))
        QCoreApplication.processEvents()

    def uiProgressBar(self):
        obj = self.uiProgressBar_
        assert isinstance(obj, QProgressBar)
        return obj

    def pickClassColor(self):
        w = self.sender()
        color = QColorDialog.getColor()
        if color.name() != '#000000':
            w.setStyleSheet('background-color: {}'.format(color.name()))

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_F1:
            self.onAdvancedClicked()

    def updateSpinboxes(self, *args):
        self.log('')

        if self.uiSampeMode_.currentText() == 'Percent':
            value = float(self.uiSampleSizePercent_.value())
        else:
            value = float(self.uiSampleSizePixel_.value())

        for spinbox, count in zip(self.spinboxes, self.counts):
            if self.uiSampeMode_.currentText() == 'Percent':
                spinbox.setValue(int(round(count * value / 100.)))
            else:
                spinbox.setValue(int(value))

    def filenameTmpClassification(self):
        return '/vsimem/classification_workflow/classification.bsq'

    def filenameTmpRaster(self):
        return '/vsimem/classification_workflow/raster.bsq'

    def initClasses(self, *args):
        self.log('')
        self.spinboxes = None
        self.uiStacked_.setEnabled(False)
        self.widget_.hide()
        self.widget_ = QWidget()
        self.layout_.addWidget(self.widget_)
        layout = QHBoxLayout(self.widget_)
        self.updateTotalSamples()

        if self.uiTrainingType_.currentIndex() == 0: # raster
            rasterLayer: QgsRasterLayer = self.uiType0Raster_.currentLayer()
            classificationLayer: QgsRasterLayer = self.uiType0Classification_.currentLayer()
            if rasterLayer is None or classificationLayer is None:
                return

            if not isinstance(classificationLayer.renderer(), QgsPalettedRasterRenderer):
                self.log('Selected layer is not a valid classification (requires Paletted/Unique values renderer).')
                self.uiType0Classification_.setLayer(None)
                return

            saveLayerAsClassification(
                qgsMapLayer=classificationLayer,
                filename=self.filenameTmpClassification()
            )

            classification = Classification(filename=self.filenameTmpClassification())
        elif self.uiTrainingType_.currentIndex() == 1: # vector
            rasterLayer: QgsRasterLayer = self.uiType1Raster_.currentLayer()
            vectorClassificationLayer: QgsVectorLayer = self.uiType1VectorClassification_.currentLayer()
            if rasterLayer is None or vectorClassificationLayer is None:
                return

            if not isinstance(vectorClassificationLayer.renderer(), QgsCategorizedSymbolRenderer):

                dlg = CategoryFieldSelectionDialog(layer=vectorClassificationLayer, parent=self)
                if dlg.exec_():
                    fieldName = dlg.field.currentField()
                    fields: QgsFields = vectorClassificationLayer.fields()
                    fieldIndex = fields.indexFromName(fieldName)
                    uniqueValues = vectorClassificationLayer.uniqueValues(fieldIndex)
                    categories = list()
                    for value in uniqueValues:
                        name = str(value)
                        color = HubdsmColor.fromRandom()
                        color = QColor(color.red, color.green, color.blue).name()
                        symbol = QgsMarkerSymbol.createSimple(
                        {'color': color, 'size': '2', 'outline_color': 'black'})
                        categories.append(QgsRendererCategory(value, symbol, name, True))
                    renderer = QgsCategorizedSymbolRenderer(fieldName, categories)
                    vectorClassificationLayer.setRenderer(renderer)

                    if dlg.checkBox.isChecked():
                        CategoryFieldSelectionDialog.openLayerPropertiesDialog(
                            layer=vectorClassificationLayer, parent=self
                        )

                else:
                    self.uiType1VectorClassification_.setLayer(None)
                    return

            raster = Raster(filename=self.uiType1Raster_.currentLayer().source())

            if not raster.dataset().projection().equal(
                    Vector(filename=vectorClassificationLayer.source()).dataset().projection()
            ):
                self.log('Projection mismatch between Raster and Vector Classification.')
                return

            self.log('Rasterize vector classification on raster grid')
            saveLayerAsClassification(
                qgsMapLayer=vectorClassificationLayer,
                grid=GdalRaster.open(raster.filename()).grid,
                filename=self.filenameTmpClassification()
            )
            self.log('')

            classification = Classification(filename=self.filenameTmpClassification())
            self.progressBar().setPercentage(0)

        elif self.uiTrainingType_.currentIndex() == 2: # speclib
            libraryLayer: QgsVectorLayer = self.uiType2Library_.currentLayer()
            if libraryLayer is None:
                return

            try:
                renderer = libraryLayer.renderer().clone()
                libraryLayer = SpectralLibrary(name=libraryLayer.name(), uri=libraryLayer.source())
                libraryLayer.setRenderer(renderer)
            except:
                self.uiType2Library_.setLayer(None)
                self.log('Selected layer is not a valid library.')
                return

            assert is_spectral_library(libraryLayer)

            if not isinstance(libraryLayer.renderer(), QgsCategorizedSymbolRenderer):
                self.uiType2Library_.setLayer(None)
                self.log('Selected layer is not a valid library classification (requires Categorized renderer).')
                return

            qgsVectorClassificationScheme = QgsVectorClassificationScheme.fromQgsVectorLayer(
                qgsVectorLayer=libraryLayer
            )

            # make pseudo raster
            X = list()
            y = list()
            fieldIndex = None
            for profile in libraryLayer:
                if fieldIndex is None:
                    fieldIndex = profile.fieldNames().index(qgsVectorClassificationScheme.classAttribute)
                label = profile.attribute(fieldIndex)
                if label not in qgsVectorClassificationScheme.categories:
                    continue
                category = qgsVectorClassificationScheme.categories[label]
                y.append(category.id)
                X.append(profile.values()['y'])
            X = np.array(X, dtype=np.float64)
            y = np.array(y)
            raster = Raster.fromArray(
                array=np.atleast_3d(X.T),
                filename=self.filenameTmpRaster()
            )
            classification = GdalRaster.createFromArray(
                array=np.atleast_3d(y),
                filename=self.filenameTmpClassification()
            )
            classification.setCategories(list(qgsVectorClassificationScheme.categories.values()))
            del classification
            classification = Classification(self.filenameTmpClassification())
        else:
            assert 0

        counts = classification.statistics()
        self.counts = counts

        self.spinboxes = list()
        self.colors = list()
        self.names = list()

        for i in range(classification.classDefinition().classes()):

            layout1 = QVBoxLayout()
            layout2 = QHBoxLayout()
            color = QToolButton()
            color.setStyleSheet(
                'background-color: {}'.format(classification.classDefinition().color(i + 1)._qColor.name()))
            color.setMaximumWidth(25)
            color.setMaximumHeight(18)

            color.setAutoRaise(True)
            color.clicked.connect(self.pickClassColor)
            self.colors.append(color)
            layout2.addWidget(color)
            layout2.addWidget(QLabel('{}:'.format(i + 1)))
            name = QLineEdit(classification.classDefinition().name(i + 1))
            text = name.text()
            fm = name.fontMetrics()
            w = fm.boundingRect(text).width()
            name.resize(w, name.height())
            name.setMinimumWidth(w + 10)
            layout2.addWidget(name)
            # layout2.addWidget(QLabel('({} px)  '.format(counts[i])))
            self.names.append(name)
            layout1.addLayout(layout2)

            # layout3 = QHBoxLayout()
            spinbox = QSpinBox()
            spinbox.setRange(0, counts[i])
            spinbox.setSingleStep(1)
            spinbox.setValue(counts[i])
            spinbox.setSuffix(' ({} px)'.format(counts[i]))
            spinbox.valueChanged.connect(self.updateTotalSamples)
            self.spinboxes.append(spinbox)
            layout1.addWidget(spinbox)
            # layout3.addWidget(QLabel('({} px)  '.format(counts[i])))
            # layout1.addLayout(layout3)

            layout.addLayout(layout1)

            self.updateTotalSamples()

        # self.widget_.adjustSize()
        # self.adjustSize()

        self.uiStacked_.setEnabled(True)

    def updateTotalSamples(self, *args):
        total = 0
        if self.spinboxes is not None:
            for spinbox in self.spinboxes:
                total += int(spinbox.value())
        self.uiTotalSampleSize_.setText('Total sample size = {}'.format(total))

    def initClassifier(self):
        from _classic.enmapboxgeoalgorithms.algorithms import ALGORITHMS, ClassifierFit
        self.classifiers = [alg for alg in ALGORITHMS if isinstance(alg, ClassifierFit)]
        self.classifierNames = [alg.name()[3:] for alg in self.classifiers]
        self.uiClassifier_.addItems(self.classifierNames)
        self.uiClassifier_.currentIndexChanged.connect(
            lambda index: self.uiCode_.setText(self.classifiers[index].code()))
        self.uiClassifier_.setCurrentIndex(self.classifierNames.index('RandomForestClassifier'))

    def initOutputs(self):
        outdir = tempfile.gettempdir()
        self.uiSampledClassificationFilename_.setStorageMode(QgsFileWidget.SaveFile)
        self.uiModelFilename_.setStorageMode(QgsFileWidget.SaveFile)
        self.uiClassificationFilename_.setStorageMode(QgsFileWidget.SaveFile)
        self.uiProbabilityFilename_.setStorageMode(QgsFileWidget.SaveFile)
        self.uiReportFilename_.setStorageMode(QgsFileWidget.SaveFile)
        self.uiSampledClassificationFilename_.setFilePath(join(outdir, 'sample.bsq'))
        self.uiModelFilename_.setFilePath(join(outdir, 'classifier.pkl'))
        self.uiClassificationFilename_.setFilePath(join(outdir, 'classification.bsq'))
        self.uiProbabilityFilename_.setFilePath(join(outdir, 'probability.bsq'))
        self.uiReportFilename_.setFilePath(join(outdir, 'accass.html'))

    def execute(self, *args):
        self.log('')

        try:
            saveSampledClassification = self.uiSampledClassificationFilename_.isEnabled()
            saveSampledClassificationComplement = saveSampledClassification  # self.uiSampledClassificationComplementFilename_.isEnabled()
            saveModel = self.uiModelFilename_.isEnabled()
            saveClassification = self.uiClassificationFilename_.isEnabled()
            saveProbability = self.uiProbabilityFilename_.isEnabled()
            saveRGB = self.uiRGB_.isEnabled()
            saveReport = self.uiReportFilename_.isEnabled()
            filenameSampledClassification = self.uiSampledClassificationFilename_.filePath()
            filenameSampledClassificationComplement = '{}_complement{}'.format(
                *splitext(filenameSampledClassification)
            )
            filenameModel = self.uiModelFilename_.filePath()
            filenameClassification = self.uiClassificationFilename_.filePath()
            filenameProbability = self.uiProbabilityFilename_.filePath()
            filenameReport = self.uiReportFilename_.filePath()

            if self.uiTrainingType_.currentIndex() == 0: # raster
                qgsRaster = self.uiType0Raster_.currentLayer()
                qgsClassification = self.uiType0Classification_.currentLayer()
                if qgsRaster is None:
                    self.log('Error: no raster selected')
                    return
                if qgsClassification is None:
                    self.log('Error: no classification selected')
                    return
                raster = Raster(filename=qgsRaster.source())
            elif self.uiTrainingType_.currentIndex() == 1:  # vector
                qgsRaster = self.uiType1Raster_.currentLayer()
                qgsClassification = self.uiType1VectorClassification_.currentLayer()
                if qgsRaster is None:
                    self.log('Error: no raster selected')
                    return
                if qgsClassification is None:
                    self.log('Error: no classification selected')
                    return
                raster = Raster(filename=qgsRaster.source())
            elif self.uiTrainingType_.currentIndex() == 2:  # speclib
                raster = Raster(filename=self.filenameTmpRaster())
            else:
                assert 0

            colors = list()
            for w in self.colors:
                hex = w.styleSheet().split(' ')[1]
                colors.append(Color(hex))

            names = list()
            for w in self.names:
                names.append(w.text())

            classDefinition = ClassDefinition(names=names, colors=colors)

            classification = Classification(filename=self.filenameTmpClassification(), classDefinition=classDefinition)

            #if not raster.grid().equal(other=classification.grid()):
            #    self.log('Error: raster and reference grids do not match')
            #    return

            sample = ClassificationSample(raster=raster, classification=classification)

            qgsRaster2 = self.uiRaster2_.currentLayer()
            if (saveClassification or saveProbability) and (qgsRaster2 is None):
                self.log('Error: no raster for mapping selected')
                return
            raster2 = Raster(filename=qgsRaster2.source())

            qgsMask2 = self.uiMask_.currentLayer()
            if isinstance(qgsMask2, QgsRasterLayer):
                mask2 = Mask(filename=qgsMask2.source())
                if not raster.grid().equal(other=mask2.grid()):
                    self.log('Error: raster and mask grids do not match')
                    return
            elif isinstance(qgsMask2, QgsVectorLayer):
                mask2 = VectorMask(filename=qgsMask2.source())
            elif qgsMask2 is None:
                mask2 = None
            else:
                assert 0

            n = [spinbox.value() for spinbox in self.spinboxes]
            if np.sum(n) == np.sum(self.counts):  # perform no random sampling if all samples are used
                n = None

            cv = self.uiNFold_.value()

            namespace = dict()
            code = self.uiCode_.toPlainText()
            exec(code, namespace)
            sklEstimator = namespace['estimator']
            classifier = Classifier(sklEstimator=sklEstimator)

            self.uiExecute_.setEnabled(False)

            classificationWorkflow(sample=sample,
                classifier=classifier,
                raster=raster2,
                mask=mask2,
                n=n,
                cv=cv,
                saveSampledClassification=saveSampledClassification,
                saveSampledClassificationComplement=saveSampledClassificationComplement,
                saveModel=saveModel,
                saveClassification=saveClassification,
                saveProbability=saveProbability,
                saveRGB=saveRGB,
                saveReport=saveReport,
                filenameSampledClassification=filenameSampledClassification,
                filenameSampledClassificationComplement=filenameSampledClassificationComplement,
                filenameModel=filenameModel,
                filenameClassification=filenameClassification,
                filenameProbability=filenameProbability,
                filenameReport=filenameReport,
                ui=self)
            self.log('Done!')
            self.progressBar().setPercentage(0)
            self.uiExecute_.setEnabled(True)


        except Exception as error:
            traceback.print_exc()
            self.log('Error: {}'.format(str(error)))
            self.uiExecute_.setEnabled(True)


class CategoryFieldSelectionDialog(QDialog):

    def __init__(self, layer: QgsVectorLayer, *args, **kwargs):
        super(CategoryFieldSelectionDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle('Invalid Vector Classification')
        self.layer = layer

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.field = QgsFieldComboBox()
        self.field.setLayer(layer=layer)
        self.field.setCurrentIndex(0)
        self.field.setAllowEmptyFieldName(False)
        self.checkBox = QCheckBox('Open layer styling dialog for changing class names and colors?')
        self.checkBox.setChecked(True)
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel('Selected layer is not a well defined vector classification.'))
        self.layout.addWidget(QLabel('This can be fixed by changing the layer styling to categorized rendering.'))
        self.layout.addWidget(QLabel(''))
        self.layout.addWidget(QLabel('Please select a value field used for categorization.'))
        self.layout.addWidget(self.field)
        self.layout.addWidget(self.checkBox)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.resize(300, 50)

    @staticmethod
    def openLayerPropertiesDialog(layer: QgsVectorLayer, parent: QWidget):
        from enmapbox.qgispluginsupport.qps.layerproperties import LayerPropertiesDialog
        dialog = LayerPropertiesDialog(layer, parent=parent)
        dialog.mOptionsListWidget.setCurrentRow(2)
        dialog.setModal(True)
        dialog.exec_()
