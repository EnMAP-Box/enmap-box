from os import DirEntry, scandir
from os.path import dirname, join

import numpy
from collections import OrderedDict
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from enmapboxapplications.imagemathapp.routines import *

def routinesDictionary():

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
    insertRoutine(d, 'Dataset interaction', 'noDataValue setNoDataValue metadata setMetadata descriptions setDescriptions categoryNames setCategoryNames categoryColors setCategoryColors'.split(), packageName=None)

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

    d['Online documentations'] = [WebItem(name='NumPy reference', url=r'http://www.numpy.org/devdocs/reference/'),
                                 WebItem(name='NumPy user guide', url=r'http://www.numpy.org/devdocs/user/quickstart.html'),
                                 WebItem(name='SciPy documentation', url=r'http://scipy.github.io/devdocs')]

    d['Code snippets'] = list()
    snippetsFolder = join(dirname(__file__), 'snippets')
    entry: DirEntry

    for entry in scandir(snippetsFolder):
        if entry.name.endswith('.py'):
            with open(entry.path) as file:
                code = file.read()
            d['Code snippets'].append(SnippetItem(name=entry.name, code=code, filename=entry.path))

    return d

def createTree(d, tree):
    for name, child in d.items():
        node = QTreeWidgetItem()
        node.setText(0, name)
        node.docText = ''
        if isinstance(tree, QTreeWidget):
            tree.addTopLevelItem(node)
        else:
            tree.addChild(node)
        if isinstance(child, OrderedDict):
            createTree(d=child, tree=node)
        else:
            assert isinstance(child, list)
            for numpyItem in child:
                node.addChild(numpyItem)

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

class SnippetItem(NumpyItem):

    def __init__(self, name, code, filename):
        NumpyItem.__init__(
            self, name=name, doc=f'source: {filename}\n\n{code}',
            doubleClickInsert=code,
            dragInsert=code
        )
