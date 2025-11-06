import os

import numpy as np
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QIcon, QColor, QPixmap
from qgis.PyQt.QtWidgets import QMenu, QApplication
from qgis.core import QgsCoordinateReferenceSystem, QgsUnitTypes, QgsRasterLayer, QgsDataItem, QgsLayerItem, \
    QgsMapLayerType, QgsVectorLayer, QgsMapLayer, QgsRasterDataProvider

from enmapbox.gui.utils import dataTypeName
from enmapbox.qgispluginsupport.qps.classification.classificationscheme import ClassInfo, ClassificationScheme
from enmapbox.qgispluginsupport.qps.models import TreeNode, PyObjectTreeNode
from enmapbox.qgispluginsupport.qps.utils import fileSizeString, SpatialExtent, QGIS_DATATYPE_NAMES


class CRSLayerTreeNode(TreeNode):
    def __init__(self, crs: QgsCoordinateReferenceSystem):
        assert isinstance(crs, QgsCoordinateReferenceSystem)
        super().__init__(crs.description())
        self.setName('CRS')
        self.setIcon(QIcon(':/images/themes/default/propertyicons/CRS.svg'))
        self.setToolTip('Coordinate Reference System')
        self.mCrs = None
        self.nodeDescription = TreeNode('Name', toolTip='Description')
        self.nodeAuthID = TreeNode('AuthID', toolTip='Authority ID')
        self.nodeAcronym = TreeNode('Acronym', toolTip='Projection Acronym')
        self.nodeMapUnits = TreeNode('Map Units')
        self.setCrs(crs)

        self.appendChildNodes([self.nodeDescription, self.nodeAuthID, self.nodeAcronym, self.nodeMapUnits])

    def setCrs(self, crs):
        assert isinstance(crs, QgsCoordinateReferenceSystem)
        self.mCrs = crs
        if self.mCrs.isValid():
            self.setValues(crs.description())
            self.nodeDescription.setValues(crs.description())
            self.nodeAuthID.setValues(crs.authid())
            self.nodeAcronym.setValues(crs.projectionAcronym())
            # self.nodeDescription.setItemVisibilityChecked(Qt.Checked)
            self.nodeMapUnits.setValues(QgsUnitTypes.toString(self.mCrs.mapUnits()))
        else:
            self.setValues(None)
            self.nodeDescription.setValue('N/A')
            self.nodeAuthID.setValue('N/A')
            self.nodeAcronym.setValue('N/A')
            self.nodeMapUnits.setValue('N/A')

    def contextMenu(self):
        menu = QMenu()
        a = menu.addAction('Copy EPSG Code')
        a.setToolTip('Copy the authority id ("{}") of this CRS.'.format(self.mCrs.authid()))
        a.triggered.connect(lambda: QApplication.clipboard().setText(self.mCrs.authid()))

        a = menu.addAction('Copy WKT')
        a.setToolTip('Copy the well-known-type representation of this CRS.')
        a.triggered.connect(lambda: QApplication.clipboard().setText(self.mCrs.toWkt()))

        a = menu.addAction('Copy Proj4')
        a.setToolTip('Copy the Proj4 representation of this CRS.')
        a.triggered.connect(lambda: QApplication.clipboard().setText(self.mCrs.toProj4()))
        return menu


class RasterBandTreeNode(TreeNode):

    def __init__(self, rasterLayer: QgsRasterLayer, bandIndex, *args, **kwds):
        super().__init__(*args, **kwds)
        assert isinstance(rasterLayer, QgsRasterLayer)
        assert bandIndex >= 0
        assert bandIndex < rasterLayer.bandCount()
        # self.mDataSource = dataSource
        self.mBandIndex: int = bandIndex

        if False:
            md = self.mDataSource.mBandMetadata[bandIndex]
            classScheme = md.get('__ClassificationScheme__')
            if isinstance(classScheme, ClassificationScheme):
                to_add = []
                for ci in classScheme:
                    assert isinstance(ci, ClassInfo)
                    classNode = TreeNode(name=str(ci.label()))
                    classNode.setValue(ci.name())
                    classNode.setIcon(ci.icon())
                    to_add.append(classNode)
                self.appendChildNodes(to_add)

    def bandIndex(self) -> int:
        return self.mBandIndex

    def rasterSource(self) -> TreeNode:
        from enmapbox.gui.datasources.datasources import RasterDataSource
        return self.findParentNode(RasterDataSource)


class ClassificationNodeLayer(TreeNode):

    def __init__(self, classificationScheme, name='Classification Scheme'):
        super(ClassificationNodeLayer, self).__init__()
        self.setName(name)
        to_add = []
        for i, ci in enumerate(classificationScheme):
            to_add.append(TreeNode(name='{}'.format(i), values=ci.name(), icon=ci.icon()))
        self.appendChildNodes(to_add)


