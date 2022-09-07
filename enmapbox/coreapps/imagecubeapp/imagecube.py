# -*- coding: utf-8 -*-
"""
Demonstrates GLVolumeItem for displaying volumetric data.

"""
import enum
import pathlib
import pickle
import sys
import time
import typing
import numpy as np
from OpenGL.GL import glEnd, glVertex3f, glColor4f, glLineWidth, GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST, \
    glEnable, glHint, glBegin, GL_LINES

from enmapbox.qgispluginsupport.qps.utils import loadUi, SpatialExtent
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QColor, QVector3D, QMatrix4x4
from qgis.PyQt.QtWidgets import QMainWindow, QApplication, QCheckBox, QLineEdit
from qgis.core import QgsRasterLayer, Qgis, QgsRasterRenderer, QgsRectangle, QgsCoordinateReferenceSystem, \
    QgsTaskManager, QgsApplication, QgsSingleBandGrayRenderer, QgsMultiBandColorRenderer, QgsPalettedRasterRenderer, \
    QgsContrastEnhancement, QgsSingleBandPseudoColorRenderer, QgsRasterMinMaxOrigin, QgsProject, \
    QgsTask, QgsMapLayerProxyModel, QgsRasterBlock, QgsRasterBlockFeedback, QgsSingleBandColorDataRenderer
from qgis.gui import QgsMapCanvas, QgsMapLayerComboBox

from enmapbox.gui import SliderSpinBox, DoubleSliderSpinBox, SpatialExtentMapTool
import enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.opengl as gl
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem, GLOptions
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.opengl.GLViewWidget import GLViewWidget
from enmapbox.qgispluginsupport.qps.layerproperties import showLayerPropertiesDialog, rendererFromXml, rendererToXml
from . import NAME, VERSION

KEY_GL_ITEM_GROUP = 'CUBEVIEW/GL_ITEM_GROUP'
KEY_DEFAULT_TRANSFORM = 'CUBEVIEW/DEFAULT_TRANSFORM'
QGIS2NUMPY_DATA_TYPES = {Qgis.Byte: np.byte,
                         Qgis.UInt16: np.uint16,
                         Qgis.Int16: np.int16,
                         Qgis.UInt32: np.uint32,
                         Qgis.Int32: np.int32,
                         Qgis.Float32: np.float32,
                         Qgis.Float64: np.float64,
                         Qgis.CFloat32: complex,
                         Qgis.CFloat64: np.complex64,
                         Qgis.ARGB32: np.uint32,
                         Qgis.ARGB32_Premultiplied: np.uint32}


class TaskMock(QgsTask):
    def __init__(self):
        super(TaskMock, self).__init__()


def qaRed(array: np.ndarray) -> np.ndarray:
    return (array >> 16) & 0xff


def qaGreen(array: np.ndarray) -> np.ndarray:
    return (array >> 8) & 0xff


def qaBlue(array: np.ndarray) -> np.ndarray:
    return array & 0xff


def qaAlpha(array: np.ndarray) -> np.ndarray:
    return array >> 24


class GLItem(enum.Enum):
    Text = 'TEXT'
    SliceX = 'SLICE_X'
    SliceY = 'SLICE_Y'
    SliceZ = 'SLICE_Z'
    Cube = 'CUBE'
    Box = 'IMAGE_BOX_FULL'
    BoxSubset = 'IMAGE_BOX_SUBSET'
    Axes = 'AXES'
    TopPlane = 'TOPPLANE'


class ImageCubeGLWidget(GLViewWidget):

    def __init__(self, *args, **kwds):
        super(ImageCubeGLWidget, self).__init__(*args, *kwds)

        self.mTextLabels = []

        self.mShowCameraInfo = True

    def addTextLabel(self, pos: QVector3D, text: str, color=QColor('white')):
        assert isinstance(text, str)
        self.mTextLabels.append((pos, text, color))

    def clearTextLabels(self):
        self.mTextLabels.clear()

    def setShowCameraInfo(self, b: bool):
        assert isinstance(b, bool)
        self.mShowCameraInfo = b

    def paintGL(self, *args, **kwds):

        from OpenGL.GL import glEnable, glDisable, GL_DEPTH_TEST
        glEnable(GL_DEPTH_TEST)

        GLViewWidget.paintGL(self, *args, **kwds)

        glDisable(GL_DEPTH_TEST)
        for (pos, text, color) in self.mTextLabels:
            self.qglColor(color)
            assert isinstance(pos, QVector3D)
            self.renderText(pos.x(), pos.y(), pos.z(), text)

        dist = self.opts['distance']
        elev = self.opts['elevation']
        azim = self.opts['azimuth']

        if self.mShowCameraInfo:
            info = 'dist: {} elev: {} azim: {}'.format(dist, elev, azim)
            self.renderText(2, 10, info)
            c = self.opts['center']
            info = 'center: {} {} {}'.format(c.x(), c.y(), c.z())
            self.renderText(2, 20, info)


def samplingGrid(layer: QgsRasterLayer, extent: QgsRectangle, ncb: int = 1, max_size: int = 2 * 2 ** 20) -> tuple:
    """
    :param layer:
    :param extent: QgsRectangles extent to show from image
    :param nl: original image number of lines
    :param ns: original image number of samples
    :param ncb: number of color bands to return. Will be multiplied by 4 for RGBA
                1 = standard RGB image, 144 = for 144 input bands (cube)
    :param max_size: max. size in bytes
    :return: nnl, nns = lines an sample to sample the extent
    """
    assert ncb >= 1

    ns, nl = layer.width(), layer.height()
    lW, lH = layer.extent().width(), layer.extent().height()
    eW, eH = extent.width(), extent.height()

    """
    nnl / eH = nl / lH
    nns / eW = ns / lW
    """
    nnl = int(nl * eH / lH)
    nns = int(ns * eW / lW)

    TOTAL_SIZE = nnl * nns * ncb * 4
    if TOTAL_SIZE < max_size:
        return nnl, nns
    else:
        """
        Eq. 1.  nnl * nns * ncb * 4 = MAX_SIZE
                nnl = MAX_SIZE / (nns * ncb * 4)
        Eq. 2.  eW / eH = nns / nnl
                nns = eW / eH * nnl

        Eq. 2 in 1
                nnl = MAX_SIZE * eH
                      eW * nnl * ncb * 4

                nnl^2 = MAX_SIZE * eH / (eW * ncb * 4)

                nnl = sqrt(MAX_SIZE * eH / (eW * ncb * 4))
        """

        nnl = np.sqrt(max_size * eH / (eW * ncb * 4))
        nns = eW / eH * nnl
        nnl, nns = int(nnl), int(nns)
        return nnl, nns


