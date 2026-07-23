import sys, os
from collections import OrderedDict
import tempfile
from osgeo import gdal, osr
from PyQt4 import uic, QtWebKit
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.Qsci import *

import numpy

from _classic.hubdc.model import Open, OpenLayer, Dataset, Layer
from _classic.hubdc.calculator.calculator import *
import _classic.hubdc.const
import _classic.hubdc.progressbar

#gdal.UseExceptions()

class ProgressBar(_classic.hubdc.progressbar.CUIProgressBar):

    def __init__(self, log, bar):
        assert isinstance(log, QTextEdit)
        assert isinstance(bar, QProgressBar)
        self.log = log
        self.bar = bar

    def displayError(self, text):
        self.setLabelText(text)

    def displayInfo(self, text, type=''):
        self.setLabelText(text)

    def setLabelText(self, text):
        self.log.append(str(text))

    def setTotalSteps(self, steps):
        _classic.hubdc.progressbar.CUIProgressBar.setTotalSteps(self, steps)
        self.bar.setMinimum(0)
        self.bar.setMaximum(steps)

    def setProgress(self, progress):
        self.bar.setValue(progress)

class IONode(QTreeWidgetItem):

    def name(self):
        return str(self.text(0))

    def filename(self):
        return str(self.child(0).text(1))

    def input(self):
        pass

class InputRasterNode(IONode):

    def options(self):
        return {'noData' : eval(str(self.child(2).child(0).text(1))),
                'resampleAlg' : eval('gdal.GRA_'+str(self.child(2).child(1).text(1)))}

    def input(self):
        return InputRaster(filename=self.filename())

class InputVectorNode(IONode):

    def layerNameOrIndex(self):
        return int(self.child(1).text(1))

    def input(self):
        return InputVector(filename=self.filename(), layerNameOrIndex=self.layerNameOrIndex())

    def options(self):
        options =  {'initValue' : float(self.child(2).child(0).text(1)),
                    'burnValue': float(self.child(2).child(1).text(1)),
                    'burnAttribute': eval(str(self.child(2).child(2).text(1))),
                    'allTouched': eval('bool('+str(self.child(2).child(3).text(1))+')'),
                    'filterSQL': eval(str(self.child(2).child(4).text(1))),
                    'dtype': eval('numpy.'+str(self.child(2).child(5).text(1)))}
        return options

class OutputRasterNode(IONode):

    def format(self):
        return str(self.child(1).text(1))

    def options(self):
        return eval(str(self.child(2).text(1)))

    def output(self):
        value = OutputRaster(filename=self.filename(), format=self.format(), creationOptions=self.options())
        return value

class NumpyItem(QTreeWidgetItem):

    def __init__(self, name, doc, doubleClickInsert, dragInsert):
        QTreeWidgetItem.__init__(self)
        self.name = name
        self.doc = doc
        self.doubleClickInsert = doubleClickInsert
        self.dragInsert = dragInsert
        self.setText(0, name)

class WebItem(QTreeWidgetItem):

    def __init__(self, name, url):
        QTreeWidgetItem.__init__(self)
        self.name = name
        self.url = url
        self.setText(0, name)


class CodeEdit(QsciScintilla):
    def __init__(self, parent=None):
        QsciScintilla.__init__(self, parent)
        self.setLexer(QsciLexerPython(self))

        # Set the default font
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(10)
#        font.setPixelSize(8)

        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("00000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#e3e3e3"))

