# -*- coding: utf-8 -*-

"""
***************************************************************************
    settings
    ---------------------
    Date                 : September 2017
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

import enum
import os

from qgis.PyQt.QtCore import Qt, QSettings, QAbstractTableModel, QModelIndex
from qgis.PyQt.QtWidgets import QStyledItemDelegate, QTableView, QColorDialog, QDialog, QAbstractItemView, \
    QDialogButtonBox
from qgis.PyQt.QtXml import QDomElement

from enmapbox import enmapboxSettings
from enmapbox.gui.utils import enmapboxUiPath
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.examples.syntax import QColor
from enmapbox.qgispluginsupport.qps.utils import loadUi
from qgis.core import QgsSettings, QgsProject
from qgis.gui import QgsColorButton


class SettingsKey(enum.Enum):
    # describe default settings (might be loaded from txt file in future
    LoadProcessingFrameWork = 'LOAD_PF'
    LoadApplications = 'LOAD_EA'
    Debug = 'DEBUG'
    SplashScreen = 'SPLASHSCREEN'
    MessageTimeout = 'MESSAGE_TIMEOUT'
    ApplicationPath = 'APPLICATION_PATH'
    CursorLocationZeroBased = 'CURSOR_LOCATION_ZERO_BASED'


class EnMAPBoxSettings(QgsSettings):

    def __init__(self):
        super().__init__(QSettings.UserScope, 'HU-Berlin', 'EnMAP-Box')

        # define missing default values
        self.restoreDefaultValues(overwrite=False)
        s = ""

    def writeSettingsToProject(self, project: QgsProject):
        pass

    def readSettingsFromProject(self, project: QgsProject):
        pass

    def writeXml(self, element: QDomElement):
        pass

    def readXml(self, element: QDomElement):
        pass

    def restoreDefaultValues(self, overwrite=True):
        allKeys = self.allKeys()

        if overwrite or SettingsKey.ApplicationPath.value not in allKeys:
            self.setValue(SettingsKey.ApplicationPath.value, None)


GLOBAL_DEFAULT_SETTINGS = dict()


class SettingsInfo(object):
    @staticmethod
    def readFromQgsProject(project):
        assert isinstance(project, QgsProject)

        r = []
        return []
        # todo: read settings from QgsProject
        # for key in settings.childKeys():
        #    key = str(key)
        #    description = None
        #    if key in GLOBAL_DEFAULT_SETTINGS.keys():
        #        description = GLOBAL_DEFAULT_SETTINGS[key].mDescription
        #    r.append(SettingsInfo(key, settings.value(key), description))
        # return r

    @staticmethod
    def readFromQSettings(settings):
        assert isinstance(settings, QSettings)

        r = []
        for key in settings.childKeys():
            key = str(key)
            description = None
            if key in GLOBAL_DEFAULT_SETTINGS.keys():
                description = GLOBAL_DEFAULT_SETTINGS[key].mDescription
            r.append(SettingsInfo(key, settings.value(key), description))
        return r

    def __init__(self, key, value, description, defaultValue=None, range=None):

        assert isinstance(key, str)
        if range:
            assert len(range) == 2
        assert value is not None
        self.mValue = value
        if defaultValue is None:
            defaultValue = value
        self.mDefaultValue = defaultValue

        self.mKey = key
        self.mType = type(defaultValue)
        self.mDescription = description
        self.mRange = range

        GLOBAL_DEFAULT_SETTINGS[key] = self

    def saveToQSettings(self, settings=None):
        if not isinstance(settings, QSettings):
            settings = enmapboxSettings()

        settings.setValue(self.mKey, self.mValue)

    def saveToProject(self, project=None):
        if project is None:
            project = QgsProject.instance()
        assert isinstance(project, QgsProject)


# describe default settings (might be loaded from txt file in future
SettingsInfo('LOAD_PF', True, 'Load QGIS processing framework.')
SettingsInfo('LOAD_EA', True, 'Load external EnMAP-Box applications.')
SettingsInfo('DEBUG', False, 'Show additional debug printouts.')
SettingsInfo('SPLASHSCREEN', True, 'Show splashscreen on EnMAP-Box start.')
SettingsInfo('MESSAGE_TIMEOUT', 250, 'Timeout for message in messag bar.')
SettingsInfo('APPLICATION_PATH', '', 'List of additional EnMAP-Box application folders. Separated by ";" or ":"')


def initGlobalSettings():
    """
    Initializes the global EnMAP-Box Settings. In case a value is undefined, it will be overwritten
    by a default values from GLOBAL_DEFAULT_SETTINGS.
    :return:
    """
    settings = enmapboxSettings()
    for settingsInfo in GLOBAL_DEFAULT_SETTINGS.values():
        assert isinstance(settingsInfo, SettingsInfo)
        if settings.value(settingsInfo.mKey, None) is None:
            settings.setValue(settingsInfo.mKey, settingsInfo.mDefaultValue)


initGlobalSettings()


def resetGlobalSettings():
    settings = enmapboxSettings()
    settings.clear()
    settings.sync()
    for settingsInfo in GLOBAL_DEFAULT_SETTINGS.values():
        assert isinstance(settingsInfo, SettingsInfo)
        settings.setValue(settingsInfo.mKey, settingsInfo.mDefaultValue)


class SettingsTableModel(QAbstractTableModel):

    def __init__(self, settings, parent=None):

        super(SettingsTableModel, self).__init__(parent)

        self.cKey = 'Key'
        self.cValue = 'Value'
        self.cDefault = 'Default'
        self.columnNames = [self.cKey, self.cValue, self.cDefault]

        if isinstance(settings, QSettings):
            self.mSettingsList = SettingsInfo.readFromQSettings(settings)
        elif isinstance(settings, QgsProject):
            self.mSettingsList = SettingsInfo.readFromQgsProject(settings)
        else:
            raise Exception('Unknown type: {}'.format(settings))

    def columnCount(self, parent=QModelIndex()):
        return 2

    def rowCount(self, parent=QModelIndex()):
        return len(self.mSettingsList)

    def index2info(self, index):
        if index.isValid():
            return self.mSettingsList[index.row()]
        else:
            return None

    def flags(self, index):
        if index.isValid():
            info = self.index2info(index)
            columnName = self.columnNames[index.column()]
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            if columnName in [self.cValue]:  # allow check state
                flags = flags | Qt.ItemIsEditable
            return flags

        return None

    def headerData(self, col, orientation, role):
        if Qt is None:
            return None
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columnNames[col]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return col
        return None

    def data(self, index, role=Qt.DisplayRole):
        if role is None or not index.isValid():
            return None

        columnName = self.columnNames[index.column()]
        info = self.index2info(index)
        assert isinstance(info, SettingsInfo)

        value = None
        if role == Qt.DisplayRole:
            if columnName == self.cKey:
                value = info.mKey
            elif columnName == self.cValue:
                value = info.mValue
            elif columnName == self.cDefault:
                value = info.mDefaultValue

        if role == Qt.EditRole:
            if columnName == self.cValue:
                value = info.mValue
        if role == Qt.UserRole:
            return info
        return value

    def setData(self, index, value, role=None):
        if role is None or not index.isValid():
            return None

        columnName = self.columnNames[index.column()]

        info = self.index2info(index)
        assert isinstance(info, SettingsInfo)

        if role == Qt.EditRole:
            if columnName == self.cValue and len(value) > 0:
                # do not accept empty strings
                info.mValue = str(value)
                return True
        return False


class SettingsWidgetDelegates(QStyledItemDelegate):

    def __init__(self, tableView, parent=None):
        assert isinstance(tableView, QTableView)
        super(SettingsWidgetDelegates, self).__init__(parent=parent)
        self.tableView = tableView
        self.tableView.doubleClicked.connect(self.onDoubleClick)
        # self.tableView.model().rowsInserted.connect(self.onRowsInserted)

    def onDoubleClick(self, idx):
        model = self.tableView.model()
        assert isinstance(model, SettingsTableModel)
        info = model.index2info(idx)

        if info.mType == QColor():
            w1 = QColorDialog(info.mValue, self.tableView)
            w1.exec_()
            if w1.result() == QDialog.Accepted:
                c = w1.getColor()
                model.setData(idx, c, role=Qt.EditRole)

    def getColumnName(self, index):
        assert index.isValid()
        assert isinstance(index.model(), SettingsTableModel)
        return index.model().columnNames[index.column()]

    def createEditor(self, parent, option, index):
        cname = self.getColumnName(index)
        model = index.model()
        assert isinstance(model, SettingsTableModel)
        w = None
        if False and cname == model.cCOLOR:
            classInfo = model.getClassInfoFromIndex(index)
            w = QgsColorButton(parent, 'Class {}'.format(classInfo.mName))
            w.setColor(QColor(index.data()))
            w.colorChanged.connect(lambda: self.commitData.emit(w))
        return w

    def setEditorData(self, editor, index):
        cname = self.getColumnName(index)
        model = index.model()
        assert isinstance(model, SettingsTableModel)

        info = model.index2info(index)
        assert isinstance(info, SettingsInfo)

    def setModelData(self, w, model, index):
        cname = self.getColumnName(index)
        model = index.model()
        assert isinstance(model, SettingsTableModel)

        if False and cname == model.cCOLOR:
            assert isinstance(w, QgsColorButton)
            if index.data() != w.color():
                model.setData(index, w.color(), Qt.EditRole)


class SettingsDialog(QDialog):

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent=parent)
        loadUi(enmapboxUiPath('settingsdialog.ui'), self)

        self.modelGlobals = SettingsTableModel(enmapboxSettings(), parent=self)
        self.tableViewGlobalSettings.setModel(self.modelGlobals)
        # self.tableViewGlobalSettings.verticalHeader().setMovable(True)
        self.tableViewGlobalSettings.verticalHeader().setDragEnabled(True)
        self.tableViewGlobalSettings.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        # self.tableViewGlobalSettings.horizontalHeader().setResizeMode(QHeaderView.Interactive)
        self.tableViewGlobalSettings.resizeColumnsToContents()

        # self.tableViewProjectSettings.verticalHeader().setMovable(True)
        self.tableViewProjectSettings.verticalHeader().setDragEnabled(True)
        self.tableViewProjectSettings.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        # self.tableViewProjectSettings.horizontalHeader().setResizeMode(QHeaderView.Interactive)
        self.synQgsProjectSettings()

        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.onAccepted)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(lambda: self.setResult(QDialog.Rejected))
        self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.resetSettings)
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.saveSettings)

    def onAccepted(self):
        self.saveSettings()
        self.setResult(QDialog.Accepted)

    def saveSettings(self):
        for info in self.modelGlobals.mSettingsList:
            assert isinstance(info, SettingsInfo)
            info.saveToQSettings()

        # todo: save to QGIS Project file

    def resetSettings(self):
        resetGlobalSettings()
        self.modelGlobals = SettingsTableModel(enmapboxSettings(), parent=self)
        self.tableViewGlobalSettings.setModel(self.modelGlobals)
        self.tableViewGlobalSettings.resizeColumnsToContents()
        self.tableViewProjectSettings.resizeColumnsToContents()

    def synQgsProjectSettings(self):
        qgsProject = QgsProject.instance()
        path = qgsProject.fileName()
        if os.path.isfile(path):
            self.tableViewProjectSettings.setEnabled(True)
            self.labelProjectFilePath.setText(path)
            self.modelProject = SettingsTableModel(qgsProject, parent=self)
            self.tableViewProjectSettings.setModel(self.modelProject)
        else:
            self.tableViewProjectSettings.setEnabled(False)
            self.labelProjectFilePath.setText('<not available>')
            self.modelProject = None
            self.tableViewProjectSettings.setModel(None)

        self.tableViewGlobalSettings.resizeColumnsToContents()
        self.tableViewProjectSettings.resizeColumnsToContents()


def showSettingsDialog(parent=None):
    w = SettingsDialog(parent=parent)
    w.show()
