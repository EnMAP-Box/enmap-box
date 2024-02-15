import fnmatch
import os.path
from typing import List, Union

import numpy as np
from PyQt5.QtTest import QAbstractItemModelTester
from qgis.PyQt.QtCore import QModelIndex, Qt

from enmapbox import initAll
from enmapbox.gui.datasources.datasources import AnyObjectSource
from enmapbox.gui.datasources.datasourcesets import AnyOtherSourcesSet
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app, EnMAPBoxTestCase
from enmapboxtestdata import classifierDumpPkl

start_app()


def findNode(view, path: Union[str, List[str]], parent: QModelIndex = QModelIndex()) -> QModelIndex:
    """
    Returns the QModelIndex for the deepest node in a node-path., e.g. n3 from 'n1/n2/n3'
    :param view: QAbstractItemView
    :param path: node-path, e.g. 'node/subNode'
                 node names need to match on a QModelIndex.data(Qt.DisplayRole)
                 node names can be wildcard expressions
    :param parent: QModelIndex, parent of the give node-path.
    :return: QModelIndex or None
    """
    model = view.model()
    if isinstance(path, str):
        path = path.split('/')
    expression = path[0]

    child_names = []

    CHILD_NAMES = {}
    row = 0
    last_row = None
    while True:
        if row == model.rowCount(parent):
            if model.canFetchMore(parent):

                sm = model.sourceModel()
                sp = model.mapToSource(parent)
                A = [sm.index(r, 0, sp).data() for r in range(sm.rowCount(sp))]
                model.fetchMore(parent)
                B = [sm.index(r, 0, sp).data() for r in range(sm.rowCount(sp))]
                if len(B) == len(A) + 1 and A != B[0:-1]:
                    s = ""
                continue
            else:
                break
        assert row not in CHILD_NAMES
        CHILD_NAMES[row] = [model.index(r2, 0, parent).data() for r2 in range(row)]
        child: QModelIndex = model.index(row, 0, parent)
        child_name = child.data(Qt.DisplayRole)

        if child_name == 'dtype':
            s = ""
            if child_name in child_names:
                s = ""
            else:
                s = ""

        child_names.append(child_name)
        if fnmatch.fnmatch(child_name, expression):
            if len(path) == 1:
                return child
            else:
                node = findNode(view, path[1:], parent=child)
                if isinstance(node, QModelIndex):
                    return node
        last_row = row
        row += 1

    return None


def expandNodes(view,
                path: Union[str, List[str]],
                parent: QModelIndex = QModelIndex(),
                expanded: bool = True,
                last_only: bool = False):
    """
    :param view: QAbstractItemView
    :param path: node path, e.g. 'rootNodeName/subNodeName/subsubNodeName'.
                 can contain Wildcards, e.g. 'sub*' to catch Nodes called 'subA' and 'subB'
    :param parent: QModelIndex
    :param expanded: True (default) to expand the nodes
    :param last_only: False. Set True to expand only the last node in the path.
    :return:
    """
    if isinstance(path, str):
        path = path.split('/')

    node = findNode(view, path, parent=parent)
    if isinstance(node, QModelIndex):
        if last_only:
            view.setExpanded(node, expanded)
        else:
            while node.isValid():
                view.setExpanded(node, expanded)
                node = node.parent()



class Issue641Tests(EnMAPBoxTestCase):

    def test_issue632(self):
        initAll()
        file_name = os.path.basename(classifierDumpPkl)
        box = EnMAPBox(load_core_apps=False, load_other_apps=False)

        tv = box.dataSourceManagerTreeView()
        mgr = box.dataSourceManager()

        anySourcSet = AnyOtherSourcesSet()
        mgr.rootNode().appendChildNodes(anySourcSet)
        tester = QAbstractItemModelTester(mgr, QAbstractItemModelTester.FailureReportingMode.Fatal)

        # path = f'Models*/{file_name}/Content/X/array/0'
        path = f'*/{file_name}/Content/X/array/0'
        # obj = {'X': np.random.rand(58, 177)}
        obj = {'X': np.random.rand(20, 10)}
        source = AnyObjectSource(obj=obj, name=file_name)
        # box.addSource(source)

        box.addSource(classifierDumpPkl)
        box.ui.show()

        expandNodes(tv, path)
        path = f'Models*/{file_name}/Content'
        # expandNodes(tv, path, expanded=False, last_only=True)
        # QApplication.processEvents()
        s = ""
        # maximize datasource panel
        box.ui.dockPanel.hide()
        box.ui.resizeDocks([box.ui.dataSourcePanel], [box.ui.width()], Qt.Horizontal)
        self.showGui(box.ui)
        s = ""