class CalculatorMainWindow(QMainWindow):

    def __init__(self, parent=None):

        self.appdir = os.path.dirname(__file__)

        # load ui file
        QMainWindow.__init__(self, parent=parent)
        uic.loadUi(os.path.join(self.appdir, 'main.ui'), self)

        assert isinstance(self.uiCode, QTextEdit)
        self.uiCode = self.uiCode
        # change uiCode from QTextEdit (placeholder in QtDesigner) to QsciScintilla (not available in QtDesigner)
        uiCode = CodeEdit()
        self.uiCode.parent().insertWidget(0, uiCode)
        self.uiCode.hide()
        self.uiCode = uiCode

        assert isinstance(self.uiLog, QTextEdit)
        self.uiLog = self.uiLog
        assert isinstance(self.uiDoc, QtWebKit.QWebView)
        self.uiDoc = self.uiDoc
        assert isinstance(self.uiInputs, QTreeWidget)
        self.uiInputs = self.uiInputs
        assert isinstance(self.uiOutputs, QTreeWidget)
        self.uiOutputs = self.uiOutputs
        assert isinstance(self.uiFunctions, QTreeWidget)
        self.uiFunctions = self.uiFunctions
        assert isinstance(self.uiButtonExecute, QPushButton)
        self.uiButtonExecute = self.uiButtonExecute
        assert isinstance(self.uiProgressBar, QProgressBar)
        self.uiProgressBar = self.uiProgressBar
        self.progressBar = ProgressBar(log=self.uiLog, bar=self.uiProgressBar)

        # set icons
        self.setWindowIcon(QIcon(os.path.join(self.appdir, 'icons', 'numpy.png')))
        self.uiAddInputRaster.setIcon(QIcon(os.path.join(self.appdir, 'icons', 'addRaster.png')))
        self.uiAddInputVector.setIcon(QIcon(os.path.join(self.appdir, 'icons', 'addVector.png')))
        self.uiRemoveInput.setIcon(QIcon(os.path.join(self.appdir, 'icons', 'remove.png')))
        self.uiAddOutputRaster.setIcon(QIcon(os.path.join(self.appdir, 'icons', 'addRaster.png')))
        self.uiRemoveOutput.setIcon(QIcon(os.path.join(self.appdir, 'icons', 'remove.png')))

        # create
        self.createUIRoutines()

        # connect signals
        self.uiAddInputRaster.clicked.connect(self.handleAddInputRaster)
        self.uiAddInputVector.clicked.connect(self.handleAddInputVector)
        self.uiRemoveInput.clicked.connect(self.handleRemoveInput)
        self.uiAddOutputRaster.clicked.connect(self.handleAddOutputRaster)
        self.uiRemoveOutput.clicked.connect(self.handleRemoveOutput)

        self.uiInputs.itemDoubleClicked.connect(self.handleInputsDoubleClicked)
        self.uiOutputs.itemDoubleClicked.connect(self.handleOutputsDoubleClicked)

        #todo drop self.uiInputs.dropEvent.connect(self.handleInputsDropEvent)

        self.uiButtonExecute.clicked.connect(self.handleExecute)
        self.uiFunctions.selectionModel().selectionChanged.connect(self.handleFunctionSelection)
        self.uiFunctions.itemDoubleClicked.connect(self.handleFunctionDoubleClicked)
        self.uiProjectionUser.toggled.connect(self.handleProjectionToggled)
        self.uiProjectionFromSelectedInput.clicked.connect(self.handleProjectionFromSelectedInput)
        self.uiExtentUser.toggled.connect(self.handleExtentToggled)
        self.uiExtentFromSelectedInput.clicked.connect(self.handleExtentFromSelectedInput)
        self.uiResolutionUser.toggled.connect(self.handleResolutionToggled)
        self.uiResolutionFromSelectedInput.clicked.connect(self.handleResolutionFromSelectedInput)

    def createUIRoutines(self):

        def insertRoutine(parent, parentName, routineNames, packageName='numpy'):
            parent[parentName] = list()
            for routineName in routineNames:

                if packageName is not None:
                    fullName = '{}.{}'.format(packageName, routineName)
                else:
                    fullName = routineName

                try:
                    routine = eval(fullName)
                except:
                    print(fullName + ' not available')
                    continue

                doubleClickInsert = fullName.replace('numpy.','') + '('
                dragInsert = routine.__doc__.split('\n')[0] # take first line
                if packageName == 'numpy.ndarray':
                    doubleClickInsert = '.' + doubleClickInsert
                    dragInsert = dragInsert[1:]  # skip the "a" array

                parent[parentName].append(NumpyItem(name=routineName, doc=routine.__doc__,
                                                    doubleClickInsert=doubleClickInsert,
                                                    dragInsert=dragInsert))

        def insertNdarrayAttributes(parent, parentName, attributeNames):
            parent[parentName] = list()
            for attributeName in attributeNames:

                fullName = 'numpy.ndarray.{}'.format(attributeName)
                attribute = eval(fullName)
                parent[parentName].append(NumpyItem(name=attributeName, doc=attribute.__doc__,
                                                    doubleClickInsert='.'+attributeName,
                                                    dragInsert='.'+attributeName))

        d = OrderedDict()
        insertRoutine(d, 'Dataset interaction', 'noDataValue setNoDataValue metadata setMetadata'.split(), packageName=None)

        d['The N-dimensional array (ndarray)'] = OrderedDict()
        insertNdarrayAttributes(d['The N-dimensional array (ndarray)'], 'Array attributes', 'shape ndim size dtype T flat'.split())

        d['The N-dimensional array (ndarray)']['Array methods'] = di = OrderedDict()
        insertRoutine(di, 'Array conversion', 'astype copy view fill'.split(), packageName='numpy.ndarray')
        insertRoutine(di, 'Shape manipulation', 'reshape resize transpose swapaxes flatten ravel'.split(), packageName='numpy.ndarray')
        insertRoutine(di, 'Item selection and manipulation', 'take put repeat choose sort argsort partition argpartition searchsorted nonzero compress diagonal'.split(), packageName='numpy.ndarray')
        insertRoutine(di, 'Calculation', 'argmax min argmin ptp clip conj round trace sum cumsum mean var std prod cumprod all any'.split(), packageName='numpy.ndarray')

        d[r'NumPy routines (numpy)'] = OrderedDict()
        d['NumPy routines (numpy)']['Array creation routines'] = di = OrderedDict()
        insertRoutine(di, 'Ones and zeros', sorted('empty empty_like eye identity ones ones_like zeros zeros_like full full_like'.split()))
        insertRoutine(di, 'From existing data', sorted('array asarray asmatrix copy'.split()))
        insertRoutine(di, 'Numerical ranges', sorted('arange linspace logspace geomspace meshgrid mgrid ogrid'.split()))
        insertRoutine(di, 'Building matrices', sorted('diag diagflat tri tril triu vander mat bmat'.split()))
        d['NumPy routines (numpy)']['Array manipulation routines'] = di = OrderedDict()
        insertRoutine(di, 'Basic operations', 'copyto'.split())
        insertRoutine(di, 'Changing array shape', 'reshape ravel'.split())
        insertRoutine(di, 'Transpose-like operations', 'moveaxis rollaxis swapaxes transpose'.split())
        insertRoutine(di, 'Changing number of dimensions', 'atleast_1d  atleast_2d atleast_3d broadcast broadcast_to broadcast_arrays expand_dims squeeze'.split())
        insertRoutine(di, 'Changing kind of array', 'asarray  asanyarray asmatrix asfarray asarray_chkfinite asscalar require'.split())
        insertRoutine(di, 'Joining arrays', 'concatenate stack column_stack dstack hstack vstack'.split())
        insertRoutine(di, 'Splitting arrays', 'split  array_split dsplit hsplit vsplit'.split())
        insertRoutine(di, 'Tiling arrays', 'tile repeat'.split())
        insertRoutine(di, 'Adding and removing elements', 'delete insert append resize trim_zeros unique'.split())
        insertRoutine(di, 'Rearranging elements', 'flip  fliplr flipud reshape roll rot90'.split())
        d['NumPy routines (numpy)']['Binary operations'] = di = OrderedDict()
        insertRoutine(di, 'Elementwise bit operations', 'bitwise_and bitwise_or bitwise_xor invert left_shift right_shift'.split())
        insertRoutine(di, 'Bit packing', 'packbits unpackbits'.split())

        d['NumPy routines (numpy)']['Indexing routines'] = di = OrderedDict()
        insertRoutine(di, 'Generating index arrays', 'nonzero where indices ogrid diag_indices diag_indices_from mask_indices tril_indices tril_indices_from triu_indices triu_indices_from'.split())
        insertRoutine(di, 'Indexing-like operations', 'take choose compress diag diagonal select'.split())
        insertRoutine(di, 'Inserting data into arrays', 'place put putmask fill_diagonal'.split())
        insertRoutine(di, 'Iterating over arrays', 'nditer ndenumerate flatiter'.split())

        d['NumPy routines (numpy)']['Logic functions'] = di = OrderedDict()
        insertRoutine(di, 'Truth value testing', 'all any'.split())
        insertRoutine(di, 'Array contents', 'isfinite isinf isnan isneginf isposinf'.split())
        insertRoutine(di, 'Array type testing', 'iscomplex iscomplexobj isreal isrealobj isscalar'.split())
        insertRoutine(di, 'Logical operations', 'logical_and logical_or logical_not logical_xor'.split())
        insertRoutine(di, 'Comparison', 'allclose isclose array_equal array_equiv greater greater_equal less less_equal equal not_equal'.split())

        d['NumPy routines (numpy)']['Mathematical functions'] = di = OrderedDict()
        insertRoutine(di, 'Trigonometric functions', 'sin cos tan arcsin arccos arctan hypot arctan2 degrees radians unwrap deg2rad rad2deg'.split())
        insertRoutine(di, 'Hyperbolic functions', 'sinh cosh tanh arcsinh arccosh arctanh'.split())
        insertRoutine(di, 'Rounding', 'around round_ rint fix floor ceil trunc'.split())
        insertRoutine(di, 'Sums, products, differences', 'prod sum nanprod nansum cumprod cumsum nancumprod nancumsum diff ediff1d gradient cross trapz'.split())
        insertRoutine(di, 'Exponents and logarithms', 'exp expm1 exp2 log log10 log2 log1p logaddexp logaddexp2'.split())
        insertRoutine(di, 'Other special functions', 'i0 sinc'.split())
        insertRoutine(di, 'Floating point routines', 'signbit copysign frexp ldexp nextafter spacing'.split())
        insertRoutine(di, 'Arithmetic operations', 'add reciprocal negative multiply divide power subtract true_divide floor_divide float_power fmod mod modf remainder divmod'.split())
        insertRoutine(di, 'Handling complex numbers', 'angle real imag conj'.split())
        insertRoutine(di, 'Miscellaneous', 'convolve clip sqrt cbrt square absolute fabs sign heaviside maximum minimum fmax fmin nan_to_num real_if_close interp'.split())

        d['NumPy routines (numpy)']['Random sampling (numpy.random)'] = di = OrderedDict()
        insertRoutine(di, 'Simple random data', 'rand randn randint random_integers random_sample random ranf sample choice bytes'.split(), packageName='numpy.random')
        insertRoutine(di, 'Permutations', 'shuffle permutation'.split(), packageName='numpy.random')
        insertRoutine(di, 'Distributions', 'beta binomial chisquare dirichlet exponential f gamma geometric gumbel hypergeometric laplace logistic lognormal logseries multinomial  negative_binomial noncentral_chisquare noncentral_f normal pareto poisson power rayleigh standard_cauchy standard_exponential standard_gamma standard_normal standard_t triangular uniform vonmises wald weibull zipf'.split(), packageName='numpy.random')

        d['NumPy routines (numpy)']['Sorting, searching, and counting'] = di = OrderedDict()
        insertRoutine(di, 'Sorting', 'sort lexsort argsort  msort sort_complex partition argpartition'.split())
        insertRoutine(di, 'Searching', 'argmax nanargmax argmin nanargmin argwhere nonzero flatnonzero where searchsorted extract'.split())
        insertRoutine(di, 'Counting', 'count_nonzero'.split())

        d['NumPy routines (numpy)']['Statistics'] = di = OrderedDict()
        insertRoutine(di, 'Order statistics', 'amin amax nanmin nanmax ptp percentile nanpercentile'.split())
        insertRoutine(di, 'Averages and variances', 'median average mean std var nanmedian nanmean nanstd nanvar'.split())
        insertRoutine(di, 'Correlating', 'corrcoef correlate cov'.split())
        insertRoutine(di, 'Histograms', 'histogram histogram2d histogramdd bincount digitize'.split())

        d['Online documentations'] = [WebItem(name='NumPy reference', url='https://numpy.org/devdocs/reference/'),
                                     WebItem(name='NumPy user guide', url='https://numpy.org/devdocs/user/'),
                                     WebItem(name='SciPy documentation', url='http://scipy.github.io/devdocs')]

        def createTree(d, parent):
            for name, child in d.items():
                node = QTreeWidgetItem()
                node.setText(0, name)
                node.docText = ''
                if parent is self.uiFunctions:
                    self.uiFunctions.addTopLevelItem(node)
                else:
                    parent.addChild(node)
                if isinstance(child, OrderedDict):
                    createTree(d=child, parent=node)
                else:
                    assert isinstance(child, list)
                    for numpyItem in child:
                        node.addChild(numpyItem)

        createTree(d, self.uiFunctions)
        self.uiDoc.setUrl(QUrl('https://numpy.org/devdocs/reference'))
