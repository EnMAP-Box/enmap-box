import pickle
from os.path import join, basename, isabs
from typing import Optional

from osgeo import gdal

import processing
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.mimedata import MDF_RASTERBANDS, QGIS_URILIST_MIMETYPE, MDF_ENMAPBOX_LAYERTREEMODELDATA, \
    MDF_QGIS_LAYERTREEMODELDATA, MDF_QGIS_LAYERTREEMODELDATA_XML, MDF_URILIST
from enmapbox.gui.widgets.multiplerasterbandselectionwidget.multiplerasterbandselectionwidget import \
    MultipleRasterBandSelectionWidget
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from geetimeseriesexplorerapp import MapTool
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QEvent
from qgis.PyQt.QtWidgets import QToolButton, QTableWidget, QRadioButton
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsMimeDataUtils, QgsReadWriteContext, QgsLayerTree, QgsProject, QgsMapLayerProxyModel, \
    QgsRasterLayer
from qgis.gui import QgsMapLayerComboBox, QgsDockWidget, QgisInterface, QgsFileWidget
from typeguard import typechecked


@typechecked
class RasterBandStackingDockWidget(QgsDockWidget):
    mRasterTable: QTableWidget
    mAddRaster: QToolButton
    mRemoveRaster: QToolButton
    mRemoveAllRaster: QToolButton
    mMoveUp: QToolButton
    mMoveDown: QToolButton
    mFile: QgsFileWidget
    mCreate: QToolButton

    mGridAutomaticType: QRadioButton
    mGridRasterType: QRadioButton
    mGridRaster: QgsMapLayerComboBox

    EnmapBoxInterface, QgisInterface = 0, 1
    AutomaticGridType, RasterGridType = 0, 1

    def __init__(self, currentLocationMapTool: Optional[MapTool], parent=None):
        QgsDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        self.currentLocationMapTool = currentLocationMapTool
        self.mFile.setFilePath('bandStack.vrt')
        self.mGridRaster.setFilters(QgsMapLayerProxyModel.RasterLayer)

        # set from outside
        self.interface = None
        self.interfaceType = None

        # connect signals
        self.mAddRaster.clicked.connect(self.onAddRasterClicked)
        self.mRemoveRaster.clicked.connect(self.onRemoveRasterClicked)
        self.mRemoveAllRaster.clicked.connect(self.onRemoveAllRasterClicked)
        self.mMoveUp.clicked.connect(self.onMoveUpClicked)
        self.mMoveDown.clicked.connect(self.onMoveDownClicked)
        self.mCreate.clicked.connect(self.onCreateClicked)

        self.mRasterTable.installEventFilter(self)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.DragEnter):
            event.accept()
            return True
        if (event.type() == QEvent.Drop):
            mimeData = event.mimeData()

            is_QGIS_LAYERTREE_FORMAT = any(
                [MDF_ENMAPBOX_LAYERTREEMODELDATA in mimeData.formats(),
                 MDF_QGIS_LAYERTREEMODELDATA in mimeData.formats()]
            )
            QGIS_LAYERTREE_FORMAT = MDF_QGIS_LAYERTREEMODELDATA

            if is_QGIS_LAYERTREE_FORMAT:
                doc = QDomDocument()
                doc.setContent(mimeData.data(QGIS_LAYERTREE_FORMAT))
                node = doc.firstChildElement(MDF_QGIS_LAYERTREEMODELDATA_XML)
                context = QgsReadWriteContext()
                layerTree = QgsLayerTree.readXml(node, context)
                for layerId in layerTree.findLayerIds():
                    layer = QgsProject.instance().mapLayer(layerId)
                    if isinstance(layer, QgsRasterLayer):
                        self.onAddRasterClicked(layer=layer)
            elif MDF_RASTERBANDS in mimeData.formats():
                data = pickle.loads(mimeData.data(MDF_RASTERBANDS))
                for uri, baseName, providerKey, bandIndex in data:
                    self.onAddRasterClicked(uri=uri, bandNo=bandIndex + 1)
            elif QGIS_URILIST_MIMETYPE in mimeData.formats():
                for uri in QgsMimeDataUtils.decodeUriList(mimeData):
                    self.onAddRasterClicked(uri=uri.uri)
            elif MDF_URILIST in mimeData.formats():
                for url in mimeData.urls():
                    source = url.url().replace('file:///', '')
                    layer = QgsRasterLayer(source)
                    if layer.isValid():
                        self.onAddRasterClicked(uri=source)
            else:
                raise NotImplementedError()

            return True
        return False

    def enmapBoxInterface(self) -> EnMAPBox:
        return self.interface

    def qgisInterface(self):
        return self.interface

    def setInterface(self, interface):
        self.interface = interface
        if isinstance(interface, EnMAPBox):
            self.interfaceType = 0
        elif isinstance(interface, QgisInterface):
            self.interfaceType = 1
        else:
            raise ValueError()

    def onAddRasterClicked(self, *args, uri: str = None, layer: QgsRasterLayer = None, bandNo: int = None):

        self.mRasterTable.setRowCount(self.mRasterTable.rowCount() + 1)
        row = self.mRasterTable.rowCount() - 1
        mRaster = QgsMapLayerComboBox()
        mRaster.setFilters(QgsMapLayerProxyModel.RasterLayer)
        mRaster.setExcludedProviders(['wms'])
        mRaster.setAllowEmptyLayer(True)

        if self.interfaceType == self.EnmapBoxInterface:
            sources = self.enmapBoxInterface().dataSources('RASTER', True)
            mRaster.setAdditionalItems(sources)
        self.mRasterTable.setCellWidget(row, 0, mRaster)

        mMultiBand = MultipleRasterBandSelectionWidget()

        mRaster.layerChanged.connect(self.onLayerChanged)
        mRaster.mMultiBand = mMultiBand
        self.mRasterTable.setCellWidget(row, 1, mMultiBand)

        if uri is not None:
            items = mRaster.additionalItems()
            if uri not in items:
                items.append(uri)
            mRaster.setAdditionalItems(items)
            mRaster.setCurrentText(uri)
            layer = QgsRasterLayer(uri)
            mMultiBand.setLayer(layer)
            mMultiBand.setCurrentBands(None)
        elif layer is not None:
            mRaster.setLayer(layer)
            mMultiBand.setLayer(layer)
            mMultiBand.setCurrentBands(None)
        else:
            mRaster.setLayer(None)
            mMultiBand.setLayer(None)

        if bandNo is not None:
            mMultiBand.mBand.setCurrentIndex(bandNo)

        # self.onLayerChanged()

    def onLayerChanged(self):
        mLayer: QgsMapLayerComboBox = self.sender()
        mMultiBand: MultipleRasterBandSelectionWidget = mLayer.mMultiBand
        if mLayer.currentLayer() is None:
            if mLayer.currentText() == '':
                return
            layer = QgsRasterLayer(mLayer.currentText())
        else:
            layer: QgsRasterLayer = mLayer.currentLayer()
        mMultiBand.setLayer(layer)
        mMultiBand.setCurrentBands(None)

    def onRemoveRasterClicked(self):
        row = self.mRasterTable.currentRow()
        if row == -1:
            return
        self.mRasterTable.removeRow(row)

    def onRemoveAllRasterClicked(self):
        for i in reversed(range(self.mRasterTable.rowCount())):
            self.mRasterTable.removeRow(i)

    def onMoveUpClicked(self):
        row = self.mRasterTable.currentRow()
        if row == 0:
            return
        self.mRasterTable.insertRow(row - 1)
        self.mRasterTable.selectRow(row - 1)
        for i in range(self.mRasterTable.columnCount()):
            self.mRasterTable.setCellWidget(row - 1, i, self.mRasterTable.cellWidget(row + 1, i))
        self.mRasterTable.removeRow(row + 1)

    def onMoveDownClicked(self):
        row = self.mRasterTable.currentRow()
        if row + 1 == self.mRasterTable.rowCount():
            return
        self.mRasterTable.insertRow(row + 2)
        self.mRasterTable.selectRow(row + 2)
        for i in range(self.mRasterTable.columnCount()):
            self.mRasterTable.setCellWidget(row + 2, i, self.mRasterTable.cellWidget(row, i))
        self.mRasterTable.removeRow(row)

    def onCreateClicked(self):

        sources = list()
        bands = list()
        for row in range(self.mRasterTable.rowCount()):
            mLayer: QgsMapLayerComboBox = self.mRasterTable.cellWidget(row, 0)
            mMultiBand: MultipleRasterBandSelectionWidget = mLayer.mMultiBand
            if mLayer.currentLayer() is None:
                if mLayer.currentText() == '':
                    continue
                source = mLayer.currentText()
            else:
                source = mLayer.currentLayer().source()

            for bandNo in mMultiBand.currentBands():
                sources.append(source)
                bands.append(bandNo)

        if len(sources) == 0:
            return

        # prepare single bands
        filenames = list()

        if isabs(self.mFile.filePath()):
            filename = self.mFile.filePath()
        else:
            filename = join(Utils.getTempDirInTempFolder(), self.mFile.filePath())

        if self.mGridAutomaticType.isChecked():
            grid = None
        elif self.mGridRasterType.isChecked():
            grid = self.mGridRaster.currentLayer()
        else:
            raise ValueError()

        for i, (source, bandNo) in enumerate(zip(sources, bands), 1):
            fname = Utils.tmpFilename(filename, f'band_{i}.vrt')
            alg = TranslateRasterAlgorithm()
            parameters = {
                alg.P_RASTER: source,
                alg.P_BAND_LIST: [bandNo],
                alg.P_GRID: grid,
                alg.P_OUTPUT_RASTER: fname
            }
            processing.run(alg, parameters)
            filenames.append(fname)

        # build band stack
        ds = gdal.BuildVRT(filename, filenames, options=gdal.BuildVRTOptions(separate=True))

        # write metadata
        writer = RasterWriter(ds)
        for bandNo2, (source, bandNo) in enumerate(zip(sources, bands), 1):
            reader = RasterReader(source)
            writer.setMetadata(reader.metadata(bandNo), bandNo2)
            writer.setBadBandMultiplier(reader.badBandMultiplier(bandNo), bandNo2)
            writer.setBandColor(reader.bandColor(bandNo), bandNo2)
            writer.setBandName(reader.bandName(bandNo), bandNo2)
            writer.setEndTime(reader.endTime(bandNo), bandNo2)
            writer.setFwhm(reader.fwhm(bandNo), bandNo2)
            writer.setStartTime(reader.startTime(bandNo), bandNo2)
            writer.setWavelength(reader.wavelength(bandNo), bandNo2)
        writer.close()
        del ds

        layer = QgsRasterLayer(filename, basename(filename))

        if self.interfaceType == self.EnmapBoxInterface:
            mapDock = self.enmapBoxInterface().currentMapDock()
            if mapDock is None:
                self.enmapBoxInterface().onDataDropped([layer])
            else:
                mapDock.insertLayer(0, layer)
        elif self.interfaceType == self.QgisInterface:
            QgsProject.instance().addMapLayer(layer)
        else:
            raise ValueError()
