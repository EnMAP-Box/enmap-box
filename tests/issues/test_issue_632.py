import fnmatch
import os.path
from typing import List, Union

from qgis.PyQt.QtCore import QModelIndex, Qt

from enmapbox import initAll
from enmapbox.gui.datasources.manager import DataSourceManager, DataSourceManagerProxyModel
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app, EnMAPBoxTestCase
from enmapboxtestdata import classifierDumpPkl

start_app()


class Issue641Tests(EnMAPBoxTestCase):

    def test_issue632(self):
        initAll()

        box = EnMAPBox(load_core_apps=False, load_other_apps=False)
        box.addSource(classifierDumpPkl)

        tv = box.dataSourceManagerTreeView()
        dspm: DataSourceManagerProxyModel = tv.model()
        dsm: DataSourceManager = dspm.sourceModel()

        file_name = os.path.basename(classifierDumpPkl)

        box.ui.show()

        def findNode(view, path: List[str], parent: QModelIndex = QModelIndex) -> QModelIndex:
            model = view.model()

            expression = path[0]

            r0 = 0
            child_names = []
            while model.canFetchMore(parent) or r0 < model.rowCount(parent):
                model.fetchMore(parent)
                if model.rowCount() == r0:
                    return None

                nrows = model.rowCount(parent)
                for row in range(r0, nrows):
                    child: QModelIndex = model.index(row, 0, parent)
                    child_name = child.data(Qt.DisplayRole)
                    child_names.append(child_name)
                    if fnmatch.fnmatch(child_name, expression):
                        if len(path) == 1:
                            return child
                        else:
                            node = findNode(view, path[1:], parent=child)
                            if isinstance(node, QModelIndex):
                                return node
                    else:
                        s = ""
                    ro = row
            return None

        def expand_nodes(view,
                         path: Union[str, List[str]],
                         parent: QModelIndex = QModelIndex(),
                         expanded: bool = True,
                         last_only:bool = False):
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

        path = f'Models*/{file_name}/Content/X/array'
        expand_nodes(tv, path)
        path = f'Models*/{file_name}/Content/X'
        expand_nodes(tv, path, expanded=False, last_only=True)

        s = ""
        # maximize datasource panel
        box.ui.dockPanel.hide()
        box.ui.resizeDocks([box.ui.dataSourcePanel], [box.ui.width()], Qt.Horizontal)
        self.showGui(box.ui)