#        self.createUIFunctionsNumpyGeneric()

    def createIdentifier(self, name):
        return ''.join([c if c.isalnum() else '_' for c in name.split('.')[0]])

    def insertRasterInput(self, name, filename):

        name = self.createIdentifier(name)

        ds = Open(filename=filename)

        itemImage = InputRasterNode()
        itemImage.setText(0, name)
        itemImage.setText(1, 'array{}'.format(str(list(ds.shape))))
        itemImage.setIcon(0, QIcon(os.path.join(self.appdir, 'icons', 'raster.png')))
        itemImage.setFlags(itemImage.flags() | Qt.ItemIsEditable)

        itemFilename = QTreeWidgetItem()
        itemFilename.setText(0, 'filename')
        itemFilename.setText(1, filename)

        itemMeta = QTreeWidgetItem()
        itemMeta.setText(0, 'metadata')

        meta = ds.getMetadataDict()
        for domainName in sorted(meta.keys()):

            if domainName != '':
                if domainName in ['DERIVED_SUBDATASETS', 'IMAGE_STRUCTURE']:
                    continue
            itemDomainMeta = QTreeWidgetItem()
            itemDomainMeta.setText(0, domainName)
            itemMeta.addChild(itemDomainMeta)
            for key in meta[domainName].keys():
                item = QTreeWidgetItem()
                item.setText(0, key)
                value = meta[domainName][key]
                item.setText(1, str(value))
                if isinstance(value, list):
                    for i, v in enumerate(value):
                        itemV = QTreeWidgetItem()
                        itemV.setText(0, str(i))
                        itemV.setText(1, str(v))
                        item.addChild(itemV)
                itemDomainMeta.addChild(item)

        itemOptions = QTreeWidgetItem()
        itemOptions.setText(0, 'GDAL options')

        itemNoDataValue = QTreeWidgetItem()
        itemNoDataValue.setText(0, 'no data value')
        itemNoDataValue.setText(1, str(ds.getNoDataValue()))
        itemNoDataValue.setFlags(itemImage.flags() | Qt.ItemIsEditable)
        itemOptions.addChild(itemNoDataValue)

        itemResampleAlg = QTreeWidgetItem()
        itemResampleAlg.setText(0, 'resampling')
        itemResampleAlg.setText(1, 'NearestNeighbour')
        itemResampleAlg.setFlags(itemImage.flags() | Qt.ItemIsEditable)
        itemOptions.addChild(itemResampleAlg)

        itemImage.insertChildren(0, [itemFilename, itemMeta, itemOptions])

        self.uiInputs.insertTopLevelItem(self.uiInputs.topLevelItemCount(), itemImage)
        itemOptions.setExpanded(True)

    def insertVectorInput(self, name, filename, layer=0):

        name = self.createIdentifier(name)

        ds = OpenLayer(filename=filename, layerNameOrIndex=layer)

        itemImage = InputVectorNode()
        itemImage.setText(0, name)
        itemImage.setText(1, '{} features, {} fields)'.format(ds.getFeatureCount(), ds.getFieldCount()))
        itemImage.setIcon(0, QIcon(os.path.join(self.appdir, 'icons', 'vector.png')))
        itemImage.setFlags(itemImage.flags() | Qt.ItemIsEditable)

        itemFilename = QTreeWidgetItem()
        itemFilename.setText(0, 'filename')
        itemFilename.setText(1, filename)

        names =  ['filename', 'layerNameOrIndex']
        values = [filename,   str(layer)]
        items = list()
        for name, value in zip(names, values):
            item = QTreeWidgetItem()
            item.setText(0, name)
            item.setText(1, str(value))
            if name is 'layerNameOrIndex':
                item.setFlags(itemImage.flags() | Qt.ItemIsEditable)
            items.append(item)

        itemImage.addChildren(items)

        itemOptions = QTreeWidgetItem()
        itemOptions.setText(0, 'GDAL options')
        itemImage.addChild(itemOptions)

        names =  ['initValue', 'burnValue', 'burnAttribute', 'allTouched', 'filterSQL', 'dtype']
        values = ['0',         '1',         'None',          'False',      'None',      'float32']
        items = list()
        for name, value in zip(names, values):
            item = QTreeWidgetItem()
            item.setText(0, name)
            item.setText(1, str(value))
            item.setFlags(itemImage.flags() | Qt.ItemIsEditable)
            items.append(item)
        itemOptions.addChildren(items)

        self.uiInputs.insertTopLevelItem(self.uiInputs.topLevelItemCount(), itemImage)
        itemOptions.setExpanded(True)


    def insertRasterOutput(self, name, filename):

        name = self.createIdentifier(name)

        format = 'ENVI'
        options = ['INTERLEAVE=BSQ']

        itemImage = OutputRasterNode()
        itemImage.setText(0, name)
        itemImage.setIcon(0, QIcon(os.path.join(self.appdir, 'icons', 'raster.png')))
        itemImage.setFlags(itemImage.flags() | Qt.ItemIsEditable)


        names = ['filename', 'format', 'options']
        values = [filename, format, options]
        items = list()
        for name, value in zip(names, values):
            item = QTreeWidgetItem()
            item.setText(0, name)
            item.setText(1, str(value))
            item.setFlags(itemImage.flags() | Qt.ItemIsEditable)
            items.append(item)
        itemImage.insertChildren(0, items)

        self.uiOutputs.insertTopLevelItem(self.uiOutputs.topLevelItemCount(), itemImage)
        itemImage.setExpanded(True)

    def logText(self, text):
        self.uiLog.append(text)

    def currentInput(self):
        if len(self.uiInputs.selectedItems()) == 0:
            return None
        else:
            item = self.uiInputs.selectedItems()[0]
            if isinstance(item, InputRasterNode):
                return Open(filename=str(item.filename()))
            elif isinstance(item, InputVectorNode):
                return OpenLayer(filename=item.filename(), layerNameOrIndex=item.layerNameOrIndex())

    def code(self):
        return str(self.uiCode.text())

    def setCode(self, code):
        self.uiCode.setText(code)

    def projection(self):
        text = str(self.uiProjection.text())
        projection = osr.SpatialReference()
        if text.lower().startswith('epsg'):
            epsg = int(text.split(':')[1])
            errorCode = projection.ImportFromEPSG(epsg)
        else:
            errorCode = projection.ImportFromWkt(text)

        if errorCode != 0:
            self.logText('Error: incorrect user defined projection: <b>{}</b>'.format(text))
            return None

        return str(projection)

    def setProjection(self, projection):
        text = ' '.join(projection.split(' '))
        self.uiProjection.setText(text)
        self.uiProjection.setCursorPosition(0)

    def extent(self):
        try:
            return [float(ui.text()) for ui in (self.uiExtentXMin, self.uiExtentXMax, self.uiExtentYMin, self.uiExtentYMax)]
        except:
            self.logText('Error: incorrect user defined extent')

    def setExtent(self, extent):
        self.uiExtentXMin.setText(str(extent[0]))
        self.uiExtentXMax.setText(str(extent[1]))
        self.uiExtentYMin.setText(str(extent[2]))
        self.uiExtentYMax.setText(str(extent[3]))

    def resolution(self):
        try:
            return float(self.uiResolution.text())
        except:
            self.logText('Error: incorrect user defined resolution')

    def setResolution(self, resolution):
        self.uiResolution.setText(str(resolution))

    def windowXSize(self):
        return int(self.uiWindowXSize.value())

    def windowYSize(self):
        return int(self.uiWindowYSize.value())

    def handleProjectionToggled(self):
        self.uiProjectionBox.setEnabled(self.uiProjectionUser.isChecked())

    def handleProjectionFromSelectedInput(self):
        ds = self.currentInput()
        if isinstance(ds, Dataset):
            projection = str(ds.pixelGrid.projection)
        elif isinstance(ds, Layer):
            projection = str(ds.projection)
        else:
             self.logText('Error: selected item is not an input raster/vector')
             return
        self.setProjection(projection=projection)
        self.uiProjectionUser.click()

    def handleExtentFromSelectedInput(self):
        ds = self.currentInput()
        if isinstance(ds, Dataset):
            grid = ds.pixelGrid
        elif isinstance(ds, Layer):
            grid = ds.makePixelGrid(xRes=1e-10, yRes=1e-10)
        else:
            self.logText('Error: selected item is not an input raster/vector')
            return

        self.setExtent(grid.extent())
        self.uiExtentUser.click()

    def handleResolutionFromSelectedInput(self):
        ds = self.currentInput()
        if isinstance(ds, Dataset):
            resolution = ds.pixelGrid.xRes
        else:
            self.logText('Error: selected item is not an input raster')
            return

        self.setResolution(resolution)
        self.uiResolutionUser.click()

    def handleExtentToggled(self):
        self.uiExtentBox.setEnabled(self.uiExtentUser.isChecked())
        self.uiExtentXMin.setEnabled(self.uiExtentUser.isChecked())
        self.uiExtentXMax.setEnabled(self.uiExtentUser.isChecked())
        self.uiExtentYMin.setEnabled(self.uiExtentUser.isChecked())
        self.uiExtentYMax.setEnabled(self.uiExtentUser.isChecked())

    def handleResolutionToggled(self):
        self.uiResolutionBox.setEnabled(self.uiResolutionUser.isChecked())

    def handleAddInputRaster(self):
        dialog = QFileDialog()
        if dialog.exec_():
            for filename in dialog.selectedFiles():
                filename = str(filename)
                self.insertRasterInput(name=os.path.basename(filename), filename=filename)

    def handleAddInputVector(self):
        dialog = QFileDialog()
        if dialog.exec_():
            for filename in dialog.selectedFiles():
                filename = str(filename)
                self.insertVectorInput(name=os.path.basename(filename), filename=filename)

    def handleRemoveInput(self):
        for item in self.uiInputs.selectedItems():
            for i in range(self.uiInputs.topLevelItemCount()):
                if item is self.uiInputs.topLevelItem(i):
                    self.uiInputs.takeTopLevelItem(i)

    def handleAddOutputRaster(self):
        filename = str(QFileDialog.getSaveFileName(self))
        if filename != '':
            self.insertRasterOutput(name=os.path.basename(filename), filename=(filename))

    def handleRemoveOutput(self):
        for item in self.uiOutputs.selectedItems():
            for i in range(self.uiOutputs.topLevelItemCount()):
                if item is self.uiOutputs.topLevelItem(i):
                    self.uiOutputs.takeTopLevelItem(i)

    def handleExecute(self, checked):

        self.uiLog.clear()
        code = self.code()

        if code.strip() == '':
            return

        # try to evaluate the code as an simple expression (standard calculator mode)
        try:
            xSize = self.windowXSize()
            ySize = self.windowYSize()
            result = eval(code)
            self.logText('= '+str(result))
            return
        except:
            pass

        self.logText('analyse code')
        calculator = Calulator()
        calculator.controls.setProgressBar(progressBar=self.progressBar)

        # set inputs
        options = dict()
        for i in range(self.uiInputs.topLevelItemCount()):
            node = self.uiInputs.topLevelItem(i)
            assert isinstance(node, IONode)
            key = node.name()
            index = code.find(key)
            if index == -1: continue
            try:
                if code[index - 1].isalnum(): continue
                if code[index - 1] == '_': continue
                if code[index+len(key)].isalnum(): continue
                if code[index+len(key)] == '_': continue
            except IndexError:
                pass

            options[key] = node.options()
            value = node.input()
            if isinstance(node, InputRasterNode):
                calculator.inputRaster.setRaster(key=key, value=value)
                self.logText(r'...<b>{}</b> found (input raster)'.format(key))
            if isinstance(node, InputVectorNode):
                calculator.inputVector.setVector(key=key, value=value)
                self.logText('...<b>{}</b> found (input vector)'.format(key))

        # set outputs
        outputKeys = list()
        for i in range(self.uiOutputs.topLevelItemCount()):
            node = self.uiOutputs.topLevelItem(i)
            assert isinstance(node, OutputRasterNode)
            key = node.name()
            outputKeys.append(key)
            if code.find(key) == -1:
                continue
            try:
                output = node.output()
            except:
                self.logText('Error: incorrect output definition: <b>{}</b>'.format(key))
                return
            calculator.outputRaster.setRaster(key=key, value=output)
            self.logText('...<b>{}</b> found (output raster)'.format(key))

        # make pixel grid
        # - projection
        if self.uiProjectionUser.isChecked():
            projection = self.projection()
            if projection is None: return
            calculator.controls.setProjection(projection=projection)

        # - exent
        if self.uiExtentIntersection.isChecked():
            calculator.controls.setAutoFootprint(hubdc.const.FOOTPRINT_INTERSECTION)
        elif self.uiExtentUnion.isChecked():
            calculator.controls.setAutoFootprint(hubdc.const.FOOTPRINT_UNION)
        elif self.uiExtentUser.isChecked():
            extent = self.extent()
            if extent is None: return
            calculator.controls.setFootprint(*extent)

        # - resolution
        if self.uiResolutionHighest.isChecked():
            calculator.controls.setAutoResolution(hubdc.const.RESOLUTION_MINIMUM)
        elif self.uiResolutionLowest.isChecked():
            calculator.controls.setAutoResolution(hubdc.const.RESOLUTION_MAXIMUM)
        elif self.uiResolutionUser.isChecked():
            res = float(self.resolution())
            if res is None: return
            calculator.controls.setResolution(xRes=res, yRes=res)

        # - generate grid and set
        try:
            grid = calculator.controls._makeAutoGrid(inputRasterContainer=calculator.inputRaster)
            calculator.controls.setReferenceGrid(grid=grid)
        except:
            self.logText('Error: can not derive reference pixel grid from inputs')
            return

        # - update ui
        if not self.uiProjectionUser.isChecked():
            self.setProjection(grid.projection)
        if not self.uiExtentUser.isChecked():
            self.setExtent(grid.extent())
        if not self.uiResolutionUser.isChecked():
            self.setResolution(grid.xRes)

        calculator.controls.setWindowXSize(self.windowXSize())
        calculator.controls.setWindowYSize(self.windowYSize())

        self.logText('')

        try:
            calculator.applyCode(code=code, options=options, outputKeys=outputKeys)
        except CodeExecutionError as error:
            self.logText('')
            html = '<p style="color:red;">{}</p>'.format(error.message).replace('\n', '<br>')
            self.logText(text=html)
            #for line in error.message.split('\n'):
            #    if line.strip().startswith('File "<string>", line'):
            #        l = int(line.split(' ')[-1])-1
            #        self.uiCode.setSelection(l, 0, l, len(str(self.uiCode.text(l))))

    def handleFunctionSelection(self, selected, deselected):
        for index in selected.indexes():
            item = self.uiFunctions.itemFromIndex(index)
            if isinstance(item, NumpyItem):
                html = r'<pre><code>'+item.doc+'</code></pre>'.replace('\n', '<br>')
                self.uiDoc.setHtml(html)
            elif isinstance(item, WebItem):
                self.uiDoc.setUrl(QUrl(item.url))
            else:
                self.uiDoc.setHtml('')

    def handleFunctionDoubleClicked(self,  item, column):
        if isinstance(item, NumpyItem):
            self.uiCode.replaceSelectedText(item.doubleClickInsert)
            self.uiCode.setFocus()

    def handleInputsDoubleClicked(self, item, column):
        try:
            if isinstance(item, (InputRasterNode, InputVectorNode)):
                name = item.text(0)
                self.uiCode.replaceSelectedText(name)
            elif isinstance(item, QTreeWidgetItem):
                if item.text(0) == 'metadata':
                    name = item.parent().text(0)
                    self.uiCode.replaceSelectedText('metadata({name})'.format(name=name))
                elif item.parent().text(0) == 'metadata':
                    name = item.parent().parent().text(0)
                    domain = item.text(0)
                    self.uiCode.replaceSelectedText("metadata({name})['{domain}']".format(name=name, domain=domain))
                elif item.parent().parent().text(0) == 'metadata':
                    name = item.parent().parent().parent().text(0)
                    domain = item.parent().text(0)
                    key = item.text(0)
                    self.uiCode.replaceSelectedText("metadata({name})['{domain}']['{key}']".format(name=name, domain=domain, key=key))
                elif item.text(0) == 'no data value':
                    name = item.parent().parent().text(0)
                    self.uiCode.replaceSelectedText('noDataValue({name})'.format(name=name))
            self.uiCode.setFocus()
        except:
            pass

    def handleOutputsDoubleClicked(self, item, column):
        if isinstance(item, OutputRasterNode):
            name = item.text(0)
            self.uiCode.replaceSelectedText(name)
            self.uiCode.setFocus()

if __name__ == '__main__':

    import enmapboxtestdata

    app = QApplication(sys.argv)

    calculator = CalculatorMainWindow()
    # load test data
    calculator.insertRasterInput(name='enmap', filename=enmapboxtestdata.enmap)
    calculator.insertRasterInput(name='hymap', filename=enmapboxtestdata.hymap)
    calculator.insertVectorInput(name='landCover', filename=enmapboxtestdata.landcover)
    calculator.insertRasterOutput(name='result',
                            filename=os.path.join(tempfile.gettempdir(), 'HUB-Datacube-Calculator', 'result.img'))
    calculator.setCode(code='\n'.join(['result = enmap',
                                       'result[:, landCover[0] == 0] = noDataValue(enmap)',
                                       'setNoDataValue(result, noDataValue(enmap))',
                                       'setMetadata(result, metadata(enmap))']))
    #calculator.setCode(code='(enmap)\nprint(landCover.max())\nresult = landCover')

    calculator.show()
    sys.exit(app.exec_())

