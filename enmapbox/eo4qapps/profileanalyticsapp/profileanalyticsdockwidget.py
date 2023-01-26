import traceback
import warnings
from dataclasses import dataclass
from os.path import exists, join, dirname
from shutil import copyfile
from typing import Optional, List, Dict

import numpy as np

import enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph as pg
import processing
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.widgets.codeeditwidget import CodeEditWidget
from enmapbox.qgispluginsupport.qps.plotstyling.plotstyling import PlotStyleButton, PlotStyle
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapboxprocessing.algorithm.subsetrasterbandsalgorithm import SubsetRasterBandsAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from geetimeseriesexplorerapp import MapTool
from profileanalyticsapp.profileanalyticseditorwidget import ProfileAnalyticsEditorWidget
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QComboBox, QTableWidget, QCheckBox, QToolButton, QLineEdit, QWidget
from qgis.core import QgsMapLayerProxyModel, QgsRasterLayer, QgsVectorLayer, QgsProcessingFeatureSourceDefinition, \
    QgsFeatureRequest, QgsWkbTypes
from qgis.gui import QgsMapLayerComboBox, QgsFileWidget, QgsRasterBandComboBox, QgsDockWidget, QgisInterface
from typeguard import typechecked, check_type


@typechecked
class ProfileAnalyticsDockWidget(QgsDockWidget):
    mGraphicsLayoutWidget: pg.GraphicsLayoutWidget

    # data tab
    mSourceType: QComboBox
    mRasterProfileType: QComboBox
    mTip1: QWidget
    mTip2: QWidget
    mRasterTable: QTableWidget
    mAddRaster: QToolButton
    mRemoveRaster: QToolButton
    mEditUserFunction: QToolButton
    mRemoveAllRaster: QToolButton

    # analytics tab
    mCode: CodeEditWidget

    mXUnit: QComboBox
    mLiveUpdate: QCheckBox
    mApply: QToolButton

    RasterLayerSource, = 0,
    ZProfileType, XProfileType, YProfileType, LineProfileType = 0, 1, 2, 3
    NumberUnits, NanometerUnits, DecimalYearUnits = 0, 1, 2
    EnmapBoxInterface, QgisInterface = 0, 1

    def __init__(self, currentLocationMapTool: Optional[MapTool], parent=None):
        QgsDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        self.currentLocationMapTool = currentLocationMapTool
        self.oldLineLayer: Optional[QgsVectorLayer] = None

        # set from outside
        self.interface = None
        self.interfaceType = None

        # connect signals
        self.mSourceType.currentIndexChanged.connect(self.onLiveUpdate)
        self.mRasterProfileType.currentIndexChanged.connect(self.onRasterProfileTypeChanged)
        self.mAddRaster.clicked.connect(self.onAddRasterClicked)
        self.mRemoveRaster.clicked.connect(self.onRemoveRasterClicked)
        self.mEditUserFunction.clicked.connect(self.onEditUserFunctionClicked)
        self.mRemoveAllRaster.clicked.connect(self.onmRemoveAllRasterClicked)
        self.mXUnit.currentIndexChanged.connect(self.onLiveUpdate)
        self.mApply.clicked.connect(self.onApplyClicked)

        # init gui
        self.mPlotWidget: pg.PlotItem = self.mGraphicsLayoutWidget.addPlot(row=1, col=0)
        self.mPlotWidget.showGrid(x=True, y=True, alpha=0.5)
        self.mPlotWidget.addLegend()
        self.mPlotWidget.legend.setOffset((0.3, 0.3))

        self.onRasterProfileTypeChanged()
        self.onAddRasterClicked()

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

        # connect current location changed signal
        if self.interfaceType == self.EnmapBoxInterface:
            self.enmapBoxInterface().sigCurrentLocationChanged.connect(self.onCurrentLocationChanged)
        elif self.interfaceType == self.QgisInterface:
            self.currentLocationMapTool.sigClicked.connect(self.onCurrentLocationChanged)
        else:
            raise ValueError()

        # connect current layer changed signal
        if self.interfaceType == self.EnmapBoxInterface:
            self.enmapBoxInterface().currentLayerChanged.connect(self.onCurrentLayerChanged)
        elif self.interfaceType == self.QgisInterface:
            self.qgisInterface().currentLayerChanged.connect(self.onCurrentLayerChanged)
        else:
            raise ValueError()

    def currentLayer(self) -> Optional[QgsVectorLayer]:
        if self.interfaceType == self.EnmapBoxInterface:
            layer = self.enmapBoxInterface().currentLayer()
        elif self.interfaceType == self.QgisInterface:
            layer = self.qgisInterface().activeLayer()
        else:
            raise ValueError()

        if not isinstance(layer, QgsVectorLayer):
            return None

        if layer.geometryType() != QgsWkbTypes.GeometryType.LineGeometry:
            return None

        return layer

    def onRasterProfileTypeChanged(self):
        isLineProfile = self.mRasterProfileType.currentIndex() == self.LineProfileType
        self.mTip1.setVisible(not isLineProfile)
        self.mTip2.setVisible(isLineProfile)

        self.onLiveUpdate()

    def onCurrentLayerChanged(self):

        # disconnect old layer
        try:
            self.oldLineLayer.selectionChanged.disconnect(self.onLayerSelectionChanged)
        except Exception:
            pass

        # connect new layer
        layer = self.currentLayer()
        if layer is None:
            return
        layer.selectionChanged.connect(self.onLayerSelectionChanged)

        self.oldLineLayer = layer

    def onLayerSelectionChanged(self):
        self.onLiveUpdate()

    def onAddRasterClicked(self):
        self.mRasterTable.setRowCount(self.mRasterTable.rowCount() + 1)
        row = self.mRasterTable.rowCount() - 1
        w = QgsMapLayerComboBox()
        w.setFilters(QgsMapLayerProxyModel.RasterLayer)
        w.setAllowEmptyLayer(True)
        w.setLayer(None)
        w.layerChanged.connect(self.onLiveUpdate)
        self.mRasterTable.setCellWidget(row, 0, w)

        w2 = QgsRasterBandComboBox()
        w.layerChanged.connect(w2.setLayer)
        w2.bandChanged.connect(self.onLiveUpdate)
        self.mRasterTable.setCellWidget(row, 1, w2)

        w = PlotStyleButton()
        w.setMinimumSize(5, 5)
        w.mDialog.sigPlotStyleChanged.connect(self.onLiveUpdate)
        self.mRasterTable.setCellWidget(row, 2, w)

        w = QLineEdit('0. + 1. * y')
        w.editingFinished.connect(self.onLiveUpdate)
        self.mRasterTable.setCellWidget(row, 3, w)

        w = QgsFileWidget()
        w.setFilter('*.py')
        w.setDefaultRoot(join(dirname(__file__), 'examples'))
        w.fileChanged.connect(self.onLiveUpdate)
        w.dialog = None
        self.mRasterTable.setCellWidget(row, 4, w)

        self.onLiveUpdate()

    def onRemoveRasterClicked(self):
        row = self.mRasterTable.currentRow()
        if row == -1:
            return
        self.mRasterTable.removeRow(row)

        self.onLiveUpdate()

    def onEditUserFunctionClicked(self):
        row = self.mRasterTable.currentRow()
        if row == -1:
            return
        w: QgsFileWidget = self.mRasterTable.cellWidget(row, 4)

        if w.filePath() == '':
            filename = join(Utils.getTempDirInTempFolder(), 'analytics.py')
            copyfile(join(dirname(__file__), 'examples', 'default.py'), filename)
            w.setFilePath(filename)

        filename = w.filePath()
        with open(filename) as file:
            text = file.read()

        w.dialog = ProfileAnalyticsEditorWidget(self)
        w.dialog.mFilename.setText(filename)
        w.dialog.mCode.setText(text)
        w.dialog.mSave.clicked.connect(self.onLiveUpdate)
        w.dialog.show()

    def onmRemoveAllRasterClicked(self):
        for i in reversed(range(self.mRasterTable.rowCount())):
            self.mRasterTable.removeRow(i)

    def onCurrentLocationChanged(self):
        self.onLiveUpdate()

    def onLiveUpdate(self):
        if not self.mLiveUpdate.isChecked():
            return
        self.onApplyClicked()

    def onApplyClicked(self):

        if self.interface is None:  # not yet initialized
            return

        if not self.isUserVisible():
            return

        self.mPlotWidget.clear()

        if self.mSourceType.currentIndex() == self.RasterLayerSource:
            profiles = list()
            userFunctions = list()
            userFunctionEditors = list()
            # read and analyse profiles
            for row in range(self.mRasterTable.rowCount()):
                w: QgsMapLayerComboBox = self.mRasterTable.cellWidget(row, 0)
                layer: QgsRasterLayer = w.currentLayer()
                if layer is None:
                    continue

                w: QgsRasterBandComboBox = self.mRasterTable.cellWidget(row, 1)

                if self.mRasterProfileType.currentIndex() != self.ZProfileType:
                    bandNo: int = w.currentBand()
                    if bandNo == -1:
                        return

                if self.mRasterProfileType.currentIndex() != self.LineProfileType:
                    point = self.currentLocation()
                    if point is None:
                        return
                    pixel = point.toPixel(layer)
                    if pixel is None:
                        continue
                else:
                    pixel = None

                # read data
                reader = RasterReader(layer)
                if self.mRasterProfileType.currentIndex() == self.ZProfileType:
                    name = f'{layer.name()} [column {pixel.x() + 1}, row {pixel.y() + 1}]'
                    yValues = reader.arrayFromPixelOffsetAndSize(pixel.x(), pixel.y(), 1, 1)
                    yMaskValues = reader.maskArray(np.array(yValues))
                    if self.mXUnit.currentIndex() == self.NumberUnits:
                        xUnit = 'band numbers'
                        xValues = list(range(1, len(yValues) + 1))
                    elif self.mXUnit.currentIndex() == self.NanometerUnits:
                        xUnit = 'nanometers'
                        xValues = [reader.wavelength(bandNo) for bandNo in reader.bandNumbers()]
                    elif self.mXUnit.currentIndex() == self.DecimalYearUnits:
                        xUnit = 'decimal year'
                        xValues = [Utils.dateTimeToDecimalYear(reader.centerTime(bandNo))
                                   for bandNo in reader.bandNumbers()]
                    else:
                        raise ValueError()
                elif self.mRasterProfileType.currentIndex() == self.XProfileType:
                    name = f'{layer.name()} [band {bandNo}, row {pixel.y() + 1}]'
                    yValues = np.array(reader.arrayFromPixelOffsetAndSize(0, pixel.y(), reader.width(), 1, [bandNo]))
                    yMaskValues = np.array(reader.maskArray(np.array(yValues), [bandNo]))
                    xValues = list(range(1, reader.width() + 1))
                    xUnit = 'column numbers'
                elif self.mRasterProfileType.currentIndex() == self.YProfileType:
                    name = f'{layer.name()} [band {bandNo}, column {pixel.x() + 1}]'
                    yValues = np.array(reader.arrayFromPixelOffsetAndSize(pixel.x(), 0, 1, reader.height(), [bandNo]))
                    yMaskValues = np.array(reader.maskArray(np.array(yValues), [bandNo]))
                    xValues = list(range(1, reader.height() + 1))
                    xUnit = 'row numbers'
                elif self.mRasterProfileType.currentIndex() == self.LineProfileType:
                    lineLayer: QgsVectorLayer = self.currentLayer()
                    if lineLayer is None:
                        return

                    selectedFeatureCount = lineLayer.selectedFeatureCount()
                    if selectedFeatureCount == 0:
                        return
                    elif selectedFeatureCount > 1:
                        warnings.warn('handling multiple lines is not yet implemented')
                        return

                    lineId = lineLayer.selectedFeatureIds()[0]
                    name = f'{layer.name()} [band {bandNo}, line ID {lineId}]'

                    # 1. reproject line feature to layer CRS
                    alg = 'native:reprojectlayer'
                    parameters = {
                        'INPUT': QgsProcessingFeatureSourceDefinition(
                            lineLayer.source(), selectedFeaturesOnly=True, featureLimit=-1,
                            geometryCheck=QgsFeatureRequest.InvalidGeometryCheck.GeometryAbortOnInvalid),
                        'TARGET_CRS': reader.crs(),
                        'OUTPUT': 'TEMPORARY_OUTPUT'
                    }
                    lineLayer2: QgsVectorLayer = processing.run(alg, parameters)['OUTPUT']

                    # 2. Use Points along geometry algorithm to generate sampling locations
                    samplingDistance = (reader.rasterUnitsPerPixelX() + reader.rasterUnitsPerPixelY()) / 2
                    alg = 'native:pointsalonglines'
                    parameters = {
                        'INPUT': lineLayer2,
                        'DISTANCE': samplingDistance,
                        'START_OFFSET': 0,
                        'END_OFFSET': 0,
                        # 'OUTPUT': r'C:\Users\Andreas\Downloads\points.gpkg'  # 'TEMPORARY_OUTPUT'
                        'OUTPUT': 'TEMPORARY_OUTPUT'
                    }
                    pointLayer = processing.run(alg, parameters)['OUTPUT']

                    # 3. Sample raster band values
                    # a) subset band
                    alg = SubsetRasterBandsAlgorithm()
                    parameters = {
                        'raster': layer,
                        'bandList': [bandNo],
                        'outputRaster': 'TEMPORARY_OUTPUT'
                    }
                    rasterLayer = processing.run(alg, parameters)['outputRaster']
                    # b) sample values
                    alg = 'native:rastersampling'
                    parameters = {
                        'INPUT': pointLayer,
                        'RASTERCOPY': rasterLayer,
                        'COLUMN_PREFIX': 'SAMPLE_',
                        'OUTPUT': 'TEMPORARY_OUTPUT'
                        # 'OUTPUT': r'C:\Users\Andreas\Downloads\sample.gpkg' # 'TEMPORARY_OUTPUT'
                    }
                    pointLayer2: QgsVectorLayer = processing.run(alg, parameters)['OUTPUT']
                    xValues = [feature['distance'] for feature in pointLayer2.getFeatures()]
                    yValues = [feature['SAMPLE_1'] for feature in pointLayer2.getFeatures()]
                    yValues = [np.nan if value is None else value for value in yValues]
                    yMaskValues = reader.maskArray(np.array(yValues).reshape((1, 1, -1)), [bandNo])
                    xUnit = 'distance from line start'
                else:
                    raise ValueError()
                xValues = np.array(xValues)
                yValues = np.array(yValues).flatten()
                yMaskValues = np.array(yMaskValues).flatten()

                # mask no data values
                xMaskValues = [value is not None for value in xValues]
                valid = np.logical_and(xMaskValues, yMaskValues)
                xValues = list(xValues[valid].astype(np.float32))
                yValues = list(yValues[valid].astype(np.float32))
                if len(xValues) == 0:
                    continue

                w: PlotStyleButton = self.mRasterTable.cellWidget(row, 2)
                style = w.plotStyle()

                w: QLineEdit = self.mRasterTable.cellWidget(row, 3)
                formular = w.text()
                try:
                    offset, tmp = formular.split('+')
                    scale, _ = tmp.split('*')
                    offset = float(offset)
                    scale = float(scale)
                    if offset != 0 or scale != 1:
                        yValues = [offset + scale * y for y in yValues]
                except Exception:
                    pass

                w: QgsFileWidget = self.mRasterTable.cellWidget(row, 4)
                filename = w.filePath()
                userFunction = None
                if exists(filename):
                    namespace = dict()
                    with open(filename) as file:
                        code = file.read()
                    try:
                        exec(code, namespace)
                        userFunction = namespace['updatePlot']
                    except Exception:
                        pass
                userFunctionEditor = w.dialog

                profile = Profile(xValues, yValues, xUnit, name, style)
                profiles.append(profile)
                userFunctions.append(userFunction)
                userFunctionEditors.append(userFunctionEditor)
        else:
            raise ValueError()

        # plot profiles and call user functions
        for profile, ufunc, dialog in zip(profiles, userFunctions, userFunctionEditors):
            plotDataItem: pg.PlotDataItem = self.mPlotWidget.plot(profile.xValues, profile.yValues, name=profile.name)
            profile.style.apply(plotDataItem)
            if ufunc is not None:
                try:
                    ufunc(profile, profiles, self.mPlotWidget)
                    msg = 'Done!'
                except Exception:
                    traceback.print_exc()
                    msg = traceback.format_exc()

                if dialog is not None:
                    assert isinstance(dialog, ProfileAnalyticsEditorWidget)
                    dialog.mLog.setText(msg)

        # set x axis title
        if self.mSourceType.currentIndex() == self.RasterLayerSource:
            if self.mRasterProfileType.currentIndex() == self.ZProfileType:
                xtitle = self.mXUnit.currentText()
            elif self.mRasterProfileType.currentIndex() == self.XProfileType:
                xtitle = 'Column Number'
            elif self.mRasterProfileType.currentIndex() == self.YProfileType:
                xtitle = 'Row Number'
            elif self.mRasterProfileType.currentIndex() == self.LineProfileType:
                xtitle = 'Distance from line start'
            else:
                raise ValueError()
        else:
            raise ValueError()

        axis: pg.AxisItem = self.mPlotWidget.getAxis('bottom')
        axis.setLabel(text=xtitle, units=None, unitPrefix=None)

        # update widgets
        if all((
                self.mSourceType.currentIndex() == self.RasterLayerSource,
                self.mRasterProfileType.currentIndex() == self.ZProfileType
        )):
            self.mXUnit.setEnabled(True)
        else:
            self.mXUnit.setEnabled(False)

    def currentLocation(self) -> Optional[SpatialPoint]:
        if self.interfaceType == self.EnmapBoxInterface:
            return self.enmapBoxInterface().currentLocation()
        elif self.interfaceType == self.QgisInterface:
            return self.currentLocationMapTool.currentLocation()
        else:
            raise ValueError()

    def projectSettingsKey(self) -> str:
        return self.__class__.__name__

    def projectSettings(self) -> Dict:
        return {
            'mSourceType.currentIndex': self.mSourceType.currentIndex(),
            'mRasterProfileType.currentIndex': self.mRasterProfileType.currentIndex()
        }

    def setProjectSettings(self, settings: Dict):
        self.mSourceType.setCurrentIndex(settings['mSourceType.currentIndex'])
        self.mRasterProfileType.setCurrentIndex(settings['mRasterProfileType.currentIndex'])


@typechecked
@dataclass
class Profile(object):
    xValues: List[float]
    yValues: List[float]
    xUnit: str
    name: str
    style: PlotStyle

    def __post_init__(self):
        assert len(self.xValues) == len(self.yValues)
        check_type('style', self.style, PlotStyle)
