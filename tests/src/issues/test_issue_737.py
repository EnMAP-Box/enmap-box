"""
Addresses issue 737

Crash ID: 77ef79350e68116c5eda6d8af9e557ce99027e7d


Stack Trace


memcmp :
QTreeViewPrivate::removeViewItems :
QTreeViewPrivate::collapse :
QTreeViewPrivate::expandOrCollapseItemAtPos :
QTreeView::mousePressEvent :
PyInit_QtWidgets :
QWidget::event :
QFrame::event :
QAbstractItemView::viewportEvent :
PyInit_QtWidgets :
QCoreApplicationPrivate::sendThroughObjectEventFilters :
QApplicationPrivate::notify_helper :
QApplication::notify :
QgsApplication::notify qgsapplication.cpp:511
QCoreApplication::notifyInternal2 :
QApplicationPrivate::sendMouseEvent :
QSizePolicy::QSizePolicy :
QSizePolicy::QSizePolicy :
QApplicationPrivate::notify_helper :
QApplication::notify :
QgsApplication::notify qgsapplication.cpp:511
QCoreApplication::notifyInternal2 :
QGuiApplicationPrivate::processMouseEvent :
QWindowSystemInterface::sendWindowSystemEvents :
QEventDispatcherWin32::processEvents :
qt_plugin_query_metadata :
QEventLoop::exec :
QCoreApplication::exec :
main main.cpp:1646
WinMain mainwin.cpp:197
__scrt_common_main_seh exe_common.inl:288
BaseThreadInitThunk :
RtlUserThreadStart :


"""
import unittest

from enmapbox.gui.datasources.datasources import ModelDataSource
from enmapbox.gui.datasources.manager import DataSourceManager
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.models import PyObjectTreeNode
from enmapbox.testing import EnMAPBoxTestCase
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QTreeView
from qgis.core import QgsProject
from enmapboxtestdata import classificationDatasetAsPklFile


class TestIssue737(EnMAPBoxTestCase):

    def tearDown(self):

        emb = EnMAPBox.instance()
        if isinstance(emb, EnMAPBox):
            emb.close()

        assert EnMAPBox.instance() is None

        QgsProject.instance().removeAllMapLayers()

        super().tearDown()

    def test_issue_747(self):
        """
        Collapsing parent nodes crashes TreeView
        How to reproduce
        1. Show Widget
        2. Expand nodes 'Models', 'classification_dataset.pkl', 'dict', 'X', 'array'
           (below 'classification_dataset.pkl' will be fetched on demand)
        3. unexpand 'X'

        - happens with TreeView but not QTreeView
        - seems to be related to TreeView.setColumnSpan
        - automatic column span is necessary to save space
        """
        model = DataSourceManager()

        from enmapbox.qgispluginsupport.qps.models import TreeView
        tv = TreeView()
        # tv = QTreeView()
        tv.setUniformRowHeights(True)
        tv.setIndentation(12)
        tv.setAutoExpansionDepth(10)
        tv.setModel(model)

        # set False to avoid error
        tv.setAutoFirstColumnSpan(True)

        self.assertIsInstance(tv, QTreeView)
        model.addDataSources(classificationDatasetAsPklFile)

        node = model.rootNode().findChildNodes(ModelDataSource, recursive=True)
        self.assertTrue(len(node) == 1)
        node = node[0]
        # tv.expandRecursively(QModelIndex(), 4)
        # dict X array
        self.assertIsInstance(node, ModelDataSource)
        NODES = dict(ROOT=node)

        for name in ['dict', 'X', 'array']:
            node.fetch()
            # tv.expand(model.node2idx(node))
            node = node.findChildNodes(PyObjectTreeNode, name)[0]
            NODES[name] = node

        # tv.expand(model.node2idx(node))
        tv.resize(QSize(600, 600))
        tv.show()
        s = ""

        self.showGui(tv)


if __name__ == '__main__':
    unittest.main(buffer=False)
