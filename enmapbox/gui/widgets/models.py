# -*- coding: utf-8 -*-
"""
***************************************************************************
    models
    ---------------------
    Date                 : Februar 2018
    Copyright            : (C) 2018 by Benjamin Jakimow
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
# noinspection PyPep8Naming


import copy

from qgis.PyQt.QtCore import Qt, QObject, pyqtSignal, QModelIndex, QAbstractListModel, QAbstractItemModel
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QComboBox, QTreeView


def currentComboBoxValue(comboBox):
    assert isinstance(comboBox, QComboBox)
    if isinstance(comboBox.model(), OptionListModel):
        o = comboBox.currentData(Qt.UserRole)
        assert isinstance(o, Option)
        return o.mValue
    else:
        return comboBox.currentData()


def setCurrentComboBoxValue(comboBox, value):
    """
    Sets a QComboBox to the value `value`, if it exists in the underlying item list
    :param comboBox: QComboBox
    :param value: any type
    :return: True | False
    """
    assert isinstance(comboBox, QComboBox)
    model = comboBox.model()
    if not isinstance(model, OptionListModel):
        i = comboBox.findData(value, role=Qt.DisplayRole)
        if i == -1:
            i = comboBox.findData(value, role=Qt.UserRole)

        if i != -1:
            comboBox.setCurrentIndex(i)
            return True
    else:
        if not isinstance(value, Option):
            value = Option(value)
        for i in range(comboBox.count()):
            option = comboBox.itemData(i, role=Qt.UserRole)
            if option == value:
                comboBox.setCurrentIndex(i)
                return True
    return False


class Option(object):

    def __init__(self, value, name=None, tooltip='', icon=QIcon()):

        self.mValue = value
        if name is None:
            name = str(value)
        self.mName = name
        self.mTooltip = tooltip
        self.mIcon = None

    def value(self):
        return self.mValue

    def name(self):
        return self.mName

    def tooltip(self):
        return self.mTooltip

    def icon(self):
        return self.mIcon

    def __eq__(self, other):
        if not isinstance(other, Option):
            return False
        else:
            return other.mValue == self.mValue


class OptionListModel(QAbstractListModel):
    def __init__(self, options=None, parent=None):
        super(OptionListModel, self).__init__(parent)

        self.mOptions = []

        self.insertOptions(options)

    def __len__(self):
        return len(self.mOptions)

    def addOption(self, option):
        self.insertOptions([option])

    def addOptions(self, options):
        assert isinstance(options, list)
        self.insertOptions(options)

    sigOptionsInserted = pyqtSignal(list)

    def insertOptions(self, options, i=None):
        if options is None:
            return
        if not isinstance(options, list):
            options = [options]
        assert isinstance(options, list)

        options = [self.o2o(o) for o in options]

        options = [o for o in options if o not in self.mOptions]

        nOptions = len(options)
        if nOptions > 0:
            if i is None:
                i = len(self.mOptions)
            self.beginInsertRows(QModelIndex(), i, i + len(options) - 1)
            for o in options:
                self.mOptions.insert(i, o)
                i += 1
            self.endInsertRows()

            self.sigOptionsInserted.emit(options)

    def o2o(self, value):
        if not isinstance(value, Option):
            value = Option(value, '{}'.format(value))
        return value

    def options(self) -> list:
        """
        :return: [list-of-Options]
        """
        return self.mOptions[:]

    def optionValues(self) -> list:
        """
        :return: [list-str-of-Option-Values]
        """
        return [o.mValue for o in self.options()]

    sigOptionsRemoved = pyqtSignal(list)

    def removeOptions(self, options):
        """
        Removes a list of options from this Options list.
        :param options: [list-of-Options]
        """
        options = [self.o2o(o) for o in options]
        options = [o for o in options if o in self.mOptions]
        removed = []
        for o in options:
            row = self.mOptions.index(o)
            self.beginRemoveRows(QModelIndex(), row, row)
            o2 = self.mOptions[row]
            self.mOptions.remove(o2)
            removed.append(o2)
            self.endRemoveRows()

        if len(removed) > 0:
            self.sigOptionsRemoved.emit(removed)

    def clear(self):
        self.removeOptions(self.mOptions)

    def rowCount(self, parent=None, *args, **kwargs) -> int:
        return len(self.mOptions)

    def columnCount(self, QModelIndex_parent=None, *args, **kwargs):
        return 1

    def idx2option(self, index):
        if index.isValid():
            return self.mOptions[index.row()]
        return None

    def option2idx(self, option):
        if isinstance(option, Option):
            option = option.mValue

        idx = self.createIndex(None, -1, 0)
        for i, o in enumerate(self.mOptions):
            assert isinstance(o, Option)
            if o.mValue == option:
                idx.setRow(i)
                break
        return idx

    def optionNames(self):
        return [o.mName for o in self.mOptions]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if (index.row() >= len(self.mOptions)) or (index.row() < 0):
            return None
        option = self.idx2option(index)
        if not isinstance(option, Option):
            s = ""
        result = None
        if role == Qt.DisplayRole:
            result = '{}'.format(option.mName)
        elif role == Qt.ToolTipRole:
            result = '{}'.format(option.mName if option.mTooltip is None else option.mTooltip)
        elif role == Qt.DecorationRole:
            result = option.mIcon
        elif role == Qt.UserRole:
            result = option
        return result


class TreeNode(QObject):
    sigWillAddChildren = pyqtSignal(object, int, int)
    sigAddedChildren = pyqtSignal(object, int, int)
    sigWillRemoveChildren = pyqtSignal(object, int, int)
    sigRemovedChildren = pyqtSignal(object, int, int)
    sigUpdated = pyqtSignal(object)

    def __init__(self, parentNode, name=None, values=None):
        super(TreeNode, self).__init__()
        self.mParent = parentNode

        self.mChildren = []
        self.mName = name
        self.mValues = []
        self.mIcon = None
        self.mToolTip = None

        if name:
            self.setName(name)

        if values:
            self.setValues(values)

        if isinstance(parentNode, TreeNode):
            parentNode.appendChildNodes([self])

        s = ""

    def clone(self, parent=None):

        n = TreeNode(parent)
        n.mName = self.mName
        n.mValues = copy.copy(self.mValues[:])
        n.mIcon = QIcon(self.mIcon)
        n.mToolTip = self.mToolTip

        for childNode in self.mChildren:
            assert isinstance(childNode, TreeNode)
            childNode.clone(parent=n)
        return n

    def nodeIndex(self):
        return self.mParent.mChildren.index(self)

    def next(self):
        i = self.nodeIndex()
        if i < len(self.mChildren.mChildren):
            return self.mParent.mChildren[i + 1]
        else:
            return None

    def previous(self):
        i = self.nodeIndex()
        if i > 0:
            return self.mParent.mChildren[i - 1]
        else:
            return None

    def detach(self):
        """
        Detaches this TreeNode from its parent TreeNode
        :return:
        """
        if isinstance(self.mParent, TreeNode):
            self.mParent.mChildren.remove(self)
            self.setParentNode(None)

    def appendChildNodes(self, listOfChildNodes):
        self.insertChildNodes(len(self.mChildren), listOfChildNodes)

    def insertChildNodes(self, index, listOfChildNodes):
        assert index <= len(self.mChildren)
        if isinstance(listOfChildNodes, TreeNode):
            listOfChildNodes = [listOfChildNodes]
        assert isinstance(listOfChildNodes, list)
        listOfChildNodes = [c for c in listOfChildNodes if c not in self.mChildren]

        nChildNodes = len(listOfChildNodes)
        idxLast = index + nChildNodes - 1
        self.sigWillAddChildren.emit(self, index, idxLast)
        for i, node in enumerate(listOfChildNodes):
            assert isinstance(node, TreeNode)
            node.mParent = self
            # connect node signals
            node.sigWillAddChildren.connect(self.sigWillAddChildren)
            node.sigAddedChildren.connect(self.sigAddedChildren)
            node.sigWillRemoveChildren.connect(self.sigWillRemoveChildren)
            node.sigRemovedChildren.connect(self.sigRemovedChildren)
            node.sigUpdated.connect(self.sigUpdated)

            self.mChildren.insert(index + i, node)

        self.sigAddedChildren.emit(self, index, idxLast)
        s = ""

    def removeChildNode(self, node):
        assert node in self.mChildren
        i = self.mChildren.index(node)
        self.removeChildNodes(i, 1)

    def removeChildNodes(self, row, count):

        if row < 0 or count <= 0:
            return False

        rowLast = row + count - 1

        if rowLast >= self.childCount():
            return False

        self.sigWillRemoveChildren.emit(self, row, rowLast)
        to_remove = self.childNodes()[row:rowLast + 1]
        for n in to_remove:
            self.mChildren.remove(n)
            # n.mParent = None

        self.sigRemovedChildren.emit(self, row, rowLast)

    def setToolTip(self, toolTip):
        self.mToolTip = toolTip

    def toolTip(self):
        return self.mToolTip

    def parentNode(self):
        return self.mParent

    def setParentNode(self, treeNode):
        assert isinstance(treeNode, TreeNode)
        self.mParent = treeNode

    def setIcon(self, icon):
        self.mIcon = icon

    def icon(self):
        return self.mIcon

    def setName(self, name):
        self.mName = name

    def name(self):
        return self.mName

    def contextMenu(self):
        return None

    def setValues(self, listOfValues):
        if not isinstance(listOfValues, list):
            listOfValues = [listOfValues]
        self.mValues = listOfValues[:]

    def values(self):
        return self.mValues[:]

    def childCount(self):
        return len(self.mChildren)

    def childNodes(self):
        return self.mChildren[:]

    def findChildNodes(self, type, recursive=True):
        results = []
        for node in self.mChildren:
            if isinstance(node, type):
                results.append(node)
            if recursive:
                results.extend(node.findChildNodes(type, recursive=True))
        return results


class TreeModel(QAbstractItemModel):
    def __init__(self, parent=None, rootNode=None):
        super(TreeModel, self).__init__(parent)

        self.mColumnNames = ['Node', 'Value']
        self.mRootNode = rootNode if isinstance(rootNode, TreeNode) else TreeNode(None)
        self.mRootNode.sigWillAddChildren.connect(self.nodeWillAddChildren)
        self.mRootNode.sigAddedChildren.connect(self.nodeAddedChildren)
        self.mRootNode.sigWillRemoveChildren.connect(self.nodeWillRemoveChildren)
        self.mRootNode.sigRemovedChildren.connect(self.nodeRemovedChildren)
        self.mRootNode.sigUpdated.connect(self.nodeUpdated)

        self.mTreeView = None
        if isinstance(parent, QTreeView):
            self.connectTreeView(parent)
        s = ""

    def rootNode(self):
        return self.mRootNode

    def nodeWillAddChildren(self, node, idx1, idxL):
        idxNode = self.node2idx(node)
        self.beginInsertRows(idxNode, idx1, idxL)

    def nodeAddedChildren(self, *args):
        self.endInsertRows()
        # for i in range(idx1, idxL+1):

    def nodeWillRemoveChildren(self, node, idx1, idxL):
        idxNode = self.node2idx(node)
        self.beginRemoveRows(idxNode, idx1, idxL)

    def nodeRemovedChildren(self, node, idx1, idxL):
        self.endRemoveRows()

    def nodeUpdated(self, node):
        idxNode = self.node2idx(node)
        self.dataChanged.emit(idxNode, idxNode)
        self.setColumnSpan(node)

    def headerData(self, section, orientation, role):
        assert isinstance(section, int)

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:

            if len(self.mColumnNames) > section:
                return self.mColumnNames[section]
            else:
                return ''

        else:
            return None

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node = self.idx2node(index)
        if not isinstance(node, TreeNode):
            return QModelIndex()

        parentNode = node.parentNode()
        if not isinstance(parentNode, TreeNode):
            return QModelIndex()

        return self.node2idx(parentNode)

        if node not in parentNode.mChildren:
            return QModelIndex
        row = parentNode.mChildren.index(node)
        return self.createIndex(row, 0, parentNode)

    def rowCount(self, index):

        node = self.idx2node(index)
        return len(node.mChildren) if isinstance(node, TreeNode) else 0

    def hasChildren(self, index=QModelIndex()):
        node = self.idx2node(index)
        return isinstance(node, TreeNode) and len(node.mChildren) > 0

    def columnNames(self):
        return self.mColumnNames

    def columnCount(self, index=QModelIndex()):

        return len(self.mColumnNames)

    def connectTreeView(self, treeView):
        self.mTreeView = treeView

    def setColumnSpan(self, node, span=None):
        if isinstance(self.mTreeView, QTreeView) \
                and isinstance(node, TreeNode) \
                and isinstance(node.parentNode(), TreeNode):
            idxNode = self.node2idx(node)
            idxParent = self.node2idx(node.parentNode())
            if not isinstance(span, bool):
                span = len(node.values()) == 0
            self.mTreeView.setFirstColumnSpanned(idxNode.row(), idxParent, span)
            for n in node.childNodes():
                self.setColumnSpan(n)

    def index(self, row, column, parentIndex=None):

        if parentIndex is None:
            parentNode = self.mRootNode
        else:
            parentNode = self.idx2node(parentIndex)

        if row < 0 or row >= parentNode.childCount():
            return QModelIndex()
        if column < 0 or column >= len(self.mColumnNames):
            return QModelIndex()

        if isinstance(parentNode, TreeNode) and row < len(parentNode.mChildren):
            return self.createIndex(row, column, parentNode.mChildren[row])
        else:
            return QModelIndex()

    def findParentNode(self, node, parentNodeType):
        assert isinstance(node, TreeNode)
        while True:
            if isinstance(node, parentNodeType):
                return node
            if not isinstance(node.parentNode(), TreeNode):
                return None
            node = node.parentNode()

    def indexes2nodes(self, indexes):
        assert isinstance(indexes, list)
        nodes = []
        for idx in indexes:
            n = self.idx2node(idx)
            if n not in nodes:
                nodes.append(n)
        return nodes

    def expandNode(self, node, expand=True, recursive=True):
        assert isinstance(node, TreeNode)
        if isinstance(self.mTreeView, QTreeView):
            idx = self.node2idx(node)
            self.mTreeView.setExpanded(idx, expand)

            if recursive:
                for n in node.childNodes():
                    self.expandNode(n, expand=expand, recursive=recursive)

    def nodes2indexes(self, nodes):
        return [self.node2idx(n) for n in nodes]

    def idx2node(self, index):
        if not index.isValid():
            return self.mRootNode
        else:
            return index.internalPointer()

    def node2idx(self, node):
        assert isinstance(node, TreeNode)
        if node == self.mRootNode:
            return QModelIndex()
        else:
            parentNode = node.parentNode()
            assert isinstance(parentNode, TreeNode)
            if node not in parentNode.mChildren:
                return QModelIndex()
            r = parentNode.mChildren.index(node)
            return self.createIndex(r, 0, node)

    def data(self, index, role):
        node = self.idx2node(index)
        col = index.column()
        if role == Qt.UserRole:
            return node

        if col == 0:
            if role in [Qt.DisplayRole, Qt.EditRole]:
                return node.name()
            if role == Qt.DecorationRole:
                return node.icon()
            if role == Qt.ToolTipRole:
                return node.toolTip()
        if col > 0:
            i = col - 1
            if role in [Qt.DisplayRole, Qt.EditRole] and len(node.values()) > i:
                return str(node.values()[i])

    def flags(self, index):
        assert isinstance(index, QModelIndex)
        if not index.isValid():
            return Qt.NoItemFlags
        node = self.idx2node(index)
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class TreeView(QTreeView):
    def __init__(self, *args, **kwds):
        super(TreeView, self).__init__(*args, **kwds)
