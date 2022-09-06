from os.path import join, dirname, basename, splitext, exists, isabs, abspath
from os import remove
import tempfile

from PyQt5.uic import loadUi
from osgeo import gdal
import numpy
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from PyQt5.Qsci import *
# from qgis.PyQt.QtWebKitWidgets import QWebView
# from qgis.PyQt.QtWebKit import QWebSettings
# from qgis.PyQt.QtWebEngineWidgets import QWebEngineView as QWebView

from .calculator import (Calulator, CodeExecutionError, ApplierInputRaster, ApplierInputVector, ApplierOutputRaster,
                         ApplierOptions, ApplierControls)
import _classic.hubdc.core
import _classic.hubdc.progressbar
import _classic.hubdc.hubdcerrors

pathUi = join(dirname(__file__), 'ui')


class InvalidIdentifierError(Exception):
    pass


class InvalidFloatError(Exception):
    pass


class InvalidOutputPathError(Exception):
    pass


class ValidatedQLineEdit(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.styleInvalid = 'QLineEdit {\n     border: 2px solid gray;\n     padding: 0 8px;\n     background: yellow;\n     selection-background-color: darkgray;\n }\n'
        self.textChanged.connect(self.onTextChanged)

    def value(self):
        if self.valid():
            return self.text()
        else:
            raise self.error()

    def error(self):
        return Exception()

    def valid(self):
        return True

    def onTextChanged(self, text):
        if self.valid():
            self.setStyleSheet(None)
            self.setToolTip(None)
        else:
            self.setStyleSheet(self.styleInvalid)
            self.setToolTip('Invalid {}'.format(self.__class__.__name__))


class Identifier(ValidatedQLineEdit):

    def error(self):
        return InvalidIdentifierError(self.text())

    def valid(self):

        text = self.text()
        if len(text) == 0:
            return False

        import string
        letters = string.ascii_letters + '_'
        digits = '0123456789'

        for i, c in enumerate(text):
            if i == 0:
                if c in letters:
                    continue
            else:
                if c in letters + digits:
                    continue
            return False
        return True


class Float(ValidatedQLineEdit):

    def error(self):
        return InvalidFloatError(self.text())

    def valid(self):
        try:
            float(self.text())
            return True
        except:
            return False


class Input(QWidget):
    sigLayerChanged = pyqtSignal(QgsMapLayer)
    sigNameChanged = pyqtSignal(str)
    sigImportArray = pyqtSignal()
    sigImportMetadata = pyqtSignal()
    sigImportNoDataValue = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(join(pathUi, 'input.ui'), self)
        # self.setupUi(self)
        self.nameByLayer = True

        self.uiImportArray.hide()

        # init layer
        assert isinstance(self.uiLayer, QgsMapLayerComboBox)
        self.uiLayer.setCurrentIndex(0)
        self.uiLayer.layerChanged.connect(self.sigLayerChanged)

        # init name
        assert isinstance(self.uiName, Identifier)
        self.uiName.textEdited.connect(self.turnNameByLayerOff)

        # init resampling algorithms combobox
        assert isinstance(self.uiResampleAlg, QComboBox)
        from osgeo import gdal
        resampleAlgs = [s.split('_')[1] for s in dir(gdal) if s.startswith('GRA_')]
        self.resampleAlgs = resampleAlgs
        self.uiResampleAlg.addItems(resampleAlgs)
        self.uiResampleAlg.setCurrentIndex(resampleAlgs.index('NearestNeighbour'))

        self.uiBurnAttribute.setFilters(QgsFieldProxyModel.Numeric)  # All, Date, Double, Int, LongLong, Numeric

        # connect signals to slots
        self.sigLayerChanged.connect(self.setNameByLayer)
        self.sigLayerChanged.connect(self.showOptions)
        self.uiImportArray.clicked.connect(self.sigImportArray)
        #        self.uiImportArray2.clicked.connect(self.sigImportArray)
        #        self.uiImportMetadata.clicked.connect(self.sigImportMetadata)
        #        self.uiImportNoDataValue.clicked.connect(self.sigImportNoDataValue)

        self.showOptions(layer=self.layer())

    def setNameByLayer(self, layer):

        if layer is None:
            self.uiName.setText('')
            return

        import string
        letters = string.ascii_letters + '_'
        digits = '0123456789'

        if self.nameByLayer:
            name = splitext(basename(layer.source()))[0]
            identifier = list(name)
            for i, c in enumerate(name):
                if i == 0:
                    if c in letters:
                        continue
                else:
                    if c in letters + digits:
                        continue
                identifier[i] = '_'
            identifier = ''.join(identifier)
            self.uiName.setText(identifier)

    def showOptions(self, layer=None):
        if layer is None:
            self.uiOptions1.hide()
            self.uiOptions2.hide()
        elif isinstance(layer, QgsRasterLayer):
            self.uiOptions1.show()
            self.uiOptions2.hide()
        elif isinstance(layer, QgsVectorLayer):
            self.uiOptions1.hide()
            self.uiOptions2.show()

    def turnNameByLayerOff(self):
        self.nameByLayer = False

    def name(self):
        return self.uiName.value()

    def layer(self):
        return self.uiLayer.currentLayer()

    def setValue(self, name=None, layer=None):
        if layer is not None:
            self.setLayer(layer)
        if name is not None:
            self.setName(name)

    def value(self):
        value = dict()
        value['name'] = self.name()
        value['layer'] = self.layer()
        if isinstance(value['layer'], QgsRasterLayer):
            value['resampleAlg'] = eval('gdal.GRA_' + self.uiResampleAlg.currentText())
        elif isinstance(value['layer'], QgsVectorLayer):
            value['initValue'] = 0.
            value['burnValue'] = 1.
            value['burnAttribute'] = self.uiBurnAttribute.currentField()
            if value['burnAttribute'] == '':
                value['burnAttribute'] = None
            value['allTouched'] = self.uiAllTouched.isChecked()
        elif value['layer'] is None:
            return None
        else:
            assert 0

        return value

    def setLayer(self, layer):
        assert isinstance(layer, QgsMapLayer)
        filename = layer.source()
        index = None
        for i in range(self.uiLayer.count()):
            layer = self.uiLayer.layer(i)
            if layer is not None:
                if layer.source() == filename:
                    index = i
                    break

        if index is None:
            raise Exception('layer not found')
            # QgsProject.instance().addMapLayer(layer)
            # self.uiLayer.setCurrentIndex(i)

        self.uiLayer.setLayer(layer)

    def setName(self, name):
        self.uiName.setText(name)


class OutputFilename(QgsFileWidget):
    def __init__(self, parent=None):
        self._defaultRoot = join(tempfile.gettempdir(), 'imageMath')
        super().__init__(parent)
        self.setStorageMode(QgsFileWidget.SaveFile)

    def value(self, default):
        filename = self.filePath()

        if filename.startswith('/vsimem/'):
            pass
        else:
            if isabs(filename):
                pass
            elif isabs(join(self._defaultRoot, filename)):
                filename = join(self._defaultRoot, filename)
            else:
                raise InvalidOutputPathError(filename)
            filename = abspath(filename)  # deals with '..' inside the path

        if filename == self._defaultRoot:
            filename = default
            self.setFilePath(default)

        return filename


class Output(QWidget):
    sigFilenameChanged = pyqtSignal(str)
    sigNameChanged = pyqtSignal(str)
    sigSetArray = pyqtSignal()
    sigSetMetadata = pyqtSignal()
    sigSetNoDataValue = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(join(pathUi, 'output.ui'), self)
        # self.setupUi(self)

        self.uiSetArray.hide()

        # setup name
        self.uiName().textEdited.connect(self.turnNameByFilenameOff)

        # setup file
        self.uiFilename().fileChanged.connect(self.sigFilenameChanged)
        self.uiFilename().fileChanged.connect(self.sigNameChanged)

        self.nameByFilename = True

        self.sigFilenameChanged.connect(self.setNameByFilename)

        self.uiSetArray.clicked.connect(self.sigSetArray)
        # self.uiSetMetadata.clicked.connect(self.sigSetMetadata)
        # self.uiSetNoDataValue.clicked.connect(self.sigSetNoDataValue)

    def uiFilename(self):
        assert isinstance(self.uiFilename_, OutputFilename)
        return self.uiFilename_

    def uiName(self):
        assert isinstance(self.uiName_, Identifier)
        return self.uiName_

    def name(self):
        return self.uiName().value()

    def filename(self):
        return self.uiFilename().value(default='/vsimem/{}.bsq'.format(self.name()))

    def value(self):
        value = dict()
        value['name'] = self.name()
        value['filename'] = self.filename()
        return value

    def setValue(self, name=None, filename=None):
        if name is not None:
            self.setName(name)
        if filename is not None:
            self.setFilename(filename)

    def setName(self, name):
        self.uiName().setText(name)

    def setFilename(self, filename):
        self.uiFilename().setFilePath(filename)

    def setNameByFilename(self, filename):
        import string
        letters = string.ascii_letters + '_'
        digits = '0123456789'

        if self.nameByFilename:
            name = splitext(basename(filename))[0]
            identifier = list(name)
            for i, c in enumerate(name):
                if i == 0:
                    if c in letters:
                        continue
                else:
                    if c in letters + digits:
                        continue
                identifier[i] = '_'
            identifier = ''.join(identifier)
            self.uiName().setText(identifier)

    def turnNameByFilenameOff(self):
        self.nameByFilename = False


class RemovableItem(QWidget):
    sigCreated = pyqtSignal()
    sigRemoved = pyqtSignal()
    sigImportArray = pyqtSignal()
    sigImportMetadata = pyqtSignal()
    sigImportNoDataValue = pyqtSignal()
    sigSetArray = pyqtSignal()
    sigSetMetadata = pyqtSignal()
    sigSetNoDataValue = pyqtSignal()

    def __init__(self, type, parent=None):
        super().__init__(parent)
        loadUi(join(pathUi, 'removableItem.ui'), self)
        # self.setupUi(self)
        self.type = type
        self.uiItem = None
        self.uiSpacer = self.uiLayout.itemAt(self.uiLayout.count() - 1)
        self.uiCreate.clicked.connect(self.createItem)
        self.uiRemove.clicked.connect(self.removeItem)
        self.uiRemove.hide()

    def createItem(self):
        self.uiItem = self.type()
        if isinstance(self.uiItem, Input):
            self.uiItem.sigImportArray.connect(self.sigImportArray)
            self.uiItem.sigImportMetadata.connect(self.sigImportMetadata)
            self.uiItem.sigImportNoDataValue.connect(self.sigImportNoDataValue)
        elif isinstance(self.uiItem, Output):
            self.uiItem.sigSetArray.connect(self.sigSetArray)
            self.uiItem.sigSetMetadata.connect(self.sigSetMetadata)
            self.uiItem.sigSetNoDataValue.connect(self.sigSetNoDataValue)
        else:
            assert 0

        self.uiLayout.insertWidget(2, self.uiItem)
        self.uiCreate.hide()
        self.uiRemove.show()
        self.uiLayout.removeItem(self.uiSpacer)

        self.sigCreated.emit()

    def removeItem(self):
        self.uiItem.setParent(None)
        self.uiItem.destroy()
        self.uiItem = None
        self.uiCreate.show()
        self.uiRemove.hide()
        self.uiLayout.addItem(self.uiSpacer)
        self.sigRemoved.emit()

    def setValue(self, **kwargs):
        self.uiItem.setValue(**kwargs)

    def value(self):
        if self.uiItem is not None:
            return self.uiItem.value()
        else:
            return None


class ItemList(QWidget):
    TYPE = None
    sigImportArray = None
    sigImportMetadata = None
    sigImportNoDataValue = None
    sigSetArray = None
    sigSetMetadata = None
    sigSetNoDataValue = None

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(join(pathUi, 'itemList.ui'), self)
        # self.setupUi(self)
        assert self.TYPE is not None
        self.addItem()

    def addItem(self, index=None):
        item = RemovableItem(type=self.TYPE)
        self._lastItem = item
        item.sigCreated.connect(self.addItem)
        item.sigRemoved.connect(self.removeItem)
        if isinstance(self, InputList):
            item.sigImportArray.connect(self.sigImportArray)
            item.sigImportMetadata.connect(self.sigImportMetadata)
            item.sigImportNoDataValue.connect(self.sigImportNoDataValue)
        elif isinstance(self, OutputList):
            item.sigSetArray.connect(self.sigSetArray)
            item.sigSetMetadata.connect(self.sigSetMetadata)
            item.sigSetNoDataValue.connect(self.sigSetNoDataValue)
        else:
            assert 0
        if index is None:
            index = self.uiLayout.count() - 1
        self.uiLayout.insertWidget(index, item)

    def removeItem(self):
        item = self.sender()
        item.setParent(None)
        item.deleteLater()

    def lastItem(self):
        return self._lastItem

    def values(self):
        values = list()
        for index in range(self.uiLayout.count()):
            item = self.uiLayout.itemAt(index).widget()
            if item is None:
                continue
            value = item.value()
            if value is None:
                continue
            values.append(value)
        return values


class InputList(ItemList):
    TYPE = Input
    sigImportArray = pyqtSignal()
    sigImportMetadata = pyqtSignal()
    sigImportNoDataValue = pyqtSignal()


class OutputList(ItemList):
    TYPE = Output
    sigSetArray = pyqtSignal()
    sigSetMetadata = pyqtSignal()
    sigSetNoDataValue = pyqtSignal()


class Projection(QgsProjectionSelectionWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setNotSetText('automatic')  # .setLayerCrs(crs=enmap.crs())
        self.setOptionVisible(QgsProjectionSelectionWidget.CrsNotSet, True)
        self.setOptionVisible(QgsProjectionSelectionWidget.LayerCrs, True)
        self.setOptionVisible(QgsProjectionSelectionWidget.ProjectCrs, False)
        self.setOptionVisible(QgsProjectionSelectionWidget.CurrentCrs, False)
        self.setOptionVisible(QgsProjectionSelectionWidget.DefaultCrs, False)
        self.setOptionVisible(QgsProjectionSelectionWidget.RecentCrs, False)

    def setValue(self, projection=None):
        if projection is None:
            pass
        else:
            assert isinstance(projection, _classic.hubdc.core.Projection)
            crs = QgsCoordinateReferenceSystem.fromWkt(projection.wkt())
            self.setCrs(crs)

    def value(self):
        wkt = self.crs().toWkt()
        if wkt == '':
            projection = None
        else:
            projection = _classic.hubdc.core.Projection(wkt=wkt)
        return projection


class Extent(QWidget):
    INTERSECTION = 'intersection'
    UNION = 'union'
    USER = 'user'
    MODE_OPTIONS = [INTERSECTION, UNION, USER]

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(join(pathUi, 'extent.ui'), self)
        # self.setupUi(self)

        self.uiMode.currentIndexChanged.connect(self.onCurrentIndexChanged)
        self.uiMode.currentIndexChanged.emit(0)

        # self.uiUserInput.hide()

    def onCurrentIndexChanged(self, index):
        if self.uiMode.count() - 1 == index:
            self.uiUserInput.show()
        else:
            self.uiUserInput.hide()

    def mode(self):
        return self.MODE_OPTIONS[self.uiMode.currentIndex()]

    def setMode(self, mode):
        assert mode in self.MODE_OPTIONS
        index = self.MODE_OPTIONS.index(mode)
        self.uiMode.setCurrentIndex(index)

    def value(self, projection):
        mode = self.mode()
        if mode == self.USER:
            extent = _classic.hubdc.core.Extent(
                xmin=float(self.uiXmin.text()),
                xmax=float(self.uiXmax.text()),
                ymin=float(self.uiYmin.text()),
                ymax=float(self.uiYmax.text()),
                projection=projection
                                       )
        else:
            extent = None
        return mode, extent

    def setValue(self, mode, extent=None):

        if isinstance(extent, _classic.hubdc.core.Extent):
            self.uiXmin.setText(str(extent.xmin()))
            self.uiXmax.setText(str(extent.xmax()))
            self.uiYmin.setText(str(extent.ymin()))
            self.uiYmax.setText(str(extent.ymax()))

        self.setMode(mode=mode)


class Resolution(QWidget):
    COARSEST = 'coarsest'
    FINEST = 'finest'
    USER = 'user'
    MODE_OPTIONS = [COARSEST, FINEST, USER]

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(join(pathUi, 'resolution.ui'), self)
        # self.setupUi(self)
        self.uiMode.currentIndexChanged.connect(self.onCurrentIndexChanged)
        self.uiMode.currentIndexChanged.emit(0)

    def onCurrentIndexChanged(self, index):
        if self.uiMode.count() - 1 == index:
            self.uiUserInput.show()
        else:
            self.uiUserInput.hide()

    def mode(self):
        return self.MODE_OPTIONS[self.uiMode.currentIndex()]

    def setMode(self, mode):
        index = self.MODE_OPTIONS.index(mode)
        self.uiMode.setCurrentIndex(index)

    def value(self):
        mode = self.mode()
        if mode == self.USER:
            resolution = _classic.hubdc.core.Resolution(x=float(self.uiResolution.text()),
                y=float(self.uiResolution.text()))
        else:
            resolution = None
        return mode, resolution

    def setValue(self, mode, resolution=None):
        assert mode in self.MODE_OPTIONS
        if mode == self.USER:
            if resolution is None:
                self.uiResolution.setText('')
            else:
                assert isinstance(resolution, _classic.hubdc.core.Resolution)
                self.uiResolution.setText(str(resolution.x()))
        self.setMode(mode=mode)


class Grid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(join(pathUi, 'grid.ui'), self)
        # self.setupUi(self)

        self.uiLayer().setCurrentIndex(0)
        self.uiLayer().layerChanged.connect(self.setValueByLayer)

    def uiProjection(self):
        assert isinstance(self.uiProjection_, Projection)
        return self.uiProjection_

    def uiExtent(self):
        assert isinstance(self.uiExtent_, Extent)
        return self.uiExtent_

    def uiResolution(self):
        assert isinstance(self.uiResolution_, Resolution)
        return self.uiResolution_

    def uiLayer(self):
        assert isinstance(self.uiLayer_, QgsMapLayerComboBox)
        return self.uiLayer_

    #    def setValue(self, mode, extent=None):
    #        self.uiExtent().setValue(mode=mode, extent=extent)

    def setValueByLayer(self, layer):
        if layer is None:
            return
        elif isinstance(layer, QgsRasterLayer):
            xy = layer.rasterUnitsPerPixelX()
            resolution = _classic.hubdc.core.Resolution(x=xy, y=xy)
        elif isinstance(layer, QgsVectorLayer):
            resolution = None
        else:
            assert 0

        projection = _classic.hubdc.core.Projection(wkt=layer.crs().toWkt())
        qgsExtent = layer.extent()
        extent = _classic.hubdc.core.Extent(
            xmin=qgsExtent.xMinimum(),
            xmax=qgsExtent.xMaximum(),
            ymin=qgsExtent.yMinimum(),
            ymax=qgsExtent.yMaximum(),
            projection=projection
        )

        self.uiProjection().setValue(projection=projection)
        self.uiExtent().setValue(mode=Extent.USER, extent=extent)
        self.uiResolution().setValue(mode=Resolution.USER, resolution=resolution)

        self.uiLayer().setCurrentIndex(0)

    def value(self):
        projection = self.uiProjection().value()
        extent = self.uiExtent().value(projection)
        resolution = self.uiResolution().value()
        return projection, extent, resolution


class CodeEdit(QsciScintilla):
    def __init__(self, parent=None):
        QsciScintilla.__init__(self, parent)
        self.setLexer(QsciLexerPython(self))

        # Set the default font
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        # font.setPointSize(10)
        font.setPixelSize(8)

        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#e3e3e3"))

    def replaceSelectedTextAndFocus(self, text):
        self.replaceSelectedText(text)
        self.setFocus()


class ProgressBar(_classic.hubdc.progressbar.CUIProgressBar):

    def __init__(self, log, bar):
        assert isinstance(log, WebLog)
        assert isinstance(bar, QProgressBar)
        self.log = log
        self.bar = bar
        self.bar.setMinimum(0)
        self.bar.setMaximum(100)

    def setText(self, text):
        self.log.appendText(str(text))

    def setPercentage(self, percentage):
        self.bar.setValue(int(percentage))


class WebLog(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentText = ''
        self.setOpenExternalLinks(True)

    #        self.settings().setFontFamily(QWebSettings.FixedFont)

    def setText(self, text):
        html = '<font face="Arial">{}</font>'.format(text.replace('\n', '<br>'))
        self.setHtml(html)
        self._currentText = text

    def appendText(self, text):
        newText = self._currentText + '\n' + text
        self.setText(text=newText)


class Routines(QTreeWidget):
    sigHTMLSelected = pyqtSignal(str)
    sigURLSelected = pyqtSignal(QUrl)
    sigRoutineDoubleClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        from enmapboxapplications.imagemathapp.routines2 import routinesDictionary, createTree
        d = routinesDictionary()
        createTree(d, self)

        #        self.uiFunctions.selectionModel().selectionChanged.connect(self.handleFunctionSelection)
        #        self.uiFunctions.itemDoubleClicked.connect(self.handleFunctionDoubleClicked)
        self.selectionModel().selectionChanged.connect(self.handleFunctionSelection)
        self.itemDoubleClicked.connect(self.handleFunctionDoubleClicked)

    def handleFunctionSelection(self, selected, deselected):
        from enmapboxapplications.imagemathapp.routines2 import NumpyItem, WebItem
        for index in selected.indexes():
            item = self.itemFromIndex(index)
            if isinstance(item, NumpyItem):
                html = r'<pre><code>' + item.doc + '</code></pre>'.replace('\n', '<br>')
                self.sigHTMLSelected.emit(html)
            elif isinstance(item, WebItem):
                self.sigURLSelected.emit(QUrl(item.url))
            else:
                self.sigHTMLSelected.emit('')

    def handleFunctionDoubleClicked(self, item, column):
        from enmapboxapplications.imagemathapp.routines2 import NumpyItem, WebItem
        if isinstance(item, NumpyItem):
            text = item.doubleClickInsert
            self.sigRoutineDoubleClicked.emit(text)


class ImageMathApp(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        loadUi(join(pathUi, 'main.ui'), self)
        # self.setupUi(self)
        self.uiExecute().clicked.connect(self.execute)

        # assert isinstance(self.uiLog2_,  QWebView)
        self.uiLog().setText('')

        self.uiRoutines().sigHTMLSelected.connect(self.uiLog().setHtml)
        self.uiRoutines().sigURLSelected.connect(lambda qUrl: self.uiLog().setHtml(qUrl.url()))
        self.uiRoutines().sigRoutineDoubleClicked.connect(self.uiCode().replaceSelectedTextAndFocus)

    def uiInputs(self):
        assert isinstance(self.uiInputs_, InputList)
        return self.uiInputs_

    def uiOutputs(self):
        assert isinstance(self.uiOutputs_, OutputList)
        return self.uiOutputs_

    def uiExecute(self):
        assert isinstance(self.uiExecute_, QToolButton)
        return self.uiExecute_

    def uiCode(self):
        assert isinstance(self.uiCode_, CodeEdit)
        return self.uiCode_

    def uiLog(self):
        assert isinstance(self.uiLog2_, WebLog)
        return self.uiLog2_

    def uiProgressBar(self):
        assert isinstance(self.uiProgressBar_, QProgressBar)
        return self.uiProgressBar_

    def uiGrid(self):
        assert isinstance(self.uiGrid_, Grid)
        return self.uiGrid_

    def uiRoutines(self):
        assert isinstance(self.uiRoutines_, Routines)
        return self.uiRoutines_

    def addInput(self, name=None, layer=None):
        item = self.uiInputs().lastItem()
        item.createItem()
        item.sigImportArray.connect(self.onImportArray)
        item.sigImportMetadata.connect(self.onImportMetadata)
        item.sigImportNoDataValue.connect(self.onImportNoDataValue)
        item.setValue(name=name, layer=layer)

    def addOutput(self, name=None, filename=None):
        item = self.uiOutputs().lastItem()
        item.createItem()
        item.sigSetArray.connect(self.onSetArray)
        item.sigSetMetadata.connect(self.onSetMetadata)
        item.sigSetNoDataValue.connect(self.onSetNoDataValue)
        item.setValue(name=name, filename=filename)

    def code(self):
        return self.uiCode().text()

    def setCode(self, code):
        self.uiCode().setText(code)

    def execute(self):

        def redHTML(text):
            return '<p style="color:red;">{}</p>'.format(text).replace('\n', '<br>')

        self.uiLog().setText('')
        try:

            try:
                inputs = self.uiInputs().values()
                outputs = self.uiOutputs().values()
                projection, (extentMode, extent), (resolutionMode, resolution) = self.uiGrid().value()
            except InvalidIdentifierError as error:
                self.uiLog().setText(redHTML('invalid identifier: "{}"'.format(str(error))))
                return
            except InvalidFloatError as error:
                self.uiLog().setText(redHTML('invalid floating point number: "{}"'.format(str(error))))
                return
            except InvalidOutputPathError as error:
                self.uiLog().setText(redHTML('invalid output path: "{}"'.format(str(error))))
                return

            code = self.code()

            controls = ApplierControls()
            controls.setBlockSize(blockSize=self.uiBlockSize.value())

            calculator = Calulator(controls=controls)
            calculator.controls.setProgressBar(progressBar=ProgressBar(log=self.uiLog(), bar=self.uiProgressBar()))

            calculator.controls.setProjection(projection=projection)

            if extentMode == Extent.USER:
                calculator.controls.setExtent(extent)
            elif extentMode == Extent.UNION:
                calculator.controls.setAutoExtent(ApplierOptions.AutoExtent.union)
            elif extentMode == Extent.INTERSECTION:
                calculator.controls.setAutoExtent(ApplierOptions.AutoExtent.union)
            else:
                assert 0

            if resolutionMode == Resolution.USER:
                calculator.controls.setResolution(resolution)
            elif resolutionMode == Resolution.COARSEST:
                calculator.controls.setAutoResolution(ApplierOptions.AutoResolution.maximum)
            elif resolutionMode == Resolution.FINEST:
                calculator.controls.setAutoResolution(ApplierOptions.AutoResolution.minimum)
            else:
                assert 0

            options = dict()
            inputKeys = list()
            for item in inputs:
                key = item['name']
                layer = item['layer']
                filename = layer.source()
                inputKeys.append(key)
                options[key] = dict()
                if isinstance(layer, QgsRasterLayer):
                    calculator.inputRaster.setRaster(key=key, value=ApplierInputRaster(filename=filename))
                    options[key]['resampleAlg'] = item['resampleAlg']
                elif isinstance(layer, QgsVectorLayer):
                    calculator.inputVector.setVector(key=key, value=ApplierInputVector(filename=filename))
                    options[key]['initValue'] = item['initValue']
                    options[key]['burnValue'] = item['burnValue']
                    options[key]['burnAttribute'] = item['burnAttribute']
                    options[key]['allTouched'] = item['allTouched']
                    options[key]['filterSQL'] = None
                    options[key]['dtype'] = numpy.float32
                else:
                    assert 0

            outputKeys = list()
            for item in outputs:
                calculator.outputRaster.setRaster(key=item['name'],
                    value=ApplierOutputRaster(filename=item['filename']))
                outputKeys.append(item['name'])

            keys = numpy.array(inputKeys + outputKeys)
            for key in keys:
                if numpy.sum(key == keys) > 1:
                    self.uiLog().setText('duplicated identifier: ' + key)
                    return

            try:
                calculator.applyCode(code=code, options=options, overlap=self.uiBlockOverlap.value(),
                    outputKeys=outputKeys)

            except _classic.hubdc.hubdcerrors.MissingApplierProjectionError:
                self.uiLog().setText(redHTML(
                    'cannot derive coordinate reference system (CRS) from input raster layers; select CRS manually'))
                return

            except _classic.hubdc.hubdcerrors.MissingApplierExtentError:
                self.uiLog().setText(redHTML(
                    'cannot derive extent from input raster layers; select extent manually'))
                return

            except _classic.hubdc.hubdcerrors.MissingApplierResolutionError:
                self.uiLog().setText(redHTML(
                    'cannot derive resolution from input raster layers; select resolution manually'))
                return


            except CodeExecutionError as error:
                # html = '<p style="color:red;">{}</p>'.format(str(error)).replace('\n', '<br>')
                self.uiLog().setText(redHTML(str(error)))

        except:
            import traceback
            traceback.print_exc()
            html = '<p style="color:red;">{}</p>'.format(traceback.format_exc()).replace('\n', '<br>')
            self.uiLog().setText(html)

    def onImportArray(self):
        item = self.sender().uiItem
        assert isinstance(item, Input)
        text = item.name()
        self.uiCode().replaceSelectedTextAndFocus(text)

    def onImportMetadata(self):
        item = self.sender().uiItem
        assert isinstance(item, Input)
        text = 'metadata({})'.format(item.name())
        self.uiCode().replaceSelectedTextAndFocus(text)

    def onImportNoDataValue(self):
        item = self.sender().uiItem
        assert isinstance(item, Input)
        text = 'noDataValue({})'.format(item.name())
        self.uiCode().replaceSelectedTextAndFocus(text)

    def onSetArray(self):
        item = self.sender().uiItem
        assert isinstance(item, Output)
        text = '{} = '.format(item.name())
        self.uiCode().replaceSelectedTextAndFocus(text)

    def onSetMetadata(self):
        item = self.sender().uiItem
        assert isinstance(item, Output)
        text = 'setMetadata({}, metadata=)'.format(item.name())
        self.uiCode().replaceSelectedTextAndFocus(text)

    def onSetNoDataValue(self):
        item = self.sender().uiItem
        assert isinstance(item, Output)
        text = 'setNoDataValue({}, noDataValue=)'.format(item.name())
        self.uiCode().replaceSelectedTextAndFocus(text)