def renderImageData(task: QgsTask, dump):
    """
    Renders image data into RGBA Arrays
    :param task: QgsTask
    :param dump: serialized list of ImageCubeRenderJobs
    :return:
    """
    jobs = pickle.loads(dump)

    results = []
    n = len(jobs)

    renderCallsTotal = 0
    renderCallsDone = 0
    for job in jobs:
        assert isinstance(job, ImageCubeRenderJob)
        if job.id() == GLItem.Cube:
            renderCallsTotal += job.mLayerShape[0]
        elif job.id() == GLItem.TopPlane:
            renderCallsTotal += 1

    for i, job in enumerate(jobs):
        t0 = time.time()
        if task.isCanceled():
            return pickle.dumps(results)

        assert isinstance(job, ImageCubeRenderJob)
        lyr = job.rasterLayer()
        renderer = job.renderer()

        assert isinstance(lyr, QgsRasterLayer)
        assert isinstance(renderer, QgsRasterRenderer)

        nb = lyr.bandCount()
        ns = lyr.width()
        nl = lyr.height()

        if job.id() == GLItem.Cube:
            feedback = QgsRasterBlockFeedback()
            feedback.setPreviewOnly(True)
            feedback.setRenderPartialOutput(True)

            lyr.setRenderer(renderer)
            ext = job.extent()
            h, w = samplingGrid(lyr, ext, max_size=job.mMaxBytes, ncb=nb)

            if isinstance(renderer, QgsSingleBandGrayRenderer):
                setBand = renderer.setGrayBand
            elif isinstance(renderer, QgsSingleBandPseudoColorRenderer):
                setBand = renderer.setBand
            elif isinstance(renderer, QgsSingleBandColorDataRenderer):
                setBand = lambda *args: None
            elif isinstance(renderer, QgsMultiBandColorRenderer):
                setBand = lambda *args: None
            elif isinstance(renderer, QgsPalettedRasterRenderer):

                def onSetBand(b: int):
                    nonlocal renderer
                    nonlocal lyr
                    renderer = QgsPalettedRasterRenderer(lyr.dataProvider(), b, renderer.classes())
                    lyr.setRenderer(renderer)

                setBand = onSetBand

            else:
                raise NotImplementedError()

            # x, y, z, RGBA
            rgba = np.empty((h, w, nb, 4), dtype=np.uint8)

            for b in range(nb):
                setBand(b + 1)

                block = renderer.block(0, ext, w, h, feedback=feedback)

                assert isinstance(block, QgsRasterBlock)
                assert block.isValid()
                assert block.dataType() != Qgis.UnknownDataType

                colorArray = np.frombuffer(block.data(), dtype=QGIS2NUMPY_DATA_TYPES[block.dataType()])

                rgba[:, :, b, 0] = qaRed(colorArray).reshape((h, w))  # np.asarray([qRed(c) for c in colorArray])
                rgba[:, :, b, 1] = qaGreen(colorArray).reshape((h, w))  # np.asarray([qGreen(c) for c in colorArray])
                rgba[:, :, b, 2] = qaBlue(colorArray).reshape((h, w))  # np.asarray([qBlue(c) for c in colorArray])
                rgba[:, :, b, 3] = qaAlpha(colorArray).reshape((h, w))  # np.asarray([qAlpha(c) for c in colorArray])

                renderCallsDone += 1
                if isinstance(task, TaskMock):
                    QApplication.processEvents()

                task.setProgress(100 * renderCallsDone / renderCallsTotal)

            rgba = np.rot90(rgba, axes=(0, 1))
            rgba = np.flip(rgba, 0)
            # rgba = np.flip(rgba, 2)

            job.setRGBA3D(rgba)

        elif job.id() == GLItem.TopPlane:
            lyr.setRenderer(renderer)
            ext = job.extent()
            h, w = samplingGrid(lyr, ext, max_size=job.mMaxBytes, ncb=1)
            block = renderer.block(1, ext, w, h)
            assert isinstance(block, QgsRasterBlock)
            colorArray = np.frombuffer(block.data(), dtype=QGIS2NUMPY_DATA_TYPES[block.dataType()])

            rgba = np.empty((h, w, 4), dtype=np.ubyte)

            rgba[..., 0] = qaRed(colorArray).reshape((h, w))
            rgba[..., 1] = qaGreen(colorArray).reshape((h, w))
            rgba[..., 2] = qaBlue(colorArray).reshape((h, w))
            rgba[..., 3] = qaAlpha(colorArray).reshape((h, w))

            rgba = np.rot90(rgba, axes=(0, 1))
            rgba = np.flip(rgba, 0)
            renderCallsDone += 1
            task.setProgress(100 * renderCallsDone / renderCallsTotal)

            job.setRGBA2D(rgba)

        job.mDuration = time.time() - t0

        if job.rgba2D() is not None or job.rgba3D() is not None:
            results.append(job)

    task.setProgress(100)
    return pickle.dumps(results)

    pass


class ImageCubeAxisItem(gl.GLAxisItem):
    """
    **Bases:** :class:`GLGraphicsItem <pyqtgraph.opengl.GLGraphicsItem>`

    Displays three lines indicating origin and orientation of local coordinate system.

    """

    def __init__(self, *args, **kwds):
        super(ImageCubeAxisItem, self).__init__(*args, **kwds)
        self.mLineWidth = 2.0

        self.mColorZ = QColor('green')
        self.mColorY = QColor('yellow')
        self.mColorX = QColor('blue')

    def setLineWidth(self, w: float):
        assert w >= 0
        self.mLineWidth = w

    def paint(self):
        glLineWidth(self.mLineWidth)
        self.setupGLState()

        if self.antialias:
            glEnable(GL_LINE_SMOOTH)
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        glBegin(GL_LINES)

        x, y, z = self.size()
        glColor4f(*self.mColorZ.getRgb())  # z is green
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, z)

        glColor4f(*self.mColorY.getRgb())  # y is yellow
        glVertex3f(0, 0, 0)
        glVertex3f(0, y, 0)

        glColor4f(*self.mColorX.getRgb())  # x is blue
        glVertex3f(0, 0, 0)
        glVertex3f(x, 0, 0)
        glEnd()


