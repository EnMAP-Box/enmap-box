import inspect
import tempfile
import traceback

from PyQt5.uic import loadUi
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from _classic.hubflow.core import *
from enmapboxapplications.regressionapp.script import regressionWorkflow, ProgressBar

pathUi = join(dirname(__file__), 'ui')


class RegressionWorkflowApp(QMainWindow):

    def __init__(self, parent=None):

        QMainWindow.__init__(self, parent)
        loadUi(join(pathUi, 'main.ui'), self)
        #self.setupUi(self)
        self.uiInfo_ = QLabel()
        self.statusBar().addWidget(self.uiInfo_, 1)

        self.initMaps()
        self.initClassifier()
        self.initOutputs()
        self.uiRaster_.layerChanged.connect(self.onRasterLayerChanged)
        self.uiRegression_.layerChanged.connect(self.onRegressionLayerChanged)
        self.uiExecute_.clicked.connect(self.execute)
        self.uiAttribute_.fieldChanged.connect(self.clearStrata)
        self.uiAttribute_.fieldChanged.connect(self.initStrata)
        self.uiApplyStrata_.clicked.connect(self.initStrata)
        self.uiAttribute_.hide()
        self.uiAttributeLabel_.hide()
        # self.uiOversampling_.valueChanged.connect(self.onRasterizationOptionsChanged)
        # self.uiPurity_.valueChanged.connect(self.onRasterizationOptionsChanged)
        # self.uiAdvanced_.clicked.connect(self.onAdvancedClicked)
        self.uiAdvanced_.hide()  # advanced button not wanted :-(, use F1 key instead :-)
        self.uiSampleSizePercent_.valueChanged.connect(self.updateSpinboxes)
        self.uiSampleSizePixel_.valueChanged.connect(self.updateSpinboxes)
        self.uiApply_.clicked.connect(self.updateSpinboxes)
        self.uiStacked_.setEnabled(False)
        self.spinboxes = None
        # self._advancedWidgets = [self.uiOversampling_, self.uiPurity_]
        # self.onAdvancedClicked()

    def progressBar(self):
        return ProgressBar(bar=self.uiProgressBar())

    def log(self, text):
        self.uiInfo_.setText(str(text))
        QCoreApplication.processEvents()

    def uiAttributeLabel(self):
        obj = self.uiAttributeLabel_  # inspect.getcurrentframe()
        assert isinstance(obj, QLabel)
        return obj

    def uiProgressBar(self):
        obj = self.uiProgressBar_
        assert isinstance(obj, QProgressBar)
        return obj

    def pickClassColor(self):
        w = self.sender()
        color = QColorDialog.getColor()
        if color.name() != '#000000':
            w.setStyleSheet('background-color: {}'.format(color.name()))

    def onRasterizationOptionsChanged(self, *args):
        self.uiAttribute_.setCurrentIndex(-1)
        self.clearStrata()
        self.initStrata()

    def onRasterLayerChanged(self, *args):
        self.uiRegression_.setLayer(None)
        self.uiRegression_.setEnabled(self.uiRaster_.currentLayer() is not None)
        self.uiAttribute_.hide()
        self.uiAttributeLabel_.hide()
        self.uiAttribute_.setCurrentIndex(-1)
        self.clearStrata()
        self.initStrata()

    def onRegressionLayerChanged(self, *args):
        layer = self.uiRegression_.currentLayer()
        isVector = isinstance(layer, QgsVectorLayer)

        if isVector:
            try:
                openVectorDataset(filename=layer.source())
            except Exception as error:
                self.log('GDAL Error:{}'.format(str(error)))
                self.uiAttribute_.setCurrentIndex(-1)
                self.uiRegression_.setLayer(None)
                return

        self.uiAttribute_.setEnabled(isVector)
        self.uiAttribute_.setVisible(isVector)
        self.uiAttributeLabel().setVisible(isVector)

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

    def rasterizationFilename(self):
        return '/vsimem/regression_workflow/rasterizedRegression.bsq'

    def strataFilename(self):
        return '/vsimem/regression_workflow/strataClassification.bsq'

    def clearStrata(self):
        self.uiStrataMin_.setText('')
        self.uiStrataMax_.setText('')
        self.uiStrata_.setValue(1)

    def initStrata(self, *args):

        self.log('')
        self.spinboxes = None
        self.uiStacked_.setEnabled(False)
        self.widget_.hide()
        self.widget_ = QWidget()
        self.layout_.addWidget(self.widget_)
        layout = QHBoxLayout(self.widget_)
        self.updateTotalSamples()

        layer = self.uiRegression_.currentLayer()
        if layer is None:
            return
        elif isinstance(layer, QgsVectorLayer):
            self.uiAttribute_.setEnabled(True)
            name = self.uiAttribute_.currentField()
            if name == '':  # no field selected yet
                return

            filename = layer.source()
            ds = openVectorDataset(filename=filename)

            if ds.ogrDataSource().GetDriver().LongName == 'GeoPackage' and name == 'fid':
                self.log('Using GeoPackage fid as class attribute is not supported.')
                self.uiAttribute_.setCurrentIndex(-1)
                return

            vectorRegression = VectorRegression(filename=filename, regressionAttribute=name)
            raster = Raster(filename=self.uiRaster_.currentLayer().source())
            self.log('Rasterize reference on raster grid')
            regression = Regression.fromVectorRegression(filename=self.rasterizationFilename(),
                vectorRegression=vectorRegression, grid=raster.grid(),
                **ApplierOptions(emitFileCreated=False, progressBar=self.progressBar()))
            self.log('')
            self.progressBar().setPercentage(0)

        elif isinstance(layer, QgsRasterLayer):
            self.uiAttribute_.setEnabled(False)
            filename = layer.source()
            try:
                regression = Regression(filename=filename)
            except:
                self.log('Selected layer is not a valid regression.')
                self.uiRegression_.setLayer(None)
                return
        else:
            assert 0

        # calculate strata stats
        try:
            vrange = float(self.uiStrataMin_.text()), float(self.uiStrataMax_.text())
        except ValueError:
            vrange = None
        vbins = self.uiStrata_.value()
        histo = regression.statistics(
            bandIndices=[0], calcHistogram=True, histogramRanges=[vrange], histogramBins=[vbins]
        )[0].histo
        self.counts = histo.hist
        self.uiStrataMin_.setText(str(round(histo.bin_edges[0], 2)))
        self.uiStrataMax_.setText(str(round(histo.bin_edges[-1], 2)))

        self.spinboxes = list()
        self.colors = list()
        self.names = list()
        self.bin_edges = histo.bin_edges

        for i, count in enumerate(self.counts):
            layout1 = QVBoxLayout()
            layout2 = QHBoxLayout()
            layout2.addWidget(
                QLabel(f'Stratum {i + 1}: [{round(histo.bin_edges[i], 2)}, {round(histo.bin_edges[i + 1], 2)}]')
            )
            layout1.addLayout(layout2)
            spinbox = QSpinBox()
            spinbox.setRange(0, count)
            spinbox.setSingleStep(1)
            spinbox.setValue(count)
            spinbox.setSuffix(' ({} px)'.format(count))
            spinbox.valueChanged.connect(self.updateTotalSamples)
            self.spinboxes.append(spinbox)
            layout1.addWidget(spinbox)
            layout.addLayout(layout1)
            self.updateTotalSamples()

        self.uiStacked_.setEnabled(True)

    def updateTotalSamples(self, *args):
        total = 0
        if self.spinboxes is not None:
            for spinbox in self.spinboxes:
                total += int(spinbox.value())
        self.uiTotalSampleSize_.setText('Total sample size = {}'.format(total))

    def initMaps(self):
        assert isinstance(self.uiAttribute_, QgsFieldComboBox)
        self.uiRaster_.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.uiRaster2_.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.uiRegression_.layerChanged.connect(self.initStrata)
        self.uiRegression_.layerChanged.connect(self.clearStrata)
        self.uiAttribute_.setFilters(
            QgsFieldProxyModel.Numeric)  # All, Date, Double, Int, LongLong, Numeric, String, Time

    def initClassifier(self):
        from _classic.enmapboxgeoalgorithms.algorithms import ALGORITHMS, RegressorFit
        self.classifiers = [alg for alg in ALGORITHMS if isinstance(alg, RegressorFit)]
        self.classifierNames = [alg.name()[3:] for alg in self.classifiers]
        self.uiClassifier_.addItems(self.classifierNames)
        self.uiClassifier_.currentIndexChanged.connect(
            lambda index: self.uiCode_.setText(self.classifiers[index].code()))
        self.uiClassifier_.setCurrentIndex(self.classifierNames.index('RandomForestRegressor'))

    def initOutputs(self):
        outdir = tempfile.gettempdir()
        self.uiSampledRegressionFilename_.setStorageMode(QgsFileWidget.SaveFile)
        #        self.uiSampledRegressionComplementFilename_.setStorageMode(QgsFileWidget.SaveFile)
        self.uiModelFilename_.setStorageMode(QgsFileWidget.SaveFile)
        self.uiRegressionFilename_.setStorageMode(QgsFileWidget.SaveFile)
        self.uiReportFilename_.setStorageMode(QgsFileWidget.SaveFile)

        self.uiSampledRegressionFilename_.setFilePath(join(outdir, 'sample.bsq'))
        #        self.uiSampledRegressionComplementFilename_.setFilePath(join(outdir, 'complement.bsq'))
        self.uiModelFilename_.setFilePath(join(outdir, 'classifier.pkl'))
        self.uiRegressionFilename_.setFilePath(join(outdir, 'regression.bsq'))
        self.uiReportFilename_.setFilePath(join(outdir, 'accass.html'))

    def execute(self, *args):
        self.log('')

        try:
            saveSampledRegression = self.uiSampledRegressionFilename_.isEnabled()
            saveSampledRegressionComplement = saveSampledRegression  # self.uiSampledRegressionComplementFilename_.isEnabled()
            saveModel = self.uiModelFilename_.isEnabled()
            saveRegression = self.uiRegressionFilename_.isEnabled()
            saveReport = self.uiReportFilename_.isEnabled()
            filenameSampledRegression = self.uiSampledRegressionFilename_.filePath()
            filenameSampledRegressionComplement = '{}_complement{}'.format(
                *splitext(filenameSampledRegression))
            filenameModel = self.uiModelFilename_.filePath()
            filenameRegression = self.uiRegressionFilename_.filePath()
            filenameReport = self.uiReportFilename_.filePath()

            qgsRaster = self.uiRaster_.currentLayer()
            if qgsRaster is None:
                self.log('Error: no raster selected')
                return
            raster = Raster(filename=qgsRaster.source())

            qgsRegression = self.uiRegression_.currentLayer()
            if qgsRegression is None:
                self.log('Error: no reference selected')
                return

            colors = list()
            for w in self.colors:
                hex = w.styleSheet().split(' ')[1]
                colors.append(Color(hex))

            names = list()
            for w in self.names:
                names.append(w.text())

            if isinstance(qgsRegression, QgsRasterLayer):
                regression = Regression(filename=qgsRegression.source())
                if not raster.grid().equal(other=regression.grid()):
                    self.log('Error: raster and reference grids do not match')
                    return
            elif isinstance(qgsRegression, QgsVectorLayer):
                regression = Regression(filename=self.rasterizationFilename())
            else:
                assert 0

            sample = RegressionSample(raster=raster, regression=regression)

            qgsRaster2 = self.uiRaster2_.currentLayer()
            if saveRegression and qgsRaster2 is None:
                self.log('Error: no raster for mapping selected')
                return
            raster2 = Raster(filename=qgsRaster2.source())

            n = [spinbox.value() for spinbox in self.spinboxes]
            if np.sum(n) == np.sum(self.counts):  # perform no random sampling if all samples are used
                n = None

            if n is not None:
                bin_edges = self.bin_edges

                def doit(array, bin_edges):
                    result = np.zeros_like(array, dtype=np.uint8)
                    for i, v0 in enumerate(bin_edges[:-1], 1):
                        result[array >= v0] = i
                    result[array > bin_edges[-1]] = 0
                    return result

                kwds = dict(bin_edges=bin_edges)
                tmp = regression.applySpatial(filename=self.strataFilename(), function=doit, kwds=kwds)
                del tmp
                strata = Classification(self.strataFilename(), classDefinition=ClassDefinition(classes=len(n)))
            else:
                strata = None

            cv = self.uiNFold_.value()

            namespace = dict()
            code = self.uiCode_.toPlainText()
            exec(code, namespace)
            sklEstimator = namespace['estimator']
            regressor = Regressor(sklEstimator=sklEstimator)

            self.uiExecute_.setEnabled(False)

            regressionWorkflow(sample=sample,
                regressor=regressor,
                raster=raster2,
                strata=strata,
                n=n,
                cv=cv,
                saveSampledRegression=saveSampledRegression,
                saveSampledRegressionComplement=saveSampledRegressionComplement,
                saveModel=saveModel,
                saveRegression=saveRegression,
                saveReport=saveReport,
                filenameSampledRegression=filenameSampledRegression,
                filenameSampledRegressionComplement=filenameSampledRegressionComplement,
                filenameModel=filenameModel,
                filenameRegression=filenameRegression,
                filenameReport=filenameReport,
                ui=self)
            self.log('Done!')
            self.uiAttributeLabel()
            self.progressBar().setPercentage(0)
            self.uiExecute_.setEnabled(True)


        except Exception as error:
            traceback.print_exc()
            self.log('Error: {}'.format(str(error)))
            self.uiExecute_.setEnabled(True)
