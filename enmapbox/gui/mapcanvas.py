# -*- coding: utf-8 -*-
# noinspection PyPep8Naming
"""
***************************************************************************
    mapcanvas.py
    ---------------------
    Date                 : August 2017
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import os
import time
import typing
import warnings
from _weakrefset import WeakSet
from typing import List

from enmapbox import enmapboxSettings
from enmapbox.enmapboxsettings import EnMAPBoxSettings
from enmapbox.gui import MapTools, MapToolCenter, PixelScaleExtentMapTool, \
    CursorLocationMapTool, FullExtentMapTool, QgsMapToolAddFeature, QgsMapToolSelect, \
    CrosshairDialog, CrosshairStyle, CrosshairMapCanvasItem
from enmapbox.gui.mimedata import containsMapLayers, extractMapLayers
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint, SpatialExtent, qgisAppQgisInterface

from qgis.PyQt.QtCore import Qt, QObject, QCoreApplication, pyqtSignal, QEvent, QPointF, QMimeData, QTimer, QSize, \
    QModelIndex, QAbstractListModel
from qgis.PyQt.QtGui import QMouseEvent, QIcon, QDragEnterEvent, QDropEvent, QResizeEvent, QKeyEvent, QColor
from qgis.PyQt.QtWidgets import QAction, QToolButton, QFileDialog, QHBoxLayout, QFrame, QMenu, QLabel, QApplication, \
    QWidgetAction, QGridLayout, QSpacerItem, QSizePolicy, QDialog, QVBoxLayout, QComboBox
from qgis.core import QgsLayerTreeLayer, QgsCoordinateReferenceSystem, QgsRectangle, QgsMapLayerProxyModel, \
    QgsVectorLayerTools, \
    QgsMapLayer, QgsRasterLayer, QgsPointXY, \
    QgsProject, QgsMapSettings, QgsMapToPixel
from qgis.core import QgsVectorLayer, QgsLayerTree
from qgis.gui import QgsColorDialog, QgsLayerTreeMapCanvasBridge, QgsMapTool
from qgis.gui import QgsMapCanvas, QgisInterface, QgsMapToolZoom, QgsAdvancedDigitizingDockWidget, QgsMapLayerComboBox, \
    QgsProjectionSelectionWidget, QgsMapToolIdentify, QgsMapToolPan, QgsMapToolCapture, QgsMapMouseEvent

LINK_ON_SCALE = 'SCALE'
LINK_ON_CENTER = 'CENTER'
LINK_ON_CENTER_SCALE = 'CENTER_SCALE'
UNLINK = 'UNLINK'

N_MAX_GRP = 2

DEBUG = False

KEY_LAST_CLICKED = 'LAST_CLICKED'


class MapCanvasListModel(QAbstractListModel):
    def __init__(self, parent=None, mapCanvases=None):
        super(MapCanvasListModel, self).__init__(parent)

        self.mMapCanvases = []
        if mapCanvases:
            for m in mapCanvases:
                self.addMapCanvas(m)

    def __iter__(self):
        return self.mMapCanvases.__iter__()

    def __len__(self):
        return len(self.mMapCanvases)

    def mapCanvases(self):
        return self.mMapCanvases[:]

    def insertCanvases(self, canvases, i=None):
        assert isinstance(canvases, list)
        if i is None:
            i = len(self.mMapCanvases)
        canvases = [c for c in canvases if c not in self.mMapCanvases]
        if len(canvases) > 0:
            self.beginInsertRows(QModelIndex(), i, i + len(canvases) - 1)
            self.mMapCanvases.extend(canvases)
            for c in canvases:
                if isinstance(c, MapCanvas):
                    c.sigNameChanged.connect(lambda: self.onCanvasUpdate(c))
            self.endInsertRows()

    def removeCanvas(self, canvas):
        if isinstance(canvas, list):
            for c in canvas:
                self.removeCanvas(c)
        else:
            if isinstance(canvas, QgsMapCanvas) and canvas in self.mMapCanvases:
                idx = self.canvas2idx(canvas)
                self.beginRemoveRows(QModelIndex(), idx.row(), idx.row())
                self.mMapCanvases.remove(canvas)
                self.endRemoveRows()

    def onCanvasUpdate(self, canvas):
        if canvas in self.mMapCanvases:
            idx = self.canvas2idx(canvas)
            self.dataChanged.emit(idx, idx)

    def addMapCanvas(self, mapCanvas):
        self.insertCanvases([mapCanvas])

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.mMapCanvases)

    def columnCount(self, QModelIndex_parent=None, *args, **kwargs):
        return 1

    def idx2canvas(self, index):
        if index.isValid():
            return self.mMapCanvases[index.row()]
        return None

    def canvas2idx(self, canvas):
        return self.createIndex(self.mMapCanvases.index(canvas), 0)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if (index.row() >= len(self.mMapCanvases)) or (index.row() < 0):
            return None

        mapCanvas = self.idx2canvas(index)

        value = None
        if isinstance(mapCanvas, MapCanvas):
            if role == Qt.DisplayRole:
                value = '{}'.format(mapCanvas.name())
            if role == Qt.DecorationRole:
                value = QIcon()
            if role == Qt.UserRole:
                value = mapCanvas
        return value


class CanvasLinkDialog(QDialog):
    LINK_TYPES = [LINK_ON_CENTER_SCALE, LINK_ON_SCALE, LINK_ON_CENTER, UNLINK]

    @staticmethod
    def showDialog(parent=None, canvases=None):
        """
        Opens a Dialog to specify the map linking
        """
        from enmapbox.gui.enmapboxgui import EnMAPBox
        emb = EnMAPBox.instance()

        if canvases is None:
            canvases = emb.mapCanvases()
        if len(canvases) <= 1:
            return

        for c in canvases:
            assert isinstance(c, QgsMapCanvas)
        d = CanvasLinkDialog(parent=parent)
        d.addCanvas(canvases)
        d.setSourceCanvas(canvases[0])

        if isinstance(emb, EnMAPBox):
            emb.sigMapCanvasAdded.connect(d.addCanvas)
            emb.sigMapCanvasRemoved.connect(d.removeCanvas)
            emb.sigClosed.connect(d.close)

        d.show()

    def __init__(self, *args, **kwds):
        super(CanvasLinkDialog, self).__init__(*args, **kwds)

        self.setWindowIcon(QIcon(':/enmapbox/gui/ui/icons/enmapbox.svg'))
        self.setWindowTitle('Map Linking')
        self.setLayout(QVBoxLayout())

        self.grid = QGridLayout()
        self.cbSrcCanvas = QComboBox()
        self.cbSrcCanvas.currentIndexChanged.connect(self.onSourceCanvasChanged)
        self.mSrcCanvasModel = MapCanvasListModel()
        self.cbSrcCanvas.setModel(self.mSrcCanvasModel)

        self.mTargets = []
        hb = QHBoxLayout()
        hb.addWidget(QLabel('Link '))
        hb.addWidget(self.cbSrcCanvas)
        hb.addWidget(QLabel('with...'))
        hb.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.mWidgetLUT = dict()
        self.layout().addLayout(hb)
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)
        self.layout().addWidget(hline)
        self.layout().addLayout(self.grid)
        self.layout().addSpacing(0)

    def onSourceCanvasChanged(self):
        pass
        self.setSourceCanvas(self.currentSourceCanvas())
        s = ""

    def onTargetSelectionChanged(self):
        sender = self.sender()
        s = ""

    def addCanvas(self, canvas):

        if isinstance(canvas, list):
            for c in canvas:
                self.addCanvas(c)
        else:
            self.mSrcCanvasModel.addMapCanvas(canvas)

        # force a refresh of widgets
        src = self.currentSourceCanvas()
        self.setSourceCanvas(src)

    def removeCanvas(self, canvas):
        if isinstance(canvas, list):
            for c in canvas:
                self.removeCanvas(c)
        else:
            self.mSrcCanvasModel.removeCanvas(canvas)

            # force a refresh of widgets
            src = self.currentSourceCanvas()
            self.setSourceCanvas(src)

    def currentSourceCanvas(self):
        return self.cbSrcCanvas.itemData(self.cbSrcCanvas.currentIndex(), Qt.UserRole)

    def currentTargetCanvases(self):
        srcCanvas = self.currentSourceCanvas()
        return [trgCanvas for trgCanvas in self.mSrcCanvasModel.mapCanvases() if trgCanvas != srcCanvas]

    def setSourceCanvas(self, canvas):

        if not isinstance(canvas, QgsMapCanvas):
            return

        if canvas not in self.mSrcCanvasModel:
            self.addCanvas(canvas)

        srcCanvas = self.currentSourceCanvas()

        # create a widget for each target canvas
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.setParent(None)
            self.mWidgetLUT.clear()

        trgCanvases = self.currentTargetCanvases()

        if not isinstance(srcCanvas, MapCanvas):
            return

        def createButtonToAll(linkType, tooltip):
            a = CanvasLink.linkAction(None, None, linkType)
            a.setToolTip(tooltip)
            a.triggered.connect(lambda: self.linkToAll(linkType))
            btn1 = QToolButton()
            btn1.setDefaultAction(a)
            return btn1

        if len(trgCanvases) >= N_MAX_GRP:

            self.grid.addWidget(QLabel('All Canvases'), 0, 0)
            btn1 = createButtonToAll(LINK_ON_CENTER_SCALE, 'Link all canvases on center and scale.')
            btn2 = createButtonToAll(LINK_ON_SCALE, 'Link all canvases on scale.')
            btn3 = createButtonToAll(LINK_ON_CENTER, 'Link all canvases on center.')
            btn4 = createButtonToAll(UNLINK, 'Unlink all canvases.')
            self.grid.addWidget(QLabel('All Canvases'), 0, 0)
            btns = [btn1, btn2, btn3, btn4]
            for i, btn in enumerate(btns):
                self.grid.addWidget(btn, 0, i + 1)

        offset = self.grid.rowCount()
        for iRow, trgCanvas in enumerate(trgCanvases):
            iRow += offset
            assert isinstance(trgCanvas, MapCanvas)

            if isinstance(trgCanvas, MapCanvas):
                label = QLabel(trgCanvas.name())
                trgCanvas.sigNameChanged.connect(label.setText)

            elif isinstance(trgCanvas, QgsMapCanvas):
                import qgis.utils
                if isinstance(qgis.utils.iface, QgisInterface) and \
                        isinstance(qgis.utils.iface.mapCanvas(), QgsMapCanvas):
                    label = QLabel('QGIS Map Canvas')

            self.grid.addWidget(label, iRow, 0)
            btnDict = {}
            for iCol, linkType in enumerate(CanvasLinkDialog.LINK_TYPES):
                btn = QToolButton(self)
                btn.setObjectName('btn{}{}_{}'.format(srcCanvas.name(), trgCanvas.name(), linkType).replace(' ', '_'))
                a = CanvasLink.linkAction(srcCanvas, trgCanvas, linkType)
                assert isinstance(a, QAction)
                a.setCheckable(True)
                a.triggered.connect(self.updateLinkSelection)
                btn.setDefaultAction(a)
                self.grid.addWidget(btn, iRow, iCol + 1)
                btnDict[linkType] = btn

            self.mWidgetLUT[trgCanvas] = btnDict

            if iRow == 0:
                self.grid.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum), iRow, iCol + 1)
        self.grid.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), self.grid.rowCount(), 0)

        self.updateLinkSelection()

    def linkToAll(self, linkType):
        src = self.currentSourceCanvas()
        for trg in self.currentTargetCanvases():
            CanvasLink.linkMapCanvases(src, trg, linkType)
        self.updateLinkSelection()

    def updateLinkSelection(self, *args):
        srcCanvas = self.currentSourceCanvas()
        assert isinstance(srcCanvas, MapCanvas)

        targetCanvases = self.mWidgetLUT.keys()
        for targetCanvas in targetCanvases:
            link = CanvasLink.between(srcCanvas, targetCanvas)
            if isinstance(link, CanvasLink):
                linkType = link.linkType
            else:
                linkType = UNLINK

            if linkType not in self.mWidgetLUT[targetCanvas].keys():
                s = ""

            for btnLinkType, btn in self.mWidgetLUT[targetCanvas].items():
                assert isinstance(btn, QToolButton)
                a = btn.defaultAction()
                a.setChecked(linkType == btnLinkType)

    def onButtonPressed(self, btnList, srcCanvas, targetCanvas, linkType):
        sender = self.sender()
        CanvasLink.linkMapCanvases(srcCanvas, targetCanvas, linkType)

        for btn in btnList:
            assert isinstance(btn, QToolButton)
            if btn == sender:
                s = ""
                # todo: highlight activated function
            else:
                s = ""
                # todo: de-highlight activated function

    pass


class CanvasLinkTargetWidget(QFrame):

    def __init__(self, canvas1, canvas2):
        assert isinstance(canvas1, QgsMapCanvas)
        assert isinstance(canvas2, QgsMapCanvas)

        QFrame.__init__(self, parent=canvas2)
        self.canvas1 = canvas1
        self.canvas2 = canvas2
        # self.canvas1.installEventFilter(self)
        self.canvas2.installEventFilter(self)
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        self.setCursor(Qt.ArrowCursor)

        ly = QHBoxLayout()
        # add buttons with link functions
        self.buttons = list()

        for linkType in [LINK_ON_CENTER_SCALE, LINK_ON_SCALE, LINK_ON_CENTER]:
            bt = QToolButton(self)
            bt.setDefaultAction(CanvasLink.linkAction(self.canvas1, self.canvas2, linkType))
            self.buttons.append(bt)

        btStyle = """
        QToolButton { /* all types of tool button */
        border: 2px solid #8f8f91;
        border-radius: 6px;
        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f6f7fa, stop: 1 #dadbde);
        }

        QToolButton[popupMode="1"] { /* only for MenuButtonPopup */
            padding-right: 20px; /* make way for the popup button */
        }

        QToolButton:pressed {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #dadbde, stop: 1 #f6f7fa);
        }"""

        for bt in self.buttons:
            bt.setAttribute(Qt.WA_PaintOnScreen)
            bt.setStyleSheet(btStyle)
            bt.setIconSize(QSize(100, 100))
            bt.setAutoRaise(True)
            ly.addWidget(bt)

        self.layout.addLayout(ly, 0, 0)
        self.setStyleSheet('background-color:rgba(125, 125, 125, 125);')
        self.setAttribute(Qt.WA_PaintOnScreen)

        self.updatePosition()

    def updatePosition(self):
        if hasattr(self.parent(), 'viewport'):
            parentRect = self.parent().viewport().rect()

        else:
            parentRect = self.parent().rect()

        if not parentRect:
            return

        # get map center
        x = int(parentRect.width() / 2 - self.width() / 2)
        y = int(parentRect.height() / 2 - self.height() / 2)

        mw = int(min([self.width(), self.height()]) * 0.9)
        mw = min([mw, 120])
        for bt in self.buttons:
            bt.setIconSize(QSize(mw, mw))

        # self.setGeometry(x, y, self.width(), self.height())
        self.setGeometry(parentRect)

    def setParent(self, parent):
        self.updatePosition()
        return super(CanvasLinkTargetWidget, self).setParent(parent)

    def resizeEvent(self, event):
        super(CanvasLinkTargetWidget, self).resizeEvent(event)
        self.updatePosition()

    def showEvent(self, event):
        self.updatePosition()
        return super(CanvasLinkTargetWidget, self).showEvent(event)

    def eventFilter(self, obj, event):

        if event.type() == QEvent.Resize:
            self.updatePosition()
        return False

    def mousePressEvent(self, ev):

        if ev.button() == Qt.RightButton:
            # no choice, remove Widgets
            CanvasLink.RemoveMapLinkTargetWidgets(True)
            ev.accept()


class CanvasLink(QObject):
    """
    A CanvasLink describes how two MapCanvas are linked to each other.
    """
    LINKTYPES = [LINK_ON_SCALE, LINK_ON_CENTER, LINK_ON_CENTER_SCALE]
    LINK_ON_SCALE = LINK_ON_SCALE
    LINK_ON_CENTER = LINK_ON_CENTER
    LINK_ON_CENTER_SCALE = LINK_ON_CENTER_SCALE
    UNLINK = UNLINK
    GLOBAL_LINK_LOCK = False

    @staticmethod
    def ShowMapLinkTargets(mapDockOrMapCanvas):
        from enmapbox.gui.dataviews.docks import MapDock
        if isinstance(mapDockOrMapCanvas, MapDock):
            mapDockOrMapCanvas = mapDockOrMapCanvas.mCanvas
        assert isinstance(mapDockOrMapCanvas, QgsMapCanvas)

        canvas1 = mapDockOrMapCanvas
        assert isinstance(canvas1, QgsMapCanvas)
        CanvasLink.RemoveMapLinkTargetWidgets(True)

        for canvas_source in MapCanvas.instances():
            if canvas_source != canvas1:
                w = CanvasLinkTargetWidget(canvas1, canvas_source)
                w.setAutoFillBackground(False)
                w.show()
                CanvasLink.LINK_TARGET_WIDGETS.add(w)
                # canvas_source.freeze()
            s = ""

        s = ""

    @staticmethod
    def linkMapCanvases(canvas1, canvas2, linktype):
        """
        Use this function to link or unlink two MapCanvases
        :param canvas1: MapCanvas
        :param canvas2: MapCanvas
        :param linktype: str

        """
        # from enmapbox.gui.mapcanvas import CanvasLink
        if linktype in [UNLINK, None]:
            CanvasLink.unlinkMapCanvases(canvas1, canvas2)
        else:
            CanvasLink(canvas1, canvas2, linktype)

        CanvasLink.RemoveMapLinkTargetWidgets()

    @staticmethod
    def unlinkMapCanvases(canvas1, canvas2):
        if isinstance(canvas1, MapCanvas):
            canvas1.removeCanvasLink(canvas2)
        if isinstance(canvas2, MapCanvas):
            canvas2.removeCanvasLink(canvas1)
        CanvasLink.RemoveMapLinkTargetWidgets()

    @staticmethod
    def RemoveMapLinkTargetWidgets(processEvents=True):
        for w in list(CanvasLink.LINK_TARGET_WIDGETS):
            CanvasLink.LINK_TARGET_WIDGETS.remove(w)
            p = w.parent()
            w.hide()
            del (w)
            p.refresh()
            p.update()

        if processEvents:
            # qApp.processEvents()
            QCoreApplication.instance().processEvents()

    @staticmethod
    def resetLinkLock():
        CanvasLink.GLOBAL_LINK_LOCK = False

    @staticmethod
    def linkAction(canvas1, canvas2, linkType):
        """
        Create a QAction object with icon and description to be used in UIs
        :param linkType: see [LINK_ON_SCALE, LINK_ON_CENTER, LINK_ON_CENTER_SCALE]
        :return: QAction
        """
        assert linkType in [LINK_ON_SCALE, LINK_ON_CENTER, LINK_ON_CENTER_SCALE, UNLINK]

        if linkType == LINK_ON_CENTER:
            a = QAction('Link map center', None)

            a.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_center.svg'))
            a.setToolTip('Link map center')
        elif linkType == LINK_ON_SCALE:
            a = QAction('Link map scale ("Zoom")', None)
            a.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_mapscale.svg'))
            a.setToolTip('Link to scale between both maps')
        elif linkType == LINK_ON_CENTER_SCALE:
            a = QAction('Link map scale and center', None)
            a.setToolTip('Link map scale and center')
            a.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_mapscale_center.svg'))
        elif linkType == UNLINK:
            a = QAction('Unlink', None)
            a.setToolTip('Removes an existing link between both canvases')
            a.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_open.svg'))
        else:
            raise Exception('Unknown link type : {}'.format(linkType))

        if isinstance(canvas1, QgsMapCanvas) and isinstance(canvas2, QgsMapCanvas):
            a.triggered.connect(lambda: CanvasLink.linkMapCanvases(canvas1, canvas2, linkType))
        return a

    LINK_TARGET_WIDGETS = set()

    def __init__(self, canvas1, canvas2, linkType):
        super(CanvasLink, self).__init__()
        assert linkType in CanvasLink.LINKTYPES, linkType
        assert isinstance(canvas1, MapCanvas)
        assert isinstance(canvas2, MapCanvas)
        assert canvas1 != canvas2

        if linkType == UNLINK:
            CanvasLink.unlinkMapCanvases(canvas1, canvas2)
        else:

            self.linkType = linkType
            self.canvases = [canvas1, canvas2]

            canvas1.addCanvasLink(self)
            canvas2.addCanvasLink(self)

            self.applyTo(canvas2)

    def removeMe(self):
        """Call this to remove this think from both canvases."""
        self.canvases[0].removeCanvasLink(self)

    @staticmethod
    def existsBetween(canvas1, canvas2):
        return CanvasLink.between(canvas1, canvas2) is not None

    @staticmethod
    def between(canvas1, canvas2):
        if not (isinstance(canvas1, QgsMapCanvas) and isinstance(canvas2, QgsMapCanvas)):
            return False
        links = []
        if isinstance(canvas1, MapCanvas):
            links.extend([lyr for lyr in canvas1.canvasLinks() if lyr.containsCanvas(canvas2)])
        if isinstance(canvas2, MapCanvas):
            links.extend([lyr for lyr in canvas2.canvasLinks() if lyr.containsCanvas(canvas1)])

        links = list(set(links))
        nl = len(links)
        if nl > 1:
            raise Exception('More than two CanvasLinks between {} and {}'.format(canvas1, canvas2))
        if nl == 1:
            return links[0]
        return None

    @staticmethod
    def applyLinking(initialSrcCanvas):
        """
        Applies all link actions related to MapCanvas "initialSrcCanvas"
        :param initialSrcCanvas: MapCanvas
        """
        if CanvasLink.GLOBAL_LINK_LOCK:
            # do not disturb ongoing linking by starting a new one
            return
        else:
            CanvasLink.GLOBAL_LINK_LOCK = True
            QTimer.singleShot(500, lambda: CanvasLink.resetLinkLock())

            # G0(A) -> G1(B) -> G3(E)
            #      -> G1(C) -> G3(A)
            #               -> G3(E)
            # Gx = Generation. G1 will be set before G2,...
            # A,B,..,E = MapCanvas Instances
            # Order of linking starting from A: B,C,E
            # Note: G3(A) will be not set, as A is already handled (initial signal)
            #      G3(E) receives link from G1(B) only.
            #      change related signals in-between will be blocked by GLOBAL_LINK_LOCK

            handledCanvases = [initialSrcCanvas]

            def nextLinkGeneration(srcCanvases: list):
                nonlocal handledCanvases

                generations = dict()
                for srcCanvas in srcCanvases:
                    assert isinstance(srcCanvas, MapCanvas)
                    linksToApply = []
                    for link in srcCanvas.mCanvasLinks:
                        assert isinstance(link, CanvasLink)
                        dstCanvas = link.theOtherCanvas(srcCanvas)
                        if dstCanvas not in handledCanvases:
                            linksToApply.append(link)
                    if len(linksToApply) > 0:
                        generations[srcCanvas] = linksToApply
                return generations

            nextGenerations = nextLinkGeneration(handledCanvases)

            while len(nextGenerations) > 0:
                # get the links that have to be set for the next generation
                assert isinstance(nextGenerations, dict)
                for srcCanvas, links in nextGenerations.items():
                    assert isinstance(srcCanvas, MapCanvas)
                    assert isinstance(links, list)

                    for link in links:
                        assert isinstance(link, CanvasLink)
                        dstCanvas = link.theOtherCanvas(srcCanvas)
                        assert dstCanvas not in handledCanvases
                        assert dstCanvas == link.apply(srcCanvas, dstCanvas)
                        handledCanvases.append(dstCanvas)
                nextGenerations.clear()
                nextGenerations.update(nextLinkGeneration(handledCanvases))

            CanvasLink.GLOBAL_LINK_LOCK = False

    def containsCanvas(self, canvas):
        return canvas in self.canvases

    def theOtherCanvas(self, canvas):
        assert canvas in self.canvases
        assert len(self.canvases) == 2
        return self.canvases[1] if canvas == self.canvases[0] else self.canvases[0]

    def unlink(self):
        for canvas in self.canvases:
            canvas.removeCanvasLink(self)

    def icon(self):

        if self.linkType == LINK_ON_SCALE:
            src = ":/enmapbox/gui/ui/icons/link_mapscale.svg"
        elif self.linkType == LINK_ON_CENTER:
            src = ":/enmapbox/gui/ui/icons/link_center.svg"
        elif self.linkType == LINK_ON_CENTER_SCALE:
            src = ":/enmapbox/gui/ui/icons/link_mapscale_center.svg"
        elif self.linkType == UNLINK:
            src = ":/enmapbox/gui/ui/icons/link_open.svg"
        else:
            raise NotImplementedError('unknown link type: {}'.format(self.linkType))

        return QIcon(src)

    def apply(self, srcCanvas: QgsMapCanvas, dstCanvas: QgsMapCanvas) -> QgsMapCanvas:
        """
        Applies the linking between src and dst canvas
        :param srcCanvas: QgsMapCanvas
        :param dstCanvas: QgsMapCanvas
        :return: dstCanvas QgsMapCanvas
        """
        assert isinstance(srcCanvas, QgsMapCanvas)
        assert isinstance(dstCanvas, QgsMapCanvas)

        srcCrs = srcCanvas.mapSettings().destinationCrs()
        srcExt = SpatialExtent.fromMapCanvas(srcCanvas)

        assert isinstance(srcExt, SpatialExtent)

        # original center and extent
        centerSrc = SpatialPoint.fromMapCanvasCenter(srcCanvas)
        centerDst = SpatialPoint.fromMapCanvasCenter(dstCanvas)

        # transform (T) to target CRS
        dstCrs = dstCanvas.mapSettings().destinationCrs()
        extentT = srcExt.toCrs(dstCrs)

        assert isinstance(extentT, SpatialExtent), \
            'Unable to transform {} from {} to {}'.format(srcExt.asWktCoordinates(), srcCrs.description(),
                                                          dstCrs.description())

        centerT = SpatialPoint(srcExt.crs(), srcExt.center())

        srcWidth, srcHeight = srcCanvas.width(), srcCanvas.height()
        if srcWidth == 0:
            srcWidth = max([5, dstCanvas.width()])
        if srcHeight == 0:
            srcHeight = max([5, dstCanvas.height()])

        mapUnitsPerPx_x = extentT.width() / srcWidth
        mapUnitsPerPx_y = extentT.height() / srcHeight

        scaledWidth = mapUnitsPerPx_x * dstCanvas.width()
        scaledHeight = mapUnitsPerPx_y * dstCanvas.height()
        scaledBoxCenterDst = SpatialExtent(dstCrs, scaledWidth, scaledHeight).setCenter(centerDst)
        scaledBoxCenterSrc = SpatialExtent(dstCrs, scaledWidth, scaledHeight).setCenter(centerSrc.toCrs(dstCrs))
        if self.linkType == LINK_ON_CENTER:
            dstCanvas.setCenter(centerT)

        elif self.linkType == LINK_ON_SCALE:

            dstCanvas.zoomToFeatureExtent(scaledBoxCenterDst)

        elif self.linkType == LINK_ON_CENTER_SCALE:
            dstCanvas.zoomToFeatureExtent(scaledBoxCenterSrc)

        else:
            raise NotImplementedError()
        dstCanvas.refresh()
        return dstCanvas

    def applyTo(self, canvasTo: QgsMapCanvas):
        assert isinstance(canvasTo, QgsMapCanvas)
        canvasFrom = self.theOtherCanvas(canvasTo)
        return self.apply(canvasFrom, canvasTo)

    def isSameCanvasPair(self, canvasLink):
        """
        Returns True if canvasLink contains the same canvases
        :param canvasLink:
        :return:
        """
        assert isinstance(canvasLink, CanvasLink)
        b = self.canvases[0] in canvasLink.canvases and \
            self.canvases[1] in canvasLink.canvases
        return b

    def __eq__(self, canvasLink):
        if not isinstance(canvasLink, CanvasLink):
            return False
        return self.isSameCanvasPair(canvasLink)

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        cs = list(self.canvases)
        return 'CanvasLink "{}" {} <-> {}'.format(self.linkType, cs[0], cs[1])


class MapCanvasMapTools(QObject):
    def __init__(self, canvas: QgsMapCanvas,
                 cadDock: QgsAdvancedDigitizingDockWidget):

        super(MapCanvasMapTools, self).__init__(canvas)
        self.mCanvas = canvas
        self.mCadDock = cadDock

        self.mtZoomIn = QgsMapToolZoom(canvas, False)
        self.mtZoomOut = QgsMapToolZoom(canvas, True)
        self.mtMoveToCenter = MapToolCenter(canvas)
        self.mtPan = QgsMapToolPan(canvas)
        self.mtPixelScaleExtent = PixelScaleExtentMapTool(canvas)
        self.mtFullExtentMapTool = FullExtentMapTool(canvas)
        self.mtCursorLocation = CursorLocationMapTool(canvas, True)
        self.mtAddFeature = QgsMapToolAddFeature(canvas, QgsMapToolCapture.CaptureNone, cadDock)
        self.mtSelectFeature = QgsMapToolSelect(canvas)

    def mapTools(self) -> List[QgsMapTool]:
        maptools = []
        for k, v in self.__dict__.items():
            if isinstance(v, QgsMapTool):
                maptools.append(v)
        return maptools

    def setVectorLayerTools(self, vectorLayerTools: QgsVectorLayerTools):
        """
        Sets the VectorLayerTools of an GUI application
        """
        self.mtAddFeature.setVectorLayerTools(vectorLayerTools)

    def activate(self, mapToolKey, **kwds):

        if mapToolKey == MapTools.ZoomIn:
            self.mCanvas.setMapTool(self.mtZoomIn)
        elif mapToolKey == MapTools.ZoomOut:
            self.mCanvas.setMapTool(self.mtZoomOut)
        elif mapToolKey == MapTools.Pan:
            self.mCanvas.setMapTool(self.mtPan)
        elif mapToolKey == MapTools.ZoomFull:
            self.mCanvas.setMapTool(self.mtFullExtentMapTool)
        elif mapToolKey == MapTools.ZoomPixelScale:
            self.mCanvas.setMapTool(self.mtPixelScaleExtent)
        elif mapToolKey == MapTools.CursorLocation:
            self.mCanvas.setMapTool(self.mtCursorLocation)
        elif mapToolKey == MapTools.SpectralProfile:
            pass
        elif mapToolKey == MapTools.TemporalProfile:
            pass
        elif mapToolKey == MapTools.MoveToCenter:
            self.mCanvas.setMapTool(self.mtMoveToCenter)
        elif mapToolKey == MapTools.AddFeature:
            self.mCanvas.setMapTool(self.mtAddFeature)
        elif mapToolKey == MapTools.SelectFeature:
            self.mCanvas.setMapTool(self.mtSelectFeature)

            s = ""

        else:

            print('Unknown MapTool key: {}'.format(mapToolKey))


class MapCanvas(QgsMapCanvas):
    _instances: WeakSet = WeakSet()

    @staticmethod
    def instances():
        return list(MapCanvas._instances)

    sigSpatialExtentChanged = pyqtSignal(object)
    sigCrsChanged = pyqtSignal(QgsCoordinateReferenceSystem)

    sigNameChanged = pyqtSignal(str)
    sigCanvasLinkAdded = pyqtSignal(CanvasLink)
    sigCanvasLinkRemoved = pyqtSignal(CanvasLink)
    sigCrosshairPositionChanged = pyqtSignal(object)

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.contextMenuAboutToShow.connect(self.populateContextMenu)
        self.setExtent(QgsRectangle(-1, -1, 1, 1))
        settings = EnMAPBoxSettings()
        self.setCanvasColor(settings.value(EnMAPBoxSettings.MAP_BACKGROUND, type=QColor))

        i = 1
        existing_names = [c._id for c in MapCanvas.instances()]
        while (name := f'MapCanvas.#{i}') in existing_names:
            i += 1
        self._id = name

        self.setWindowTitle(self._id)
        self.setProperty(KEY_LAST_CLICKED, time.time())
        self.acceptDrops()

        self.mCanvasBridge: QgsLayerTreeMapCanvasBridge = None
        self.mCrosshairItem = CrosshairMapCanvasItem(self)

        self.setCrosshairVisibility(False)

        # init the map tool set
        self.mCadDock = QgsAdvancedDigitizingDockWidget(self)
        self.mCadDock.setVisible(False)
        self.mMapTools = MapCanvasMapTools(self, self.mCadDock)

        self.mCanvasLinks: List[CanvasLink] = []
        # register signals to react on changes
        self.scaleChanged.connect(self.onScaleChanged)
        self.extentsChanged.connect(self.onExtentsChanged)

        self.destinationCrsChanged.connect(lambda: self.sigCrsChanged.emit(self.mapSettings().destinationCrs()))
        # activate default map tool
        self.setMapTool(self.mMapTools.mtPan)
        self.mMapMouseEvent = None
        MapCanvas._instances.add(self)

    def canvasLinks(self) -> List[CanvasLink]:
        return self.mCanvasLinks[:]

    def mousePressEvent(self, event: QMouseEvent):

        self.setProperty(KEY_LAST_CLICKED, time.time())
        set_cursor_location: bool = event.button() == Qt.LeftButton and \
            isinstance(self.mapTool(), (QgsMapToolIdentify, CursorLocationMapTool))

        super(MapCanvas, self).mousePressEvent(event)

        if set_cursor_location:
            ms = self.mapSettings()
            pointXY = ms.mapToPixel().toMapCoordinates(event.x(), event.y())
            spatialPoint = SpatialPoint(ms.destinationCrs(), pointXY)
            self.setCrosshairPosition(spatialPoint)

    def setCrosshairPosition(self, spatialPoint: SpatialPoint, emitSignal: bool = True):
        """
        Sets the position of the Crosshair.
        :param spatialPoint: SpatialPoint
        :param emitSignal: True (default). Set False to avoid emitting sigCrosshairPositionChanged
        :return:
        """
        point = spatialPoint.toCrs(self.mapSettings().destinationCrs())
        self.mCrosshairItem.setPosition(point)
        if emitSignal:
            self.sigCrosshairPositionChanged[object].emit(point)

    def mouseMoveEvent(self, event):
        self.mMapMouseEvent = QgsMapMouseEvent(self, event)
        return super(MapCanvas, self).mouseMoveEvent(event)

    def resizeEvent(self, event: QResizeEvent):
        self.setScaleLocked(True)
        super().resizeEvent(event)
        self.setScaleLocked(False)

    def refresh(self, force=False):

        self.setRenderFlag(True)
        if self.renderFlag() or force:
            super(MapCanvas, self).refresh()
            # super(MapCanvas, self).refreshAllLayers()

    def crs(self) -> QgsCoordinateReferenceSystem:
        return self.mapSettings().destinationCrs()

    def mapTools(self) -> MapCanvasMapTools:
        """
        Returns the map tools
        :return: MapCanvasMapTools
        """
        return self.mMapTools

    def populateContextMenu(self, menu: QMenu, event: QgsMapMouseEvent):
        """
        Populates a context menu with actions for applicable MapCanvas operations
        """
        if event is None:
            pt = QPointF(self.width() * 0.5, self.height() * 0.5)
            event = QMouseEvent(QEvent.MouseButtonPress, pt, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
            event = QgsMapMouseEvent(self, event)
        assert isinstance(menu, QMenu)
        assert isinstance(event, QgsMapMouseEvent)
        mapSettings = self.mapSettings()
        assert isinstance(mapSettings, QgsMapSettings)
        pos = event.pos()
        pointGeo = mapSettings.mapToPixel().toMapCoordinates(pos.x(), pos.y())
        assert isinstance(pointGeo, QgsPointXY)
        spatialPoint = SpatialPoint(mapSettings.destinationCrs(), pointGeo)

        action = menu.addAction('Link with other maps')
        action.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_basic.svg'))
        action.triggered.connect(lambda: CanvasLink.ShowMapLinkTargets(self))
        action = menu.addAction('Remove links to other maps')
        action.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_open.svg'))
        action.triggered.connect(lambda: self.removeAllCanvasLinks())

        qgisApp = qgisAppQgisInterface()
        b = isinstance(qgisApp, QgisInterface)
        menu.addSeparator()
        m = menu.addMenu('QGIS...')
        m.setIcon(QIcon(r':/images/themes/default/providerQgis.svg'))
        action = m.addAction('Use map center')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: self.setCenter(SpatialPoint.fromMapCanvasCenter(qgisApp.mapCanvas())))

        action = m.addAction('Set map center')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: qgisApp.mapCanvas().setCenter(
                self.spatialCenter().toCrs(qgisApp.mapCanvas().mapSettings().destinationCrs())))

        action = m.addAction('Use map extent')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: self.setExtent(SpatialExtent.fromMapCanvas(qgisApp.mapCanvas())))

        action = m.addAction('Set map extent')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: qgisApp.mapCanvas().setExtent(
                self.spatialExtent().toCrs(qgisApp.mapCanvas().mapSettings().destinationCrs())))

        menu.addSeparator()
        m = menu.addMenu('Crosshair')

        if self.crosshairIsVisible():
            action = m.addAction('Hide')
            action.triggered.connect(lambda: self.setCrosshairVisibility(False))
        else:
            action = m.addAction('Show')
            action.triggered.connect(lambda: self.setCrosshairVisibility(True))

        action = m.addAction('Style')
        action.triggered.connect(lambda: self.setCrosshairStyle(
            CrosshairDialog.getCrosshairStyle(
                crosshairStyle=self.crosshairStyle(), mapCanvas=self
            )
        ))

        mPxGrid = m.addMenu('Pixel Grid')
        if self.mCrosshairItem.crosshairStyle().mShowPixelBorder:
            action = mPxGrid.addAction('Hide')
            action.triggered.connect(lambda: self.mCrosshairItem.crosshairStyle().setShowPixelBorder(False))

        mPxGrid.addSeparator()

        rasterLayers = [lyr for lyr in self.layers() if isinstance(lyr, QgsRasterLayer) and lyr.isValid()]

        def onShowRasterGrid(layer: QgsRasterLayer):
            self.mCrosshairItem.setVisibility(True)
            self.mCrosshairItem.crosshairStyle().setShowPixelBorder(True)
            self.mCrosshairItem.setRasterGridLayer(layer)

        actionTop = mPxGrid.addAction('Top Raster')
        actionBottom = mPxGrid.addAction('Bottom Raster')

        if len(rasterLayers) == 0:
            actionTop.setEnabled(False)
            actionBottom.setEnabled(False)
        else:
            actionTop.triggered.connect(lambda b, layer=rasterLayers[0]: onShowRasterGrid(layer))
            actionBottom.triggered.connect(lambda b, layer=rasterLayers[-1]: onShowRasterGrid(layer))

        mPxGrid.addSeparator()
        wa = QWidgetAction(mPxGrid)

        cb = QgsMapLayerComboBox()
        cb.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb.setAllowEmptyLayer(True)

        # keep the list short an focus on

        # list each source only once
        all_layers = QgsProject.instance().mapLayers().values()
        all_layers = sorted(all_layers, key=lambda l: not l.title().startswith('[EnMAP-Box]'))

        excepted_layers = []
        sources = []
        for lyr in all_layers:
            if lyr.source() in sources:
                excepted_layers.append(lyr)
            else:
                sources.append(lyr.source())
        cb.setExceptedLayerList(excepted_layers)

        for i in range(cb.count()):
            lyr = cb.layer(i)
            if lyr == self.mCrosshairItem.rasterGridLayer():
                cb.setCurrentIndex(i)
                break
        cb.layerChanged.connect(onShowRasterGrid)
        wa.setDefaultWidget(cb)
        mPxGrid.addAction(wa)

        # action.triggered.connect(lambda b, layer=l: onShowRasterGrid(layer))

        menu.addSeparator()

        action = menu.addAction('Zoom Full')
        action.setIcon(QIcon(':/images/themes/default/mActionZoomFullExtent.svg'))
        action.triggered.connect(self.zoomToFullExtent)

        action = menu.addAction('Zoom Native Resolution')
        action.setIcon(QIcon(':/images/themes/default/mActionZoomActual.svg'))
        action.setEnabled(any([lyr for lyr in self.layers() if isinstance(lyr, QgsRasterLayer)]))
        action.triggered.connect(lambda: self.zoomToPixelScale(spatialPoint=spatialPoint))

        menu.addSeparator()

        m = menu.addMenu('Save to...')
        action = m.addAction('PNG')
        action.triggered.connect(lambda: self.saveMapImageDialog('PNG'))
        action = m.addAction('JPEG')
        action.triggered.connect(lambda: self.saveMapImageDialog('JPG'))
        action = m.addAction('Clipboard')
        action.triggered.connect(lambda: QApplication.clipboard().setPixmap(self.pixmap()))
        action = menu.addAction('Copy layer paths')
        action.triggered.connect(lambda: QApplication.clipboard().setText('\n'.join(self.layerPaths())))

        menu.addSeparator()

        action = menu.addAction('Refresh')
        action.setIcon(QIcon(":/qps/ui/icons/refresh_green.svg"))
        action.triggered.connect(lambda: self.refresh())

        action = menu.addAction('Refresh all layers')
        action.setIcon(QIcon(":/qps/ui/icons/refresh_green.svg"))
        action.triggered.connect(lambda: self.refreshAllLayers())

        action = menu.addAction('Clear')
        action.triggered.connect(self.clearLayers)

        menu.addSeparator()
        action = menu.addAction('Set CRS...')
        action.triggered.connect(self.setCRSfromDialog)

        action = menu.addAction('Set background color')
        action.triggered.connect(self.setBackgroundColorFromDialog)

        action = menu.addAction('Show background layer')
        action.triggered.connect(self.setBackgroundLayer)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        emb = EnMAPBox.instance()
        node = self.layerTree()
        if isinstance(emb, EnMAPBox) and isinstance(node, QgsLayerTree):

            slws = emb.spectralLibraryWidgets()
            if len(slws) > 0:
                m = menu.addMenu('Add Spectral Library')
                for slw in slws:
                    speclib = slw.speclib()
                    if isinstance(speclib, QgsVectorLayer):
                        a = m.addAction(speclib.name())
                        a.setToolTip(speclib.source())
                        a.triggered.connect(lambda *args, sl=speclib, n=node: node.insertLayer(0, sl))
        menu.addSeparator()

        return menu

    def clearLayers(self, *args):
        tree = self.layerTree()
        from enmapbox.gui.dataviews.dockmanager import MapDockTreeNode
        if isinstance(tree, MapDockTreeNode):
            layers = self.layers()
            for lyr in layers:
                node = tree.findLayer(lyr)
                if isinstance(node, QgsLayerTreeLayer):
                    node.setItemVisibilityChecked(False)
        else:
            self.setLayers([])

    def layerTree(self) -> typing.Optional['MapDockTreeNode']:  # noqa: F821
        """
        Returns the MapDockTreeNode that is linked to this MapCanvas by a QgsLayerTreeMapCanvasBridge.
        Can be None
        :return: QgsLayerTree
        """
        if isinstance(self.mCanvasBridge, QgsLayerTreeMapCanvasBridge):
            return self.mCanvasBridge.rootGroup()

        return None

    def keyPressEvent(self, e: QKeyEvent):

        is_panning = bool(QApplication.mouseButtons() & Qt.MiddleButton)
        is_ctrl = bool(QApplication.keyboardModifiers() & Qt.ControlModifier)
        is_shift = bool(QApplication.keyboardModifiers() & Qt.ShiftModifier)

        if not is_panning and is_ctrl and e.key() in [Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down]:
            # find raster layer with a reference pixel grid
            rasterLayer: QgsRasterLayer = self.mCrosshairItem.rasterGridLayer()
            if not isinstance(rasterLayer, QgsRasterLayer):
                for lyr in self.layers():
                    if isinstance(lyr, QgsRasterLayer):
                        rasterLayer = lyr
                        break

            if isinstance(rasterLayer, QgsRasterLayer):
                # get the pixel grid cell at canvas center  in canvas coordinates
                self.mCrosshairItem.isVisible()
                settings: QgsMapSettings = self.mapSettings()
                canvasCrs: QgsCoordinateReferenceSystem = settings.destinationCrs()
                layerCrs: QgsCoordinateReferenceSystem = rasterLayer.crs()

                # ptA = SpatialPoint.fromMapCanvasCenter(self)
                ptA = SpatialPoint(canvasCrs, self.mCrosshairItem.mPosition).toCrs(layerCrs)
                if not isinstance(ptA, SpatialPoint):
                    return

                dx = rasterLayer.rasterUnitsPerPixelX()
                dy = rasterLayer.rasterUnitsPerPixelY()

                ptB: SpatialPoint = None
                if e.key() == Qt.Key_Left:
                    ptB = SpatialPoint(canvasCrs, ptA.x() - dx, ptA.y())
                elif e.key() == Qt.Key_Right:
                    ptB = SpatialPoint(canvasCrs, ptA.x() + dx, ptA.y())
                elif e.key() == Qt.Key_Up:
                    ptB = SpatialPoint(canvasCrs, ptA.x(), ptA.y() + dy)
                elif e.key() == Qt.Key_Down:
                    ptB = SpatialPoint(canvasCrs, ptA.x(), ptA.y() - dy)
                else:
                    raise NotImplementedError()

                ptR = ptB.toCrs(canvasCrs)

                if not isinstance(ptR, SpatialPoint):
                    super(MapCanvas, self).keyPressEvent(e)
                    return

                if isinstance(ptB, QgsPointXY):
                    # self.setCenter(ptB)
                    self.mCrosshairItem.setPosition(ptR)
                    m2p: QgsMapToPixel = settings.mapToPixel()
                    localPos = m2p.transform(ptR)

                    # simulate a left-button mouse-click
                    event = QMouseEvent(QEvent.MouseButtonPress, localPos.toQPointF(), Qt.LeftButton, Qt.LeftButton,
                                        Qt.NoModifier)
                    self.mousePressEvent(event)

                    event = QMouseEvent(QEvent.MouseButtonRelease, localPos.toQPointF(), Qt.LeftButton,
                                        Qt.LeftButton, Qt.NoModifier)
                    self.mouseReleaseEvent(event)
                    self.keyPressed.emit(e)

                    return

        super(MapCanvas, self).keyPressEvent(e)

    def layerPaths(self) -> typing.List[str]:
        """
        Returns the paths/URIs of presented QgsMapLayers
        :return:
        """
        return [lyr.source() for lyr in self.layers()]

    def pixmap(self):
        """
        Returns the current map image as pixmap
        :return: QPixmap
        """
        # deprectated
        # return QPixmap(self.map().contentImage().copy())
        return self.grab()

    def saveMapImageDialog(self, fileType):

        settings = enmapboxSettings()
        lastDir = settings.value('EMB_SAVE_IMG_DIR', os.path.expanduser('~'))
        path = os.path.join(lastDir, 'screenshot.{}'.format(fileType.lower()))

        path, filter = QFileDialog.getSaveFileName(self, 'Save map as {}'.format(fileType), path)

        if len(path) > 0:
            self.saveAsImage(path, None, fileType)
            settings.setValue('EMB_SAVE_IMG_DIR', os.path.dirname(path))

    def setCRSfromDialog(self, *args):
        """
        Opens a dialog to specify the QgsCoordinateReferenceSystem
        :param args:
        """
        setMapCanvasCRSfromDialog(self)

    def setBackgroundColorFromDialog(self, *args):
        setMapCanvasBackgroundColorFromDialog(self, self.canvasColor())

    def setBackgroundLayer(self):
        #  Once we have project settings, the user could setup his global background layer manually.
        # For now use Google Maps as default.

        backgroundLayer = QgsRasterLayer(
            'type=xyz&url=https://mt1.google.com/vt/lyrs%3Dm%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0',
            'Google Maps', 'wms'
        )
        self.layerTree().addLayer(backgroundLayer)

    def setCanvasBridge(self, bridge: QgsLayerTreeMapCanvasBridge):
        assert isinstance(bridge, QgsLayerTreeMapCanvasBridge)
        assert bridge.mapCanvas() == self
        self.mCanvasBridge = bridge

    def setCrosshairStyle(self, crosshairStyle: CrosshairStyle):
        """
        Sets the crosshair style
        :param crosshairStyle: CrosshairStyle
        """
        if isinstance(crosshairStyle, CrosshairStyle):
            self.mCrosshairItem.setCrosshairStyle(crosshairStyle)

    def crosshairStyle(self) -> CrosshairStyle:
        """
        Returns the CrosshairStyle
        :return: CrosshairStyle
        """
        return self.mCrosshairItem.mCrosshairStyle

    def setShowCrosshair(self, b):
        warnings.warn('Use setCrosshairVisibility', DeprecationWarning)
        self.setCrosshairVisibility(b)

    def setCrosshairVisibility(self, b: bool):
        self.mCrosshairItem.setVisibility(b)

    def crosshairIsVisible(self) -> bool:
        return self.mCrosshairItem.mShow

    def onScaleChanged(self, scale):
        CanvasLink.applyLinking(self)
        pass

    def onExtentsChanged(self):
        CanvasLink.applyLinking(self)
        self.sigSpatialExtentChanged.emit(SpatialExtent.fromMapCanvas(self))

    def fullExtent(self) -> QgsRectangle:
        # workaround https://github.com/qgis/QGIS/issues/43097
        return self.mapSettings().fullExtent()

    def zoomToProjectExtent(self) -> None:

        if self.extent().isNull():
            for lyr in self.layers():
                if lyr.crs().isValid():
                    self.zoomToFullExtent()
                    break
        else:
            super().zoomToProjectExtent()

    def zoomToFeatureExtent(self, spatialExtent):
        assert isinstance(spatialExtent, SpatialExtent)
        self.setExtent(spatialExtent)

    def setWindowTitle(self, name: str):
        b = self.windowTitle() != name
        super(MapCanvas, self).setWindowTitle(name)
        if b:
            self.sigNameChanged.emit(self.windowTitle())

    def setName(self, name):
        self.setWindowTitle(name)

    def name(self):
        return self.windowTitle()

    def zoomToPixelScale(self, spatialPoint: SpatialPoint = None, layer: QgsRasterLayer = None):
        if layer is not None:
            layers = [layer]
        else:
            layers = self.layers()

        for lyr in layers:
            if isinstance(lyr, QgsRasterLayer):
                if isinstance(spatialPoint, SpatialPoint):
                    if not lyr.extent().contains(spatialPoint.toCrs(lyr.crs())):
                        continue
                self.mMapTools.mtPixelScaleExtent.setRasterLayer(lyr)

    def __str__(self):
        return self._id

    # forward to MapDock
    def dragEnterEvent(self, event):
        mimeData = event.mimeData()
        assert isinstance(mimeData, QMimeData)

        # check mime types we can handle
        assert isinstance(event, QDragEnterEvent)
        if containsMapLayers(mimeData):
            event.setDropAction(Qt.CopyAction)  # copy but do not remove
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """

        :param event: QDropEvent
        """

        if event.dropAction() in [Qt.CopyAction, Qt.MoveAction]:
            mimeData = event.mimeData()
            assert isinstance(mimeData, QMimeData)

            # add map layers
            mapLayers = extractMapLayers(mimeData, project=self.project())
            to_add = []
            for lyr in mapLayers:
                if lyr in self.layers() and lyr.providerType() != 'memory':
                    lyr = lyr.clone()
                to_add.append(lyr)

            if len(to_add) > 0:
                # if this canvas is linked to a QgsLayerTree, add new layer to the TOC, not the canvas instance.
                layerTree = self.layerTree()
                if isinstance(layerTree, QgsLayerTree):
                    for lyr in reversed(to_add):
                        layerTree.insertLayer(0, lyr)
                else:
                    self.setLayers(to_add + self.layers())

            event.accept()

    def setExtent(self, rectangle):
        """
        Sets the map extent
        :param rectangle: QgsRectangle or SpatialExtent (CRS differences will be considered)
        """
        if isinstance(rectangle, SpatialExtent):
            rectangle = rectangle.toCrs(self.mapSettings().destinationCrs())

        super(MapCanvas, self).setExtent(rectangle)
        self.setRenderFlag(True)

    def spatialExtent(self) -> SpatialExtent:
        """
        Returns the map extent as SpatialExtent (extent + CRS)
        :return: SpatialExtent
        """
        return SpatialExtent.fromMapCanvas(self)

    def spatialCenter(self) -> SpatialPoint:
        """
        Returns the map center as SpatialPoint (QgsPointXY + CRS)
        :return: SpatialPoint
        """
        return SpatialPoint.fromMapCanvasCenter(self)

    def createCanvasLink(self, otherCanvas: QgsMapCanvas, linkType) -> CanvasLink:
        assert isinstance(otherCanvas, MapCanvas)
        return self.addCanvasLink(CanvasLink(self, otherCanvas, linkType))

    def addCanvasLink(self, canvasLink: CanvasLink) -> CanvasLink:
        assert isinstance(canvasLink, CanvasLink)
        toRemove = [cLink for cLink in self.mCanvasLinks if cLink.isSameCanvasPair(canvasLink)]
        for cLink in toRemove:
            self.removeCanvasLink(cLink)
        self.mCanvasLinks.append(canvasLink)
        self.sigCanvasLinkAdded.emit(canvasLink)
        return canvasLink

    def removeCanvasLink(self, canvasLink):
        """
        Removes the link to another canvas
        :param canvasLink: CanvasLink or QgsMapCanvas that might be connect to this MapCanvas.
        """
        if isinstance(canvasLink, QgsMapCanvas):
            toRemove = [lyr for lyr in self.mCanvasLinks if lyr.containsCanvas(canvasLink)]
            for cl in toRemove:
                self.removeCanvasLink(cl)

        if canvasLink in self.mCanvasLinks:
            self.mCanvasLinks.remove(canvasLink)
            self.sigCanvasLinkRemoved.emit(canvasLink)

    def removeAllCanvasLinks(self):
        toRemove = self.mCanvasLinks[:]
        for cLink in toRemove:
            for canvas in cLink.canvases:
                canvas.removeCanvasLink(cLink)

    def setLayers(self, mapLayers: typing.List[QgsMapLayer]):
        """
        Sets the list of mapLayers to show in the map canvas
        :param mapLayers: QgsMapLayer or [list-of-QgsMapLayers]
        :return: self
        """
        if not isinstance(mapLayers, list):
            mapLayers = [mapLayers]

        project = self.project()
        if isinstance(project, QgsProject):
            self.project().addMapLayers(mapLayers, False)

        super(MapCanvas, self).setLayers(mapLayers)


def setMapCanvasCRSfromDialog(mapCanvas, crs: QgsCoordinateReferenceSystem = None):
    assert isinstance(mapCanvas, QgsMapCanvas)
    w = QgsProjectionSelectionWidget(mapCanvas)
    if crs is None:
        crs = mapCanvas.mapSettings().destinationCrs()
    else:
        crs = QgsCoordinateReferenceSystem(crs)
    # set current CRS
    # w.setMessage('Define a map CRS')
    w.setCrs(crs)
    w.setLayerCrs(crs)
    w.setShowAccuracyWarnings(True)
    w.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.CrsNotSet, True)
    w.crsChanged.connect(mapCanvas.setDestinationCrs)
    w.selectCrs()
    return w


def setMapCanvasBackgroundColorFromDialog(mapCanvas: QgsMapCanvas, color: QColor = None):
    dialog = QgsColorDialog(mapCanvas)
    dialog.setColor(color)
    if dialog.exec() == QgsColorDialog.Accepted:
        mapCanvas.setCanvasColor(dialog.color())