class ImageCubeRenderJob(object):
    """
    Serilizable object that describes a render job to get image-cube color values
    """

    class JobType(enum.Enum):
        Normal = 1
        SliceX = 2
        SliceY = 3
        SliceZ = 4

    def __init__(self, id: GLItem, layer: QgsRasterLayer, renderer: QgsRasterRenderer):
        assert isinstance(id, GLItem)
        self.mID = id
        self.mUri = layer.source()
        self.mDataProvider = layer.dataProvider().name()
        self.mRendererXML = rendererToXml(renderer).toString()
        self.mExtent = layer.extent().toRectF()
        self.mMaxBytes = 1024 ** 2
        self.mLayerShape = [layer.bandCount(), layer.height(), layer.width()]
        self.mDuration = None
        self.mRGBA2D = None
        self.mRGBA3D = None

    def setMaxBytes(self, n: int):
        assert n > 1024
        self.mMaxBytes = n

    def setExtent(self, extent: QgsRectangle):
        self.mExtent = extent.toRectF()

    def extent(self) -> QgsRectangle:
        return QgsRectangle(self.mExtent)

    def __eq__(self, other) -> bool:
        if not isinstance(other, ImageCubeRenderJob):
            return False
        else:
            return self.mID == other.mID and \
                   self.mUri == other.mUri and \
                   self.mRendererXML == other.mRendererXML and \
                   self.mExtent == other.mExtent and \
                   self.mMaxBytes == other.mMaxBytes

    def __hash__(self):
        return hash((self.mID, self.mUri, self.mRendererXML))

    def id(self) -> GLItem:
        return self.mID

    def rasterLayer(self) -> QgsRasterLayer:
        return QgsRasterLayer(self.mUri, str(self.id().value), self.mDataProvider)

    def renderer(self) -> QgsRasterRenderer:
        return rendererFromXml(self.mRendererXML)

    def setRGBA2D(self, array: np.ndarray):
        assert isinstance(array, np.ndarray)
        assert array.ndim == 3
        assert array.shape[2] == 4
        self.mRGBA2D = array

    def rgba2D(self) -> np.ndarray:
        return self.mRGBA2D

    def setRGBA3D(self, array: np.ndarray):
        assert isinstance(array, np.ndarray)
        assert array.ndim == 4
        assert array.shape[3] == 4
        self.mRGBA3D = array

    def rgba3D(self) -> np.ndarray:
        return self.mRGBA3D