class ColorTreeNode(TreeNode):

    def __init__(self, color: QColor):
        assert isinstance(color, QColor)

        pm = QPixmap(QSize(20, 20))
        pm.fill(color)
        icon = QIcon(pm)
        name = color.name()
        value = color.getRgbF()
        super(ColorTreeNode, self).__init__(name=name, value=value, icon=icon)


class DataSourceSizesTreeNode(TreeNode):
    """
    A node to show the different aspects of dataSource sizes
    Sub-Nodes:
        spatial extent in map unit
        pixel sizes (if raster source)
        pixel extent (if raster source)
    """

    def __init__(self):
        super().__init__('Size')

    def updateNodes(self, dataItem: QgsDataItem) -> dict:
        self.removeAllChildNodes()
        data = dict()
        if not isinstance(dataItem, QgsDataItem):
            return data

        childs = []
        value = []

        if os.path.exists(dataItem.path()):

            try:
                size = os.path.getsize(dataItem.path())
                size = fileSizeString(size)
                value.append(size)
                childs += [TreeNode('File', size)]
            except Exception as ex:
                pass

        lyr = None

        from enmapbox.gui.datasources.datasources import LayerItem
        if isinstance(dataItem, LayerItem):
            lyr = dataItem.referenceLayer()

        if lyr is None and isinstance(dataItem, QgsLayerItem):
            if dataItem.mapLayerType() == QgsMapLayerType.VectorLayer:
                lyr = QgsVectorLayer(dataItem.path(), dataItem.name(), dataItem.providerKey())
            elif dataItem.mapLayerType() == QgsMapLayerType.RasterLayer:
                lyr = QgsRasterLayer(dataItem.path(), dataItem.name(), dataItem.providerKey())

        if isinstance(lyr, QgsMapLayer) and lyr.isValid():

            ext = SpatialExtent.fromLayer(lyr)
            mu = QgsUnitTypes.encodeUnit(ext.crs().mapUnits())
            from .datasources import DataSource
            data[DataSource.MD_LAYER] = lyr
            data[DataSource.MD_MAPUNIT] = mu
            data[DataSource.MD_EXTENT] = ext

            childs += [TreeNode('Width', value='{:0.2f} {}'.format(ext.width(), mu), toolTip='Spatial width'),
                       TreeNode('Height', value='{:0.2f} {}'.format(ext.height(), mu), toolTip='Spatial height')
                       ]

            if isinstance(lyr, QgsRasterLayer):
                dp: QgsRasterDataProvider = lyr.dataProvider()
                value.append(f'{lyr.width()}'
                             f'x{lyr.height()}'
                             f'x{lyr.bandCount()}'
                             f'x{dp.dataTypeSize(1)} ({QGIS_DATATYPE_NAMES.get(dp.dataType(1), "unknown type")})')

                childs += [TreeNode('Pixel',
                                    value=f'{lyr.rasterUnitsPerPixelX()}x'
                                          f'{lyr.rasterUnitsPerPixelY()} '
                                          f'{QgsUnitTypes.encodeUnit(lyr.crs().mapUnits())}',
                                    toolTip='Size of single pixel / ground sampling resolution'),
                           TreeNode('Samples', value=lyr.width(), toolTip='Samples/columns in X direction'),
                           TreeNode('Lines', value=lyr.height(), toolTip='Lines/rows in Y direction'),
                           TreeNode('Bands', value=lyr.bandCount(), toolTip='Raster bands'),
                           TreeNode('Data Type',
                                    value=dataTypeName(dp.dataType(1)),
                                    toolTip=dataTypeName(dp.dataType(1), verbose=True))
                           ]
            elif isinstance(lyr, QgsVectorLayer):
                value.append('{} features'.format(lyr.featureCount()))

        self.setValue(' '.join([str(v) for v in value]))
        self.appendChildNodes(childs)
        return data


class HubFlowPyObjectTreeNode(PyObjectTreeNode):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.setValue(str(self.mPyObject))

    def populateContextMenu(self, menu: QMenu):
        def copyToClipboard():
            state = np.get_printoptions()['threshold']
            np.set_printoptions(threshold=np.inf)
            QApplication.clipboard().setText(str(self.mPyObject))
            np.set_printoptions(threshold=state)

        if isinstance(self.mPyObject, np.ndarray):
            a = menu.addAction('Copy Array')
            a.setToolTip('Copy Numpy Array to Clipboard.')
            a.triggered.connect(copyToClipboard)
