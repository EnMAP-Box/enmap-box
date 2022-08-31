# -*- coding: utf-8 -*-

"""
***************************************************************************
    reclassify.py

    Algorithms to reclassify raster classification images
    ---------------------
    Date                 : Juli 2017
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
import pathlib
import re
import typing
from difflib import SequenceMatcher

from osgeo import gdal

from enmapbox import enmapboxSettings
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.qgispluginsupport.qps.classification.classificationscheme import \
    ClassificationMapLayerComboBox, ClassInfo, ClassificationScheme, ClassificationSchemeComboBox, \
    ClassificationSchemeWidget
from enmapbox.qgispluginsupport.qps.utils import loadUi
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import QgsProviderRegistry, QgsRasterLayer, QgsProject, QgsMapLayerProxyModel
from qgis.gui import QgsFileWidget, QgsRasterFormatSaveOptionsWidget, QgsMapLayerComboBox
from . import APP_DIR

SETTINGS_KEY = 'ENMAPBOX_RECLASSIFY_APP'
SAVE_DIR_KEY = SETTINGS_KEY + '/SAVE_DIR'
KEY_DST_RASTER = SETTINGS_KEY + 'DST_RASTER'


def setClassInfo(targetDataset, classificationScheme, bandIndex=0):
    assert isinstance(classificationScheme, ClassificationScheme)

    classNames = classificationScheme.classNames()
    ct = gdal.ColorTable()
    assert isinstance(ct, gdal.ColorTable)
    for i, color in enumerate(classificationScheme.classColors()):
        assert isinstance(color, QColor)
        ct.SetColorEntry(color.toRgb())

    if isinstance(targetDataset, gdal.Dataset):
        ds = targetDataset
    else:
        ds = gdal.Open(targetDataset, gdal.GA_Update)

    assert isinstance(ds, gdal.Dataset)
    assert bandIndex >= 0 and ds.RasterCount > bandIndex
    band = ds.GetRasterBand(bandIndex + 2)
    assert isinstance(band, gdal.Band)
    band.SetCategoryNames(classNames)
    band.SetColorTable(ct)


def reclassify(pathSrc: str, pathDst: str, dstClassScheme: ClassificationScheme, labelLookup: dict,
               drvDst=None,
               bandIndices=0, tileSize=None, co=None):
    """
    Internal wrapper to reclassify raster images based on hub-flow API.
    :param pathSrc: str, path of source image
    :param pathDst: str, path of destination image
    :param dstClassScheme: ClassificationScheme
    :param labelLookup: dict() as lookup table
    :param drvDst: gdal.Driver with driver of output image
    :param bandIndices: - not used -
    :param tileSize: - not used -
    :param co: - not used -
    :return: gdal.Dataset of written re-classified image
    """
    # assert os.path.isfile(pathSrc)
    assert isinstance(dstClassScheme, ClassificationScheme)
    assert isinstance(labelLookup, dict)

    # hubflow requires to handle the `unclassified` class (label = 0, always first position) separately

    MAP2HUBFLOW = dict()
    for c in dstClassScheme:
        MAP2HUBFLOW[c.label()] = c
    if 0 not in MAP2HUBFLOW.keys():
        MAP2HUBFLOW[0] = ClassInfo(label=0, name='Unclassified', color='black')

    names = []
    colors = []
    labels = []
    for l in sorted(list(MAP2HUBFLOW.keys())):
        classInfo: ClassInfo = MAP2HUBFLOW[l]
        names.append(classInfo.name())
        colors.append(classInfo.color().name())
        labels.append(l)

    if len(names) == 0:
        return

    import _classic.hubflow.core
    classification = _classic.hubflow.core.Classification(pathSrc)

    newDef = _classic.hubflow.core.ClassDefinition(names=names[1:], colors=colors[1:], ids=labels[1:])
    newDef.setNoDataNameAndColor(names[0], colors[0])

    classification.reclassify(filename=pathDst,
                              classDefinition=newDef,
                              mapping=labelLookup.copy())
    pathQml = os.path.splitext(pathDst)[0] + '.qml'
    loptions = QgsRasterLayer.LayerOptions(loadDefaultStyle=False)
    lyr = QgsRasterLayer(pathDst, options=loptions)
    renderer = dstClassScheme.rasterRenderer()
    renderer.setInput(lyr.dataProvider())
    lyr.setRenderer(renderer)
    lyr.saveNamedStyle(pathQml)
    ds = gdal.Open(pathDst)
    if isinstance(ds, gdal.Dataset):
        ds.GetFileList()  # resolve issue 410 (or similar)

    return ds


class ReclassifyTableModel(QAbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.mColumNames = ['From', 'To']
        self.mDst: ClassificationScheme = ClassificationScheme()
        self.mSrc: ClassificationScheme = ClassificationScheme()
        self.mMapping: typing.Dict[ClassInfo, ClassInfo] = dict()

    def resetMapping(self, *args):
        self.beginResetModel()
        self.mMapping.clear()
        self.endResetModel()

    def writeCSV(self, path: pathlib.Path):
        if path is None:

            filter = "CSV Files (*.csv *.txt);;" \
                     "All Files (*)"

            def_dir = enmapboxSettings().value(SAVE_DIR_KEY, None)
            path, ext = QFileDialog.getSaveFileName(caption='Save Class Mapping', filter=filter, directory=def_dir)
            if path == '':
                return
            else:
                enmapboxSettings().setValue(SAVE_DIR_KEY, os.path.dirname(path))

        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        assert isinstance(path, pathlib.Path)

        lines = ['#Source Class; Destination Class']
        for src, dst in self.mMapping.items():
            lines.append(f'{src.name()};{dst.name()}')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def readCSV(self, path: pathlib.Path, reset: bool = True):
        if path is None:
            filter = "CSV Files (*.csv *.txt);;" \
                     "All Files (*)"

            def_dir = enmapboxSettings().value(SAVE_DIR_KEY, None)
            path, ext = QFileDialog.getOpenFileName(caption='Read Class Mapping', filter=filter, directory=def_dir)
            if path == '':
                return
            else:
                enmapboxSettings().setValue(SAVE_DIR_KEY, os.path.dirname(path))

        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        assert isinstance(path, pathlib.Path) and path.is_file()

        allowedSrcNames = self.mSrc.classNames()
        allowedSrcLabels = [str(l) for l in self.mSrc.classLabels()]

        allowedDstNames = self.mDst.classNames()
        allowedDstLabels = [str(l) for l in self.mDst.classLabels()]

        if reset:
            self.resetMapping()

        with open(path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines()]
            rx = re.compile(r'^(?P<src>[^#;]+);(?P<dst>[^#;]+)$')
            rxInt = re.compile(r'^\d+$')

            for line in lines:
                match = rx.search(line)
                if match:
                    srcTxt = match.group('src')
                    dstTxt = match.group('dst')

                    srcClass = dstClass = None

                    if srcTxt in allowedSrcNames:
                        srcClass = self.mSrc[allowedSrcNames.index(srcTxt)]
                    elif srcTxt in allowedSrcLabels:
                        srcClass = self.mSrc[allowedSrcLabels.index(srcTxt)]
                    else:
                        continue
                    if dstTxt in allowedDstNames:
                        dstClass = self.mDst[allowedDstNames.index(dstTxt)]
                    elif dstTxt in allowedDstLabels:
                        dstClass = self.mDst[allowedDstLabels.index(dstTxt)]
                    else:
                        continue

                    assert isinstance(srcClass, ClassInfo)
                    assert isinstance(dstClass, ClassInfo)

                    idx = self.mSrc.classInfo2index(srcClass)
                    self.mMapping[srcClass] = dstClass
                    idx0 = self.createIndex(idx.row(), 0)
                    idx1 = self.createIndex(idx.row(), self.columnCount())
                    self.dataChanged.emit(idx0, idx1)

    def matchClassNames(self):
        LUT = dict()

        dstNames = list(set(self.mDst.classNames()))
        srcNames = list(set(self.mSrc.classNames()))

        if len(dstNames) == 0 or len(srcNames) == 0:
            return

        for srcName in srcNames:
            similarity = [SequenceMatcher(None, dstName, srcName).ratio() for dstName in dstNames]
            sMax = max(similarity)
            if sMax > 0.75:
                LUT[srcName] = dstNames[similarity.index(sMax)]

        for srcName, dstName in LUT.items():
            i = self.mSrc.classNames().index(srcName)
            j = self.mDst.classNames().index(dstName)
            self.mMapping[self.mSrc[i]] = self.mDst[j]

    def setDestination(self, cs: ClassificationScheme):
        assert isinstance(cs, ClassificationScheme)

        self.beginResetModel()
        if isinstance(self.mDst, ClassificationScheme):
            try:
                self.mDst.sigClassesRemoved.disconnect(self.onDestinationClassesRemoved)
                self.mDst.dataChanged.disconnect(self.onDestinationDataChanged)
            except:
                pass

        self.mDst = cs
        self.mDst.sigClassesRemoved.connect(self.onDestinationClassesRemoved)
        self.mDst.dataChanged.connect(self.onDestinationDataChanged)
        self.mMapping.clear()
        # match similar class names
        if isinstance(self.mSrc, ClassificationScheme):
            # match on similar names
            self.matchClassNames()
        self.endResetModel()

    def destination(self) -> ClassificationScheme:
        return self.mDst

    def setSource(self, cs: ClassificationScheme):
        assert isinstance(cs, ClassificationScheme)

        self.beginResetModel()

        oldSrc = self.mSrc
        self.mSrc = cs
        self.mMapping.clear()
        if isinstance(oldSrc, ClassificationScheme):
            self.matchClassNames()
            try:
                oldSrc.sigClassesRemoved.disconnect(self.onSourceClassesRemoved)
                self.mSrc.dataChanged.disconnect(self.onSourceDataChanged)
            except:
                pass
        self.mSrc.sigClassesRemoved.connect(self.onSourceClassesRemoved)
        self.mSrc.dataChanged.connect(self.onSourceDataChanged)

        self.endResetModel()

    def onSourceDataChanged(self, idx0, idx1, roles):

        a = self.index(idx0.row(), 0)
        b = self.index(idx1.row(), 0)

        self.dataChanged.emit(a, b, roles)

    def onDestinationDataChanged(self, a, b, roles):
        a = self.index(0, 1)
        b = self.index(self.rowCount() - 1, 1)
        self.dataChanged.emit(a, b, roles)

    def onSourceClassesRemoved(self):
        to_remove = [s for s in self.mMapping.keys() if s not in self.mDst]
        for s in to_remove:
            self.mMapping.pop(s)

    def onDestinationClassesRemoved(self):
        dst = self.destination()
        to_remove = []
        for s, d in self.mMapping.items():
            if d not in dst:
                to_remove.append(s)
        for s in to_remove:
            self.mMapping.pop(s)
        pass

    def source(self) -> ClassificationScheme:
        return self.mSrc

    def rowCount(self, parent=None, *args, **kwargs):
        if not isinstance(self.mSrc, ClassificationScheme):
            return 0
        else:
            return len(self.mSrc)

    def summary(self) -> dict:
        s = dict()
        s['dstClassScheme'] = self.destination()
        LUT = dict()
        for c1, c2 in self.mMapping.items():
            LUT[c1.label()] = c2.label()
        s['labelLookup'] = LUT
        return s

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.mColumNames)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.mColumNames[section]
        return super(ReclassifyTableModel, self).headerData(section, orientation, role)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        col = index.column()
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if col == 1:
            flags |= Qt.ItemIsEditable
        return flags

    def classDisplayName(self, c: ClassInfo) -> str:
        return f'{c.label()} "{c.name()}"'

    def classToolTip(self, c: ClassInfo) -> str:
        return f'Value: {c.label()}\n' \
               f'Name: "{c.name()}"'

    def data(self, index: QModelIndex, role=None):

        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if col == 0:
            idx0 = self.mSrc.index(row, 0)
            c = self.mSrc[row]
            assert isinstance(c, ClassInfo)
            if role == Qt.DisplayRole:
                return self.classDisplayName(c)
            elif role == Qt.ToolTipRole:
                return f'Source Class\n' + self.classToolTip(c)
            elif role == Qt.DecorationRole:
                return c.icon()

        if col == 1:
            srcClass: ClassInfo = self.mSrc[row]
            dstClass: ClassInfo = self.mMapping.get(srcClass, None)
            if isinstance(dstClass, ClassInfo):
                if role == Qt.DisplayRole:
                    return self.classDisplayName(dstClass)
                elif role == Qt.ToolTipRole:
                    return f'Destination Class\n' + self.classToolTip(dstClass)

                elif role == Qt.DecorationRole:
                    return dstClass.icon()

        return None

    def setData(self, index: QModelIndex, value, role=None):
        if not index.isValid():
            return False

        col = index.column()
        row = index.row()

        srcClass = self.mSrc[row]

        b = False
        if col == 1 and role == Qt.EditRole and isinstance(value, ClassInfo):
            if value in self.mDst[:]:
                self.mMapping[srcClass] = value
        if b:
            self.dataChanged.emit(index, index, [role])
        return b


class ReclassifyTableView(QTableView):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        model: ReclassifyTableModel = self.model().sourceModel()
        m = QMenu()
        a = m.addAction('Load Class Mapping')
        a.triggered.connect(lambda *args: model.readCSV(None))

        a = m.addAction('Save Class Mapping')
        a.triggered.connect(lambda *args: model.writeCSV(None))

        a = m.addAction('Reset Class Mapping')
        a.triggered.connect(model.resetMapping)
        m.exec_(event.globalPos())


class ReclassifyTableViewDelegate(QStyledItemDelegate):
    """

    """

    def __init__(self, tableView: QTableView, parent=None):
        assert isinstance(tableView, QTableView)
        super(ReclassifyTableViewDelegate, self).__init__(parent=parent)
        self.mTableView = tableView

    def sortFilterProxyModel(self) -> QSortFilterProxyModel:
        return self.mTableView.model()

    def reclassifyModel(self) -> ReclassifyTableModel:
        return self.sortFilterProxyModel().sourceModel()

    def setItemDelegates(self, tableView: QTableView):
        model = self.reclassifyModel()
        tableView.setItemDelegateForColumn(1, self)

    def createEditor(self, parent, option, index):
        pmodel = self.sortFilterProxyModel()
        tmodel = self.reclassifyModel()
        w = None
        tIdx = pmodel.mapToSource(index)
        assert isinstance(tIdx, QModelIndex)

        if index.isValid() and isinstance(tmodel, ReclassifyTableModel):
            if tIdx.column() == 1:
                w = ClassificationSchemeComboBox(classification=tmodel.destination(), parent=parent)
        return w

    def checkData(self, index, w, value):
        assert isinstance(index, QModelIndex)
        tModel = self.reclassifyModel()
        if index.isValid() and isinstance(tModel, ReclassifyTableModel):
            #  todo: any checks?
            self.commitData.emit(w)

    def setEditorData(self, editor, proxyIndex):

        tModel = self.reclassifyModel()
        index = self.sortFilterProxyModel().mapToSource(proxyIndex)
        assert isinstance(index, QModelIndex)

        if index.isValid() and isinstance(tModel, ReclassifyTableModel):
            if index.column() == 1:
                assert isinstance(editor, ClassificationSchemeComboBox)
                c = index.data(Qt.UserRole)
                editor.setCurrentClassInfo(c)

    def setModelData(self, w, bridge, proxyIndex):
        index = self.sortFilterProxyModel().mapToSource(proxyIndex)
        assert isinstance(index, QModelIndex)
        tModel = self.reclassifyModel()
        if index.isValid() and isinstance(tModel, ReclassifyTableModel):
            if index.column() == 1 and isinstance(w, ClassificationSchemeComboBox):
                tModel.setData(index, w.currentClassInfo(), Qt.EditRole)


class ReclassifyDialog(QDialog):
    """Constructor."""

    def __init__(self, parent=None):
        super(ReclassifyDialog, self).__init__(parent, Qt.Window)
        path = pathlib.Path(__file__).parent / 'reclassifydialog.ui'
        loadUi(path, self)

        assert isinstance(self.mapLayerComboBox, ClassificationMapLayerComboBox)
        assert isinstance(self.tableView, QTableView)
        assert isinstance(self.dstClassificationSchemeWidget, ClassificationSchemeWidget)

        self.mModel = ReclassifyTableModel()
        self.mProxyModel = QSortFilterProxyModel()
        self.mProxyModel.setSourceModel(self.mModel)
        self.tableView.setModel(self.mProxyModel)
        self.mTableViewDelegate = ReclassifyTableViewDelegate(self.tableView)
        self.mTableViewDelegate.setItemDelegates(self.tableView)

        self.mapLayerComboBox.setAllowEmptyLayer(True)
        self.mapLayerComboBox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        excluded = [p for p in QgsProviderRegistry.instance().providerList() if p not in ['gdal']]
        self.mapLayerComboBox.setExcludedProviders(excluded)
        self.mapLayerComboBox.setShowCrs(False)

        # now define all the logic behind the UI which can not be defined in the QDesigner
        assert isinstance(self.dstFileWidget, QgsFileWidget)
        self.dstFileWidget.setStorageMode(QgsFileWidget.SaveFile)
        self.dstFileWidget.setConfirmOverwrite(True)
        dst_path = enmapboxSettings().value(KEY_DST_RASTER, None)
        if isinstance(dst_path, str):
            self.dstFileWidget.setFilePath(dst_path)

        assert isinstance(self.widgetOutputOptions, QgsRasterFormatSaveOptionsWidget)
        self.widgetOutputOptions.setType(QgsRasterFormatSaveOptionsWidget.Full)
        self.widgetOutputOptions.setProvider('gdal')
        self.widgetOutputOptions.setFormat('GTIFF')
        self.widgetOutputOptions.setRasterFileName('reclassifified.tif')
        self.gbOutputOptions.setVisible(False)  # hide, as long it is not connected
        self.dstFileWidget.fileChanged.connect(self.widgetOutputOptions.setRasterFileName)
        self.dstFileWidget.fileChanged.connect(self.onDestinationRasterChanged)
        # self.dstClassificationSchemeWidget.classificationScheme().sigClassesAdded.connect(self.refreshTransformationTable)
        # self.dstClassificationSchemeWidget.classificationScheme().sigClassesRemoved.connect(self.refreshTransformationTable)

        self.mDstClassSchemeInitialized = False

        self.mapLayerComboBox.layerChanged.connect(self.onSourceRasterChanged)
        self.mapLayerComboBox.currentIndexChanged.connect(self.validate)

        self.btnSelectSrcfile.setDefaultAction(self.actionAddRasterSource)
        self.dstFileWidget.fileChanged.connect(self.validate)

        def onAddRaster(*args):
            filter = QgsProviderRegistry.instance().fileRasterFilters()
            file, filter = QFileDialog.getOpenFileName(filter=filter)

            if len(file) > 0:
                self.setSrcRasterLayer(file)

        self.actionLoadClassMapping.triggered.connect(lambda: self.mModel.readCSV(None))
        self.actionSaveClassMapping.triggered.connect(lambda: self.mModel.writeCSV(None))
        self.btnLoadClassMapping.setDefaultAction(self.actionLoadClassMapping)
        self.btnSaveClassMapping.setDefaultAction(self.actionSaveClassMapping)
        self.actionAddRasterSource.triggered.connect(onAddRaster)
        self.onSourceRasterChanged()

    def onDestinationRasterChanged(self):

        dst_path = self.dstFileWidget.filePath()
        if isinstance(dst_path, str):
            enmapboxSettings().setValue(KEY_DST_RASTER, dst_path)

    def onSourceRasterChanged(self):
        lyr = self.mapLayerComboBox.currentLayer()
        cs_final = ClassificationScheme()
        if isinstance(lyr, QgsRasterLayer):
            cs = ClassificationScheme.fromMapLayer(lyr)
            if isinstance(cs, ClassificationScheme) and len(cs) > 0:
                cs_final = cs
                if not self.mDstClassSchemeInitialized:
                    self.setDstClassificationScheme(cs.clone())
                    self.mDstClassSchemeInitialized = True

        self.mModel.setSource(cs_final)
        self.validate()

    def setDstClassificationPath(self, path: str):
        """
        Sets the output path.
        :param path:
        :return:
        """
        assert isinstance(self.dstFileWidget, QgsFileWidget)
        self.dstFileWidget.setFilePath(path)

    def setDstClassificationScheme(self, classScheme: ClassificationScheme):
        """
        Sets the destination ClassificationScheme
        :param classScheme: path of classification file or ClassificationScheme
        """
        if isinstance(classScheme, str) and os.path.isfile(classScheme):
            classScheme = ClassificationScheme.fromRasterImage(classScheme)
        classScheme = classScheme.clone()
        self.dstClassificationSchemeWidget.setClassificationScheme(classScheme)
        self.mModel.setDestination(self.dstClassificationSchemeWidget.classificationScheme())

    def dstClassificationScheme(self) -> ClassificationScheme:
        """
        Returns the targeted classification scheme.
        :return: ClassificationScheme
        """
        return self.dstClassificationSchemeWidget.classificationScheme()

    def setDstRaster(self, path: str):
        """
        Sets the output path
        :param path: str
        """
        self.dstFileWidget.setFilePath(path)

    def dstRaster(self) -> str:
        """
        Returns the destination raster path
        :return: str
        """
        return self.dstFileWidget.filePath()

    def srcRasterLayer(self) -> QgsRasterLayer:
        lyr = self.mapLayerComboBox.currentLayer()
        if isinstance(lyr, QgsRasterLayer):
            return lyr
        else:
            return None

    def selectSource(self, src: str):
        """
        Selects the raster
        :param src:
        :return:
        """
        assert isinstance(self.mapLayerComboBox, QgsMapLayerComboBox)
        for i in [self.mapLayerComboBox.findText(src), self.mapLayerComboBox.findData(src)]:
            if i > -1:
                self.mapLayerComboBox.setCurrentIndex(i)

    def setSrcRasterLayer(self, src: QgsRasterLayer) -> bool:
        """
        Adds a new source raster
        :param src: object
        :return:
        """
        assert isinstance(src, QgsRasterLayer)
        QgsProject.instance().addMapLayer(src)
        assert isinstance(self.mapLayerComboBox, QgsMapLayerComboBox)
        for i in range(self.mapLayerComboBox.count()):
            if self.mapLayerComboBox.layer(i) == src:
                self.mapLayerComboBox.setCurrentIndex(i)
                return True
        return False

    def srcClassificationScheme(self) -> ClassificationScheme:
        """
        Reuturns the ClassificationScheme of the selected source raster
        :return: ClassificationScheme
        """
        lyr = self.srcRasterLayer()
        if isinstance(lyr, QgsRasterLayer):
            return ClassificationScheme.fromMapLayer(lyr)
        else:
            return None

    def createClassInfoComboBox(self, classScheme):
        assert isinstance(classScheme, ClassificationScheme)
        box = ClassificationSchemeComboBox(classification=classScheme)
        box.setAutoFillBackground(True)

        return box

    def validate(self):
        """
        Validates GUI inputs and enabled/disabled buttons accordingly.
        """
        isOk = True
        isOk &= isinstance(self.mapLayerComboBox.currentLayer(), QgsRasterLayer)
        isOk &= len(self.dstClassificationSchemeWidget.classificationScheme()) > 0
        isOk &= len(self.dstFileWidget.filePath()) > 0
        isOk &= self.mModel.rowCount() > 0

        btnAccept = self.buttonBox.button(QDialogButtonBox.Ok)
        btnAccept.setEnabled(isOk)

    def reclassificationSettings(self) -> dict:
        """
        Returns the re-classification settings
        :return: dict with {pathSrc:str, pathDst:str, labelLookup:dict, dstClassScheme:ClassificationScheme
        """
        summary = self.mModel.summary()
        summary['pathSrc'] = self.srcRasterLayer().source()
        summary['pathDst'] = self.dstRaster()
        return summary


class ReclassifyTool(EnMAPBoxApplication):

    def __init__(self, enmapBox, parent=None):
        super(ReclassifyTool, self).__init__(enmapBox, parent=parent)
        self.name = 'Reclassify Tool'
        self.version = 'Version 0.1'
        self.licence = 'GPL-3'
        self.m_dialogs = []

    def icon(self):
        pathIcon = os.path.join(APP_DIR, 'icon.png')
        return QIcon(pathIcon)

    def menu(self, appMenu):
        """
        Specify menu, submenus and actions
        :return: the QMenu or QAction to be added to the "Applications" menu.
        """
        appMenu = self.enmapbox.menu('Tools')

        # add a QAction that starts your GUI
        a = self.utilsAddActionInAlphanumericOrder(appMenu, 'Reclassify')
        assert isinstance(a, QAction)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return a

    def startGUI(self, *args):
        uiDialog = ReclassifyDialog(self.enmapbox.ui)
        uiDialog.show()
        uiDialog.accepted.connect(lambda: self.runReclassification(**uiDialog.reclassificationSettings()))
        self.m_dialogs.append(uiDialog)

    def runReclassification(self, **settings):
        # return {'pathSrc': pathSrc, 'pathDst': pathDst, 'LUT': LUT,
        #        'classNames': dstScheme.classNames(), 'classColors': dstScheme.classColors()}

        d = self.sender()
        if len(settings) > 0:
            from reclassifyapp import reclassify
            reclassify.reclassify(settings['pathSrc'],
                                  settings['pathDst'],
                                  settings['dstClassScheme'],
                                  settings['labelLookup'])
        if d in self.m_dialogs:
            self.m_dialogs.remove(d)
