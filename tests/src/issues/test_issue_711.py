# -*- coding: utf-8 -*-
"""
***************************************************************************
    test_issue_711
    ---------------------
    Date                 :
    Copyright            : (C) 2021 by Benjamin Jakimow
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


import unittest

import qgis
from enmapbox.testing import TestObjects, EnMAPBoxTestCase
from enmapbox.gui.enmapboxgui import EnMAPBox
from qgis.core import QgsProject


class TestIssue711(EnMAPBoxTestCase):

    def tearDown(self):

        emb = EnMAPBox.instance()
        if isinstance(emb, EnMAPBox):
            emb.close()

        assert EnMAPBox.instance() is None

        QgsProject.instance().removeAllMapLayers()

        super().tearDown()

    def test_instance_pure(self):
        EMB = EnMAPBox(load_other_apps=False, load_core_apps=False)

        self.assertIsInstance(EnMAPBox.instance(), EnMAPBox)
        self.assertEqual(EMB, EnMAPBox.instance())

        self.showGui([qgis.utils.iface.mainWindow(), EMB.ui])

    def test_issue_711(self):
        """
        see https://bitbucket.org/hu-geomatics/enmap-box/issues/711
        """
        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        import os
        os.environ.setdefault('DEBUG', 'True')
        self.assertTrue(len(QgsProject.instance().mapLayers()) == 0)
        self.assertIsInstance(EnMAPBox.instance(), EnMAPBox)
        self.assertEqual(EMB, EnMAPBox.instance())

        layers = []
        if False:
            EMB.loadExampleData()
        else:
            import enmapbox.exampledata
            sources = []
            sources += [enmapbox.exampledata.enmap,
                        enmapbox.exampledata.landcover_polygons,
                        enmapbox.exampledata.landcover_points,
                        enmapbox.exampledata.library_gpkg,
                        enmapbox.exampledata.library_sli,
                        enmapbox.exampledata.enmap_srf_library
                        ]

            sources += [TestObjects.createVectorLayer(),
                        TestObjects.createVectorLayer(),
                        TestObjects.createVectorLayer(),
                        TestObjects.createVectorLayer(),
                        TestObjects.createVectorLayer()
                        ]
            sources += [TestObjects.createRasterLayer(),
                        TestObjects.createRasterLayer(),
                        TestObjects.createRasterLayer(),
                        TestObjects.createRasterLayer(),
                        TestObjects.createVectorLayer()
                        ]
            layers.extend(sources)
            dSources = EMB.addSources(sources)

        EMB.ui.show()

        for i, s in enumerate(EMB.dataSources()):
            print(f'{i + 1}: {s}')

        print('Remove all datasources:')
        EMB.dataSourceManagerTreeView().model().sourceModel().rootNode().removeAllChildNodes()
        EMB.dataSourceManagerTreeView().onRemoveAllDataSources()
        print('All datasources removed')
        self.assertTrue(len(EMB.dataSources()) == 0)
        # import qgis.utils
        # QgsProject.instance()
        # qgis.utils.iface.actionSaveProject().trigger()
        # qgis.utils.iface.mainWindow()
        self.showGui([EMB.ui])

    def test_treeModel(self):
        from enmapbox.qgispluginsupport.qps.models import TreeView, TreeModel, TreeNode

        model = TreeModel()

        view = TreeView()
        view.setModel(model)

        groupNodes = list()
        subnodes = list()
        for g in range(3):
            gnode = TreeNode()
            for i in range(10):
                node = TreeNode()
                gnode.appendChildNodes(node)
                subnodes.append(node)
            groupNodes.append(gnode)
            model.rootNode().appendChildNodes(gnode)

        view.show()

        for n in gnode:
            n.parentNode().removeChildNodes(n)


if __name__ == '__main__':
    unittest.main(buffer=False)