class ImageCubeWidget(QMainWindow):
    sigExtentRequested = pyqtSignal(QMainWindow)

    def __init__(self, *args, **kwds):

        super(ImageCubeWidget, self).__init__(*args, **kwds)
        pathUi = pathlib.Path(__file__).parent / 'imagecube.ui'
        loadUi(pathUi, self)
        self.setWindowTitle('Image Cube')
        self.mCanvas = QgsMapCanvas()
        self.mCanvas.setVisible(False)
        self.mMapTools: typing.List[SpatialExtentMapTool] = []
        self.mSliceRenderer: QgsRasterRenderer = None
        self.mTopPlaneRenderer: QgsRasterRenderer = None

        self.mBandScaleFactor = 1

        self.mSpatialExtent = SpatialExtent(QgsCoordinateReferenceSystem())

        self.mMaxSizeTopPlane = 10 * 2 ** 20  # MByte
        self.mMaxSizeCube = 20 * 2 ** 20  # MByte
        self.sbCacheTopPlane.setValue(int(self.mMaxSizeTopPlane / 2 ** 20))
        self.sbCacheCube.setValue(int(self.mMaxSizeCube / 2 ** 20))

        def setTopPlaneCache(mBytes: int):
            self.mMaxSizeTopPlane = mBytes * 2 ** 20

        def setCubeCache(mBytes: int):
            self.mMaxSizeCube = mBytes * 2 ** 20

        self.sbCacheTopPlane.valueChanged.connect(setTopPlaneCache)
        self.sbCacheCube.valueChanged.connect(setCubeCache)

        self.mRGBATopPlane = None
        self.mRGBACube = None
        self.mRGBATopPlaneExtent = None
        self.mRGBACubeExtent = None

        self.mCubeSliceDensity = 2
        self.mSliceSliceDensity = 2

        self.mMapLayerComboBox: QgsMapLayerComboBox
        self.mMapLayerComboBox.setAllowEmptyLayer(True)
        self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mMapLayerComboBox.layerChanged.connect(self.onLayerChanged)

        self.mLastJobs = dict()
        self.btnLoadData.clicked.connect(self.actionLoadData.trigger)
        self.btnSetRendererTopPlane.clicked.connect(self.actionSetRendererTopPlane.trigger)
        self.btnSetRendererSlices.clicked.connect(self.actionSetRendererSlices.trigger)
        self.btnResetGLView.clicked.connect(self.actionResetGLView.trigger)
        self.btnSetExtent.setDefaultAction(self.actionSetExtent)

        self.actionValidate.triggered.connect(self.onValidate)
        self.actionLoadData.triggered.connect(lambda *args: self.startDataLoading(top=True, cube=True))
        self.actionSetRendererTopPlane.triggered.connect(self.onSetTopPlaneRenderer)
        self.actionSetRendererSlices.triggered.connect(self.onSetSliceRenderer)
        self.actionResetGLView.triggered.connect(self.resetCameraPosition)
        self.actionSetExtent.triggered.connect(self.onExtentRequested)

        self.spinBoxX: SliderSpinBox
        self.spinBoxY: SliderSpinBox
        self.spinBoxZ: SliderSpinBox
        for sb in [self.spinBoxX, self.spinBoxY, self.spinBoxZ]:
            sb.setMinimum(1)
            sb.spinbox.setMinimumWidth(50)
        self.spinBoxX.sigValueChanged.connect(lambda: self.drawSlice(GLItem.SliceX))
        self.spinBoxY.sigValueChanged.connect(lambda: self.drawSlice(GLItem.SliceY))
        self.spinBoxZ.sigValueChanged.connect(lambda: self.drawSlice(GLItem.SliceZ))

        self.doubleSpinBoxZScale: DoubleSliderSpinBox
        self.doubleSpinBoxZScale.setMinimum(0.1)
        self.doubleSpinBoxZScale.setMaximum(10)
        self.doubleSpinBoxZScale.setSingleStep(0.1)
        self.doubleSpinBoxZScale.setValue(1)
        self.doubleSpinBoxZScale.sigValueChanged.connect(self.onZScaleChanged)

        # register GLITem visibility checkboxes

        self.cbShowTopPlane.setProperty(KEY_GL_ITEM_GROUP, GLItem.TopPlane)
        self.cbShowCube.setProperty(KEY_GL_ITEM_GROUP, GLItem.Cube)
        self.cbShowSliceX.setProperty(KEY_GL_ITEM_GROUP, GLItem.SliceX)
        self.cbShowSliceY.setProperty(KEY_GL_ITEM_GROUP, GLItem.SliceY)
        self.cbShowSliceZ.setProperty(KEY_GL_ITEM_GROUP, GLItem.SliceZ)
        self.cbShowBoxImage.setProperty(KEY_GL_ITEM_GROUP, GLItem.Box)
        self.cbShowBoxSubset.setProperty(KEY_GL_ITEM_GROUP, GLItem.BoxSubset)
        self.cbShowAxis.setProperty(KEY_GL_ITEM_GROUP, GLItem.Axes)

        for cb in [self.cbShowTopPlane, self.cbShowCube,
                   self.cbShowSliceX, self.cbShowSliceY, self.cbShowSliceZ,
                   self.cbShowBoxImage, self.cbShowBoxSubset,
                   self.cbShowAxis
                   ]:
            assert isinstance(cb, QCheckBox)
            glItem = cb.property(KEY_GL_ITEM_GROUP)
            cb.clicked.connect(lambda b, glItem=glItem: self.setGLItemVisbility(glItem, b))

        self.cbSmooth.clicked.connect(self.onGLParametersChanged)
        self.sbSliceDensity.valueChanged.connect(self.onGLParametersChanged)
        self.glViewWidget().setShowCameraInfo(self.cbDebug.isChecked())
        self.cbDebug.clicked.connect(self.glViewWidget().setShowCameraInfo)

        self.mJobs = dict()
        self.mTasks = dict()

        w = self.glViewWidget()

        # center = w.opts['center']
        # dist = w.opts['distance']
        # elev = w.opts['elevation'] #* np.pi/180.
        # azim = w.opts['azimuth'] #* np.pi/180.

        self.mDefaultCAM = {}
        for k in ['distance', 'elevation', 'azimuth']:
            self.mDefaultCAM[k] = w.opts[k]

        self.onLayerChanged(self.mMapLayerComboBox.currentLayer())
        # hide slices
        # .setSlicesVisibility(False)

    def setSlicesVisibility(self, b: bool):
        for cb in [self.cbShowSliceX, self.cbShowSliceY, self.cbShowSliceZ]:
            cb.setChecked(b)
        s = ""

    def debug(self) -> bool:
        return self.cbDebug.isChecked()

    def glItemGroupItems(self, key: GLItem) -> list:
        assert isinstance(key, GLItem)
        return [i for i in self.glViewWidget().items if i.property(KEY_GL_ITEM_GROUP) == key]

    def setGLItemGroupItems(self, key: GLItem, items):
        """
        Adds a group of items identified by a key
        :param key:
        :param items:
        :return:
        """
        assert isinstance(key, GLItem)
        if not isinstance(items, list):
            items = [items]
        itemsOld = self.glItemGroupItems(key)

        for item in itemsOld:
            self.glViewWidget().removeItem(item)

        for item in items:
            item.setProperty(KEY_GL_ITEM_GROUP, key)
            self.glViewWidget().addItem(item)

    def resetCameraPosition(self):
        distance = self.mDefaultCAM['distance']
        elevation = self.mDefaultCAM['elevation']
        azimuth = self.mDefaultCAM['azimuth']
        if True:
            nb, nl, ns = self.layerDims()

            if ns is None:
                ns = nl = nb = 1

            center = QVector3D(0.5 * ns, -0.5 * nl, -0.5 * nb)
            elevation = 22  # °
            azimuth = -66
            self.glViewWidget().opts['center'] = center
            self.glViewWidget().update()
            distance = center.length() * 5

        self.glViewWidget().setCameraPosition(distance=distance, elevation=elevation, azimuth=azimuth)

    def layerDims(self) -> tuple:
        lyr = self.rasterLayer()
        if isinstance(lyr, QgsRasterLayer):
            ns = lyr.width()
            nl = lyr.height()
            nb = lyr.bandCount()
            return (nb, nl, ns)
        else:
            return (None, None, None)

    def layerSubsetDims(self) -> tuple:
        """
        Returns the dimensions of the layer subset in pixel / band coordinates
        :return: (ns0, ns1, nl0, nl1)
        """

        lyr = self.rasterLayer()
        if isinstance(lyr, QgsRasterLayer):
            ext = self.spatialExtent().toCrs(lyr.crs())
            s = ""

        return

    def cubeDims(self) -> tuple:
        """
        Returns the cube dimensions in (nb, nl, ns) order
        :return:
        """
        if isinstance(self.mRGBACube, np.ndarray):
            nns, nnl, nnb = self.mRGBACube.shape[0:3]
            return nnb, nnl, nns
        else:
            return (None, None, None)

    def topPlaneDims(self) -> tuple:
        """
        Returns the TOPPLANE dimensions as (nl, ns)
        :return: tuple
        """
        if isinstance(self.mRGBATopPlane, np.ndarray):
            nns, nnl = self.mRGBATopPlane.shape[0:2]
            return nnl, nns
        else:
            return None, None

    def rasterLayer(self) -> QgsRasterLayer:
        return self.mMapLayerComboBox.currentLayer()

    def sliceRenderer(self) -> QgsRasterRenderer:
        return self.mSliceRenderer

    def topPlaneRenderer(self) -> QgsRasterRenderer:
        return self.mTopPlaneRenderer

    def onExtentRequested(self):
        self.mMapTools.clear()
        self.sigExtentRequested.emit(self)

    def createExtentRequestMapTool(self, canvas: QgsMapCanvas):
        assert isinstance(canvas, QgsMapCanvas)

        mt = SpatialExtentMapTool(canvas)
        mt.sigSpatialExtentSelected.connect(lambda crs, ext: self.setSpatialExtent(SpatialExtent(crs, ext)))
        canvas.setMapTool(mt)
        self.mMapTools.append(mt)

    def onSetSliceRenderer(self):

        lyr = self.rasterLayer()
        if isinstance(lyr, QgsRasterLayer):
            lyr2 = QgsRasterLayer(lyr.source(), lyr.name(), lyr.dataProvider().name())
            r = self.sliceRenderer()
            if isinstance(r, QgsRasterRenderer):
                lyr2.setRenderer(r)
            showLayerPropertiesDialog(lyr2, None)

            self.setSliceRenderer(lyr2.renderer())

        self.onValidate()

    def onSetTopPlaneRenderer(self):

        lyr = self.rasterLayer()
        if isinstance(lyr, QgsRasterLayer):
            lyr2 = QgsRasterLayer(lyr.source(), lyr.name(), lyr.dataProvider().name())
            r = self.topPlaneRenderer()
            if isinstance(r, QgsRasterRenderer):
                lyr2.setRenderer(r)
            showLayerPropertiesDialog(lyr2, self.mCanvas)
            s = ""
            self.setTopPlaneRenderer(lyr2.renderer())

        self.onValidate()

    def setSliceRenderer(self, renderer: QgsRasterRenderer):
        assert isinstance(renderer, QgsRasterRenderer)
        self.mSliceRenderer = renderer.clone()
        self.startDataLoading(cube=True)

    def setTopPlaneRenderer(self, renderer: QgsRasterRenderer):
        assert isinstance(renderer, QgsRasterRenderer)
        self.mTopPlaneRenderer = renderer.clone()
        self.startDataLoading(top=True)

    def reloadData(self):
        self.mLastJobs.clear()
        self.startDataLoading(top=True, cube=True)

    def setExtent(self, extent: QgsRectangle):
        self.setSpatialExtent(SpatialExtent(self.crs(), extent))

    def setCrs(self, crs: QgsCoordinateReferenceSystem):
        self.setSpatialExtent(self.spatialExtent().toCrs(crs))

    def extent(self) -> QgsRectangle:
        return QgsRectangle(self.spatialExtent())

    def crs(self) -> QgsCoordinateReferenceSystem:
        return self.spatialExtent().crs()

    def spatialExtent(self) -> SpatialExtent:
        return self.mSpatialExtent

    def setSpatialExtent(self, spatialExtent: SpatialExtent):
        self.mSpatialExtent: SpatialExtent = spatialExtent
        assert isinstance(self.tbExtent, QLineEdit)
        info = '{},{}:{},{}:{}'.format(
            spatialExtent.xMinimum(), spatialExtent.yMaximum(),
            spatialExtent.xMaximum(), spatialExtent.yMaximum(),
            spatialExtent.crs().description())

        self.tbExtent.setText(info)
        self.tbExtent.setToolTip(info)
        self.reloadData()

    def print(self, msg: str, file=sys.stdout):
        if self.debug():
            print(msg, file=file)

    def startDataLoading(self, cube: bool = False, top: bool = False):

        lyr = self.rasterLayer()
        if not isinstance(lyr, QgsRasterLayer):
            return
        if top and not isinstance(self.topPlaneRenderer(), QgsRasterRenderer):
            return
        if cube and not isinstance(self.sliceRenderer(), QgsRasterRenderer):
            return

        ext = self.spatialExtent().toCrs(lyr.crs())

        jobList = []
        if top:
            jobTop = ImageCubeRenderJob(GLItem.TopPlane, lyr, self.topPlaneRenderer())
            jobTop.setExtent(ext)
            jobTop.setMaxBytes(self.mMaxSizeTopPlane)
            jobList.append(jobTop)

        if cube:
            jobCube = ImageCubeRenderJob(GLItem.Cube, lyr, self.sliceRenderer())
            jobCube.setMaxBytes(self.mMaxSizeCube)
            jobCube.setExtent(ext)
            jobList.append(jobCube)

        toDo = []
        for job in jobList:
            lastJob = self.mJobs.get(job.id())
            if lastJob != job:
                toDo.append(job)

        if True:
            toDo = jobList

        if len(toDo) == 0:
            # recall plotting of already loaded color data
            if isinstance(self.mRGBACube, np.ndarray):
                self.setRGBACube(self.mRGBACube, self.mRGBACubeExtent)
            if isinstance(self.mRGBATopPlane, np.ndarray):
                self.setRGBATopPlane(self.mRGBATopPlane, self.mRGBATopPlaneExtent)
            return

        dump = pickle.dumps(toDo)

        background = self.cbUseTaskManager.isChecked()
        if not background:
            qgsTask = TaskMock()
        else:
            qgsTask = QgsTask.fromFunction('', renderImageData, dump, on_finished=self.onDataLoaded)

        tid = id(qgsTask)
        self.mTasks[tid] = qgsTask
        qgsTask.progressChanged.connect(lambda p: self.progressBar.setValue(int(p)))
        qgsTask.taskCompleted.connect(lambda *args, tid=tid: self.onRemoveTask(tid))
        qgsTask.taskTerminated.connect(lambda *args, tid=tid: self.onRemoveTask(tid))

        if not background:
            self.onDataLoaded(qgsTask, renderImageData(qgsTask, dump))
        else:
            tm = QgsApplication.taskManager()
            assert isinstance(tm, QgsTaskManager)
            tm.addTask(qgsTask)

    def onRemoveTask(self, tid):
        if tid in self.mTasks.keys():
            del self.mTasks[tid]

    def setGLItemVisbility(self, key, b: bool):
        for item in self.glItemGroupItems(key):
            assert isinstance(item, GLGraphicsItem)
            item.setVisible(b)

    def glItemVisibility(self, key: GLItem) -> bool:
        assert isinstance(key, GLItem)
        for cb in self.findChildren(QCheckBox):
            assert isinstance(cb, QCheckBox)
            if cb.property(KEY_GL_ITEM_GROUP) == key:
                return cb.isChecked()

        return False

    def glViewWidget(self) -> ImageCubeGLWidget:
        return self.openglWidget

    def smooth(self) -> bool:
        return self.cbSmooth.isChecked()

    def sliceDensity(self) -> int:
        return self.sbSliceDensity.value()

    def onDataLoaded(self, _, dump):

        joblist = pickle.loads(dump)
        n = len(joblist)
        for i, job in enumerate(joblist):

            assert isinstance(job, ImageCubeRenderJob)
            self.print('Add {}'.format(job.id()))
            if job.id() == GLItem.Cube:
                self.setRGBACube(job.rgba3D(), job.extent())
                self.drawCube()
                self.drawSlice(GLItem.SliceX)
                self.drawSlice(GLItem.SliceY)
                self.drawSlice(GLItem.SliceZ)

            elif job.id() == GLItem.TopPlane:
                self.setRGBATopPlane(job.rgba2D(), job.extent())
                self.drawTopPlane()

            self.mJobs[job.id()] = job

            continue

    def onValidate(self) -> bool:

        b = True
        b &= isinstance(self.topPlaneRenderer(), QgsRasterRenderer)
        b &= isinstance(self.sliceRenderer(), QgsRasterRenderer)
        b &= isinstance(self.rasterLayer(), QgsRasterLayer) and self.rasterLayer().isValid()

        self.btnLoadData.setEnabled(b)

        return b

    def config(self) -> dict:
        lyr = self.rasterLayer()
        c = {'uri': lyr.source(), 'provider': lyr.dataProvider().name(),
             'x': self.x(), 'y': self.y(), 'z': self.z(),
             'rendererTop': self.topPlaneRenderer(), 'rendererSlices': self.sliceRenderer()
             }
        return c

    def setX(self, x: int):
        assert 0 < x <= self.spinBoxX.maximum()
        self.spinBoxX.setValue(x)

    def x(self) -> int:
        return self.spinBoxX.value()

    def setY(self, y: int):
        assert 0 < y <= self.spinBoxY.maximum()
        self.spinBoxY.setValue(y)

    def y(self) -> int:
        return self.spinBoxY.value()

    def z(self) -> int:
        return self.spinBoxZ.value()

    def setZ(self, z: int):
        assert 0 < z <= self.spinBoxZ.maximum()
        self.spinBoxZ.setValue(z)

    def setRGBATopPlane(self, rgba: np.ndarray, extent: QgsRectangle):
        assert isinstance(rgba, np.ndarray)
        assert rgba.ndim == 3
        assert rgba.shape[2] == 4
        assert rgba.dtype == np.uint8
        assert isinstance(extent, QgsRectangle)

        self.mRGBATopPlaneExtent = extent
        self.mRGBATopPlane = rgba

    def drawSubsetExtent(self):

        pass

    def drawTopPlane(self):

        rgba = self.mRGBATopPlane
        assert isinstance(rgba, np.ndarray)
        assert rgba.ndim == 3
        assert rgba.shape[2] == 4
        assert rgba.dtype == np.uint8

        nb, nl, ns = self.layerDims()
        nnl, nns = self.topPlaneDims()

        ox, oy, ob, sx, sy, sb = self.subsetDimensions(self.rasterLayer(), self.mRGBATopPlaneExtent, self.mRGBATopPlane)

        item = gl.GLImageItem(self.mRGBATopPlane)
        # scale as it would be in 1:1:1 scaled axis space
        item.scale(sx, sy, 1)
        item.translate(ox, oy, 0)
        item.rotate(180, 1, 0, 0)

        item.setProperty(KEY_DEFAULT_TRANSFORM, item.transform())

        # scale Z Dimension
        item.translate(0, 0, 1)

        # item.translate(-ns / 2, -nl / 2, job.sliceIndex())
        # item.rotate(-90, 0, 0, 1)
        self.setGLItemGroupItems(GLItem.TopPlane, item)
        item.setVisible(self.glItemVisibility(GLItem.TopPlane))
        # self.setGLItemVisbility(GLItem.TopPlane, )

    def onGLParametersChanged(self):
        self.drawCube()
        self.drawTopPlane()

    def subsetDimensions(self, lyr: QgsRasterLayer, subsetExtent: QgsRectangle, rgba: np.ndarray):
        """
        Returns the subset dimensions in pixel-space coordinates
        :param lyr: QgsRasterLayer - Original Raster Layer
        :param subsetExtent: QgsRectangle of layer subsets
        :param rgba: np.ndarray
        :return: ox, oy, ob, sx, sy, sb
        """
        if rgba.ndim == 4:
            nns, nnl, _, _ = rgba.shape
        elif rgba.ndim == 3:
            nns, nnl, _ = rgba.shape

        ns, nl, nb = lyr.width(), lyr.height(), lyr.bandCount()

        ext = lyr.extent()
        assert isinstance(ext, QgsRectangle)

        px_size_x = ext.width() / ns
        px_size_y = ext.height() / nl

        px_size_subset_x = subsetExtent.width() / nns
        px_size_subset_y = subsetExtent.height() / nnl

        ox = (subsetExtent.xMinimum() - ext.xMinimum()) / px_size_x
        oy = (ext.yMaximum() - subsetExtent.yMaximum()) / px_size_y
        ob = 0
        sb = 1
        sx = px_size_subset_x / px_size_x
        sy = px_size_subset_y / px_size_y

        return ox, oy, ob, sx, sy, sb

    def setRGBACube(self, rgba: np.ndarray, extent: QgsRectangle):

        assert isinstance(rgba, np.ndarray)
        assert rgba.ndim == 4
        assert rgba.shape[3] == 4
        assert rgba.dtype == np.uint8
        assert isinstance(extent, QgsRectangle)
        self.mRGBACube = rgba
        self.mRGBACubeExtent = extent

        # set allowed slices ranges to extent subset range
        if True:
            ox, oy, ob, sx, sy, sb = self.subsetDimensions(self.rasterLayer(), self.mRGBACubeExtent, self.mRGBACube)
            # layer and cube dimensions
            nns, nnl, nnb = self.mRGBACube.shape[0:3]
            nb, nl, ns = self.layerDims()

            rangeX = [int(ox + 1), int(ox + nns * sx)]
            rangeY = [int(oy + 1), int(oy + nnl * sy)]
            rangeZ = [int(ob + 1), int(ob + nnb * sb)]
            self.spinBoxX.setRange(*rangeX)
            self.spinBoxY.setRange(*rangeY)
            self.spinBoxZ.setRange(*rangeZ)

            self.spinBoxX.slider.setPageStep(int(nns * 0.1))
            self.spinBoxY.slider.setPageStep(int(nnl * 0.1))
            self.spinBoxZ.slider.setPageStep(int(nnb * 0.1))

        if True:
            # show subset extent range plot item
            box = gl.GLBoxItem(size=QVector3D(nns * sx, nnl * sx, nnb * sb))
            box.translate(ox, oy, ob)
            box.rotate(180, 1, 0, 0, local=False)
            box.setProperty(KEY_DEFAULT_TRANSFORM, box.transform())
            box.scale(1, 1, self.zScale())

            box.setVisible(self.glItemVisibility(GLItem.BoxSubset))
            self.setGLItemGroupItems(GLItem.BoxSubset, box)

    def drawCube(self):
        rgba = self.mRGBACube
        assert isinstance(rgba, np.ndarray)
        assert rgba.ndim == 4
        assert rgba.shape[3] == 4
        assert rgba.dtype == np.uint8

        t0 = time.time()

        ox, oy, ob, sx, sy, sb = self.subsetDimensions(self.rasterLayer(), self.mRGBACubeExtent, self.mRGBACube)

        # layer and cube dimensions
        nns, nnl, nnb = self.mRGBACube.shape[0:3]
        nb, nl, ns = self.layerDims()

        # x = x2*sx
        iBlock = 0
        if True:
            items = []
            isVisible = self.glItemVisibility(GLItem.Cube)
            stepX = stepY = 250
            stepZ = nnb

            x = 0
            while x < nns:
                x1 = x
                x2 = min(x1 + stepX, nns)
                y = 0
                while y < nnl:
                    y1 = y
                    y2 = min(y1 + stepY, nnl)
                    z = 0

                    while z < nnb:
                        z1 = z
                        z2 = min(z1 + stepZ, nnb)
                        block = rgba[x1:x2, y1:y2, z1:z2, :]

                        blockW, blockH = block.shape[0:2]
                        iBlock += 1
                        blockW *= sx  # width of block in px size of original layer resolution
                        blockH *= sy
                        # self.print('x:[{} {}], y:[{} {}], z:[{} {}]'.format(x,x2-1,y,y2-1,z,z2-1))
                        z = z2

                        # do not plot empty blocks
                        if np.all(block == 0):
                            continue
                        # block = np.flip(block, axis=2)
                        from OpenGL.GL import GL_ALPHA_TEST

                        glOptions = GLOptions['translucent']
                        glOptions[GL_ALPHA_TEST] = True
                        item = gl.GLVolumeItem(block, sliceDensity=self.sliceDensity(), smooth=self.smooth(),
                                               glOptions=glOptions)

                        # item.scale(sx, sy, sb)

                        offsetX = ox + x * sx
                        offsetY = oy + y * sy
                        item.scale(sx, sy, sb)
                        item.translate(offsetX, offsetY, 0, local=False)
                        item.rotate(180, 1, 0, 0, local=False)
                        item.setVisible(isVisible)
                        # item.rotate(180, 0, 0, 1, local=False)
                        # item.rotate(180, 0, 1, 0, local=False)
                        item.setProperty(KEY_DEFAULT_TRANSFORM, item.transform())

                        # scale to zScale
                        item.scale(1, 1, self.zScale())
                        # item.translate(0, 0, -z2 * sb * self.zScale())

                        if False:
                            if iBlock % 2 != 0:  # use this switch to exclude single blocks
                                items.append(item)
                        else:
                            items.append(item)

                    y = y2
                x = x2

            self.setGLItemGroupItems(GLItem.Cube, items)

    def drawSlice(self, key: GLItem):
        assert isinstance(key, GLItem)
        assert key in [GLItem.SliceX, GLItem.SliceY, GLItem.SliceZ]

        items = self.glItemGroupItems(key)
        if items:
            for item in items:
                self.glViewWidget().removeItem(item)

        rgba = self.mRGBACube
        if not isinstance(rgba, np.ndarray):
            return

        assert rgba.ndim == 4
        assert rgba.shape[3] == 4
        assert rgba.dtype == np.uint8

        t0 = time.time()

        ox, oy, ob, sx, sy, sb = self.subsetDimensions(self.rasterLayer(), self.mRGBACubeExtent, self.mRGBACube)

        # layer and cube dimensions
        nns, nnl, nnb = self.mRGBACube.shape[0:3]
        nb, nl, ns = self.layerDims()

        if nb is None or nnb is None:
            return

        # calculate indices xx, yy, zz to copy from 3D cube array
        xx0, xxe = 0, nns
        yy0, yye = 0, nnl
        zz0, zze = 0, nnb

        if key == GLItem.SliceX:
            if self.x() < ox or self.x() > ox + xxe * sx:
                return
            xx0 = min(int(self.x() / sx), nns - 1)
            xxe = xx0 + 1

        elif key == GLItem.SliceY:
            if self.y() < oy or self.y() > oy + yye * sy:
                return
            yy0 = min(int(self.y() / sy), nnl - 1)
            yye = yy0 + 1

        elif key == GLItem.SliceZ:
            if self.z() < ob or self.z() > ob + zze * sy:
                return

            zz0 = min(int(self.z() / sb), nnb - 1)
            zze = zz0 + 1

        # self.print('x: {} {}\ny: {} {}\nz:{} {}'.format(x0,x1,y0,y1,z0,z1))
        items = []
        isVisible = self.glItemVisibility(key)

        if True:  # print volumetric slice
            stepX = stepY = stepZ = 250
            xx1 = xx0
            while xx1 < xxe:
                xx2 = min(xx1 + stepX, xxe)
                yy1 = yy0
                while yy1 < yye:
                    yy2 = min(yy1 + stepY, yye)
                    zz1 = zz0
                    while zz1 < zze:
                        zz2 = min(zz1 + stepZ, zze)
                        self.print('GET BLOCK {}:{},{}:{},{}:{}'.format(xx1, xx2, yy1, yy2, zz1, zz2))
                        block = self.mRGBACube[xx1:xx2, yy1:yy2, zz1:zz2, :]

                        offsetX = ox + xx1 * sx
                        offsetY = oy + yy1 * sy
                        offsetZ = ob + zz1 * sb * self.zScale()
                        zz1 = zz2

                        # do not plot empty blocks
                        if np.all(block == 0):
                            continue

                        item = gl.GLVolumeItem(block, sliceDensity=self.sliceDensity(), smooth=self.smooth())
                        item.scale(sx, sy, sb)
                        item.setVisible(isVisible)

                        item.translate(offsetX, offsetY, offsetZ, local=False)
                        item.rotate(180, 1, 0, 0, local=False)
                        item.setProperty(KEY_DEFAULT_TRANSFORM, item.transform())
                        item.scale(1, 1, self.zScale())
                        if False:
                            if key == GLItem.SliceX:

                                item.scale(1, 1, self.zScale())
                            elif key == GLItem.SliceY:
                                # item.translate(offsetX, self.y(), offsetZ, local=False)
                                # item.rotate(180, 1, 0, 0)
                                item.setProperty(KEY_DEFAULT_TRANSFORM, item.transform())

                            elif key == GLItem.SliceZ:
                                # item.translate(offsetX, offsetY, self.z(), local=False)
                                # item.rotate(180, 1, 0, 0)
                                # item.rotate(180, 0, 1, 0)
                                item.setProperty(KEY_DEFAULT_TRANSFORM, item.transform())
                                item.scale(1, 1, self.zScale())
                                # item.translate(ns, 0, -self.z()*self.zScale())

                        items.append(item)
                    yy1 = yy2
                xx1 = xx2

            self.setGLItemGroupItems(key, items)

        self.print('{} ADDED {}'.format(key, time.time() - t0))

    def zScale(self) -> float:
        return self.doubleSpinBoxZScale.value()

    def setZScale(self, z: float):
        self.doubleSpinBoxZScale.setValue(z)

    def onZScaleChanged(self):
        z = self.zScale()
        nb, nl, ns = self.layerDims()
        for item in self.glViewWidget().items:
            assert isinstance(item, GLGraphicsItem)

            transformDefault = item.property(KEY_DEFAULT_TRANSFORM)
            key = item.property(KEY_GL_ITEM_GROUP)
            if isinstance(transformDefault, QMatrix4x4):
                if key == GLItem.SliceZ:

                    z = -self.z() * self.zScale()
                    transformDefault[2, 3] = z
                    item.setTransform(transformDefault)

                else:
                    item.setTransform(transformDefault)
                    item.scale(1, 1, z)  # scale will update the item

    def onLayerChanged(self, lyr):

        self.print('LAYER CHANGED')
        b = isinstance(lyr, QgsRasterLayer)

        toRemove = self.glViewWidget().items[:]
        for item in toRemove:
            # item._setView(None)
            self.glViewWidget().removeItem(item)
        self.progressBar.setValue(0)
        self.mRGBACube = None
        self.mRGBATopPlane = None
        self.print('LAYER CHANGED CLEANUP')
        if b:
            self.setWindowTitle(f'{NAME} {VERSION} - {lyr.name()}')
            nb = lyr.bandCount()
            ns = lyr.width()
            nl = lyr.height()

            minEdge = 0.1 * min(ns, nl)

            if nb < minEdge:
                self.mBandScaleFactor = minEdge / nb
            else:
                self.mBandScaleFactor = 1

            x = self.x()
            y = self.y()
            z = self.z()

            self.spinBoxX.setRange(1, ns)
            self.spinBoxY.setRange(1, nl)
            self.spinBoxZ.setRange(1, nb)

            self.setX(min(x, ns))
            self.setY(min(y, nl))
            self.setZ(min(z, nb))

            self.mCanvas.setLayers([lyr])

            self.setSpatialExtent(SpatialExtent.fromLayer(lyr))
            self.setTopPlaneRenderer(lyr.renderer().clone())

            # set slice renderer, optimize for band
            l2 = QgsRasterLayer(lyr.source())
            if not isinstance(self.sliceRenderer(), QgsRasterRenderer):
                band = self.z()
                renderer = QgsSingleBandGrayRenderer(l2.dataProvider(), band)
                l2.setRenderer(renderer)

            else:
                renderer = self.sliceRenderer()
                if isinstance(renderer, QgsSingleBandPseudoColorRenderer):
                    renderer.setBand(self.z())
                    l2.setRenderer(renderer)
                elif isinstance(renderer, QgsSingleBandGrayRenderer):
                    renderer.setGrayBand(self.z())
                    l2.setRenderer(renderer)
                elif isinstance(renderer, QgsMultiBandColorRenderer):
                    l2.setRenderer(QgsRasterLayer(l2.source(), '', l2.dataProvider().name()).renderer())

            l2.setContrastEnhancement(QgsContrastEnhancement.StretchToMinimumMaximum, QgsRasterMinMaxOrigin.MinMax)
            self.setSliceRenderer(l2.renderer().clone())

            w = self.glViewWidget()

            # w.addTextLabel(QVector3D(ns, 0, 0), 'x')
            # w.addTextLabel(QVector3D(0, -nl, 0), 'y')
            # w.addTextLabel(QVector3D(0, 0, -nb), 'bands')

            box = gl.GLBoxItem(size=QVector3D(ns, -nl, -nb))
            # box.translate(0, 0, nb)
            box.setProperty(KEY_DEFAULT_TRANSFORM, box.transform())
            box.scale(1, 1, self.zScale())
            box.setVisible(self.glItemVisibility(GLItem.Box))
            self.setGLItemGroupItems(GLItem.Box, box)

            # ax = gl.GLAxisItem(size=QVector3D(ns, -nl, -nb))
            ax = ImageCubeAxisItem(size=QVector3D(ns, -nl, -nb))

            # ax.translate(0, nl, nb)
            # ax.rotate(180, 0, 1, 0)
            ax.setProperty(KEY_DEFAULT_TRANSFORM, ax.transform())
            ax.scale(1, 1, self.zScale())
            ax.setVisible(self.glItemVisibility(GLItem.Axes))
            self.setGLItemGroupItems(GLItem.Axes, ax)

            # w = self.glViewWidget()
            # w.mTextLabels.clear()
            # w.addTextLabel(QVector3D(0, 0, 0), 'Bands')
            # w.addTextLabel(QVector3D(0, nl+1, nb), 'Lines')
            # w.addTextLabel(QVector3D(ns+1, 0, nb), 'Columns')

            self.resetCameraPosition()

            # for i in w.items:
            #    w.removeItem(i)

            # g = gl.GLGridItem(color='w')
            # w.addItem(g)

        else:
            self.mCanvas.setLayers([])
            self.spinBoxX.setRange(1, 1)
            self.spinBoxY.setRange(1, 1)
            self.spinBoxZ.setRange(1, 1)

            b = False
            self.mBandScaleFactor = 1

            self.setWindowTitle(f'{NAME} {VERSION} - <no raster layer selected>')

        for w in [self.gbRendering, self.gbPlotting, self.gbOpenGLOptions]:
            w.setEnabled(b)

        if self.onValidate():
            self.reloadData()

    def setRasterLayer(self, lyr: QgsRasterLayer):

        if isinstance(lyr, QgsRasterLayer):
            if lyr != self.rasterLayer():
                QgsProject.instance().addMapLayer(lyr)
                self.mMapLayerComboBox.setLayer(lyr)

        if lyr is None:
            self.mMapLayerComboBox.setLayer(None)
