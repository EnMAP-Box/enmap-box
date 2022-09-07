import json
import warnings
import webbrowser
from collections import OrderedDict
from math import isnan, isfinite
from os import listdir, makedirs
from os.path import join, exists, dirname, basename, splitext
from traceback import print_exc
from typing import Optional, Dict, List, Tuple

from enmapbox import EnMAPBox
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint, SpatialExtent
from enmapbox.utils import importEarthEngine
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.utils import Utils
from geetimeseriesexplorerapp.codeeditwidget import CodeEditWidget
from geetimeseriesexplorerapp.collectioninfo import CollectionInfo
from geetimeseriesexplorerapp.externals.ee_plugin.provider import GeetseEarthEngineRasterDataProvider
from geetimeseriesexplorerapp.imageinfo import ImageInfo
from geetimeseriesexplorerapp.tasks.queryavailableimagestask import QueryAvailableImagesTask
from geetimeseriesexplorerapp.utils import utilsMsecToDateTime
from qgis.PyQt import QtGui
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QLocale, QDate, pyqtSignal, QModelIndex, QDateTime
from qgis.PyQt.QtGui import QPixmap, QColor, QIcon
from qgis.PyQt.QtWidgets import (QToolButton, QApplication, QComboBox, QLineEdit,
                                 QTableWidget, QDateEdit, QRadioButton, QListWidget, QCheckBox, QTableWidgetItem,
                                 QPlainTextEdit, QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel, QMainWindow,
                                 QListWidgetItem, QProgressBar, QFrame)
from qgis.core import QgsRasterLayer, QgsCoordinateReferenceSystem, QgsMapLayer, QgsMapSettings, \
    QgsColorRamp, QgsDateTimeRange, QgsApplication, QgsMessageLog, Qgis
from qgis.gui import (
    QgsDockWidget, QgsMessageBar, QgsColorRampButton, QgsSpinBox, QgsMapCanvas, QgsDateTimeEdit, QgisInterface
)
from typeguard import typechecked


@typechecked
class GeeTimeseriesExplorerDockWidget(QgsDockWidget):
    mMessageBar: QgsMessageBar
    mIconList: QListWidget

    # data catalog
    mUserCollection: QTableWidget
    mCollectionTitle: QLineEdit
    mOpenCatalog: QToolButton
    mOpenJson: QToolButton

    # collection metadata
    mCollectionMetadata: QPlainTextEdit

    # collection editor
    mPredefinedCollection: QComboBox
    mOpenDescription: QToolButton
    mCode: CodeEditWidget
    mLoadCollection: QToolButton

    # band properties
    mScaleBands: QCheckBox
    mBandProperty: QTableWidget

    # spectral indices
    mAsiVegatation: QListWidget
    mAsiBurn: QListWidget
    mAsiWater: QListWidget
    mAsiSnow: QListWidget
    mAsiDrought: QListWidget
    mAsiUrban: QListWidget
    mAsiOther: QListWidget

    # filtering
    mFilterDateStart: QDateEdit
    mFilterDateEnd: QDateEdit
    mFilterProperties: QTableWidget
    mFilterBitmask: QTreeWidget

    # symbology
    mRendererType: QComboBox
    mVisualization: QComboBox
    mRedBand: QComboBox
    mGreenBand: QComboBox
    mBlueBand: QComboBox
    mPseudoColorBand: QComboBox
    mRedMin: QLineEdit
    mGreenMin: QLineEdit
    mBlueMin: QLineEdit
    mPseudoColorMin: QLineEdit
    mRedMax: QLineEdit
    mGreenMax: QLineEdit
    mBlueMax: QLineEdit
    mPseudoColorMax: QLineEdit
    mReducerRed: QComboBox
    mReducerGreen: QComboBox
    mReducerBlue: QComboBox
    mReducerPseudoColor: QComboBox
    mPseudoColorRamp: QgsColorRampButton

    mCalculatePercentiles: QToolButton
    mPercentileMinMax: QRadioButton
    mPercentileMin: QgsSpinBox
    mPercentileMax: QgsSpinBox

    # image explorer
    mImageExplorerTab: QTabWidget
    mImageExtent: QComboBox
    mLimitImages: QCheckBox
    mLimitImagesValue: QgsSpinBox
    mLiveQueryAvailableImages: QCheckBox
    mQueryAvailableImages: QToolButton
    mCopyAvailableImages: QToolButton
    mCopyImageInfo: QToolButton
    mShowImageInfo: QToolButton
    mAvailableImages: QTableWidget
    mImageId: QLineEdit

    # - compositing and mosaicking
    mCompositeDateStart: QDateEdit
    mCompositeDateEnd: QDateEdit
    mCompositeSeasonStart: QDateEdit
    mCompositeSeasonEnd: QDateEdit
    mReducerType: QTabWidget
    mReducerUniform: QComboBox
    mReducerBandWise: QTableWidget
    mCompositeExtent: QComboBox

    # update layer
    mAppendName: QCheckBox
    mLayerName: QLineEdit
    mAppendId: QCheckBox
    mAppendDate: QCheckBox
    mAppendBandNames: QCheckBox
    mLayerNamePreview: QLineEdit
    mCenterLayer: QToolButton
    mLiveStretchLayer: QCheckBox
    mLiveUpdateLayer: QCheckBox
    mUpdateLayer: QToolButton
    mStretchAndUpdateLayer: QToolButton
    mTemporalEnabled: QCheckBox
    mTemporalRangeValue: QgsSpinBox
    mTemporalRangeUnits: QComboBox
    mTemporalStartFixed: QCheckBox
    mTemporalEndFixed: QCheckBox
    mTemporalStart: QgsDateTimeEdit
    mTemporalEnd: QgsDateTimeEdit

    mProgressBarFrame: QFrame
    mProgressBar: QProgressBar
    mCancelTaskManager: QToolButton

    # additional typing

    sigCollectionChanged = pyqtSignal()

    def __init__(self, parent=None):
        # eeImported, ee = importEarthEngine(False)

        QgsDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        # those are set from outside
        from geetimeseriesexplorerapp import GeeTemporalProfileDockWidget
        self.profileDock: GeeTemporalProfileDockWidget
        self.interface: QgisInterface

        self.eeInitialized = False
        # self._currentCollection: Optional[ee.ImageCollection]
        self.backgroundLayer = QgsRasterLayer(
            'type=xyz&url=https://mt1.google.com/vt/lyrs%3Dm%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0',
            'Google Maps', 'wms'
        )
        self.epsg4326 = 'EPSG:4326'
        self.crsEpsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        # self.eeFullCollection: Optional[ee.ImageCollection]
        self.eeFullCollection = None
        self.eeFullCollectionInfo: Optional[ImageInfo] = None
        self.eeFullCollectionJson: Optional[CollectionInfo] = None
        self.cache = dict()
        self.refs = list()  # keep refs to prevent crashes

        # list
        self.mIconList.setCurrentRow(0)

        # data catalog
        self.initDataCatalog()
        self.mUserCollection.itemSelectionChanged.connect(self.onCollectionClicked)
        self.mOpenCatalog.clicked.connect(self.onOpenCatalogClicked)
        self.mOpenJson.clicked.connect(self.onOpenJsonClicked)
        self.mLoadCollection.clicked.connect(self.onLoadCollectionClicked)

        self.mCode.setReadOnly(True)
        self.mLoadCollection.hide()

        # spectral indices
        self.initSpectralIndices()

        # symbology
        self.mGroupBoxBandRendering.setCollapsed(False)
        self.mGroupBoxMinMax.setCollapsed(False)
        self.mPseudoColorRamp.setColorRampFromName('RdYlGn')
        self.mPercentileMin.setClearValue(self.mPercentileMin.value())
        self.mPercentileMax.setClearValue(self.mPercentileMax.value())

        self.mVisualization.currentIndexChanged.connect(self.onVisualizationChanged)
        self.mRedBand.currentIndexChanged.connect(self.onBandChanged)
        self.mGreenBand.currentIndexChanged.connect(self.onBandChanged)
        self.mBlueBand.currentIndexChanged.connect(self.onBandChanged)
        self.mPseudoColorBand.currentIndexChanged.connect(self.onBandChanged)
        self.mCalculatePercentiles.clicked.connect(self.calculateCumulativeCountCutStretch)

        # image explorer
        self.mCenterLayer.clicked.connect(self.onCenterLayerClicked)
        self.mUpdateLayer.clicked.connect(self.onUpdateLayerClicked)
        self.mStretchAndUpdateLayer.clicked.connect(self.onStretchAndUpdateLayerClicked)
        # - image viewer
        self.mQueryAvailableImages.clicked.connect(self.queryAvailableImages)
        self.mCopyAvailableImages.clicked.connect(self.copyAvailableImages)
        self.mCopyImageInfo.clicked.connect(self.copyImageInfo)
        self.mShowImageInfo.clicked.connect(self.showImageInfo)
        self.mAvailableImages.itemSelectionChanged.connect(self.onAvailableImagesSelectionChanged)
        self.mAvailableImages.horizontalHeader().setSectionsMovable(True)
        self.mImageId.textChanged.connect(self.onImageIdChanged)
        # - compositing and mosaicking
        self.mCompositeSeasonStart.setLocale(QLocale(QLocale.English, QLocale.UnitedKingdom))
        self.mCompositeSeasonEnd.setLocale(QLocale(QLocale.English, QLocale.UnitedKingdom))

        # update layer bar
        self.mImageExplorerTab.currentChanged.connect(self.updateLayerNamePreview)
        self.mImageId.textChanged.connect(self.updateLayerNamePreview)
        self.mLayerName.textChanged.connect(self.updateLayerNamePreview)
        for w in [self.mAppendName, self.mAppendId, self.mAppendDate, self.mAppendBandNames]:
            w.toggled.connect(self.updateLayerNamePreview)

        # task manager
        # self.taskManager = QgsTaskManager()  # using this manager gives me crashes, when connected to a progress bar
        self.taskManager = QgsApplication.taskManager()
        self.taskManager.taskAdded.connect(self.mProgressBarFrame.show)
        self.taskManager.allTasksFinished.connect(self.mProgressBarFrame.hide)
        self.mCancelTaskManager.clicked.connect(self.taskManager.cancelAll)
        self.mProgressBarFrame.hide()
        self.mProgressBar.setRange(0, 0)

    def enmapBoxInterface(self) -> EnMAPBox:
        return self.interface

    def qgisInterface(self) -> QgisInterface:
        return self.interface

    def setProfileDock(self, profileDock):
        from geetimeseriesexplorerapp import GeeTemporalProfileDockWidget
        assert isinstance(profileDock, GeeTemporalProfileDockWidget)
        self.profileDock = profileDock

    class InterfaceType(object):
        EnmapBox = 0
        Qgis = 1

    def setInterface(self, interface: QgisInterface):
        self.interface = interface
        if isinstance(interface, EnMAPBox):
            self.interfaceType = 0
        elif isinstance(interface, QgisInterface):
            self.interfaceType = 1
        else:
            raise ValueError()

        # connect current location changed signal
        if self.interfaceType == self.InterfaceType.EnmapBox:
            self.interface.sigCurrentLocationChanged.connect(self.profileDock.setCurrentLocationFromEnmapBox)
        elif self.interfaceType == self.InterfaceType.Qgis:
            pass  # connected outside
        else:
            raise ValueError()

    def initSpectralIndices(self):
        mAsiLists = {
            'vegetation': self.mAsiVegatation, 'burn': self.mAsiBurn, 'water': self.mAsiWater, 'snow': self.mAsiSnow,
            'drought': self.mAsiDrought, 'urban': self.mAsiUrban, 'other': self.mAsiOther
        }
        for name, spec in CreateSpectralIndicesAlgorithm.IndexDatabase.items():
            mList: QListWidget = mAsiLists.get(spec['type'])
            if mList is None:
                continue
            item = QListWidgetItem(f"{spec['short_name']}: {spec['long_name']}")
            item.setToolTip(f"{spec['formula']}")
            item.setCheckState(Qt.Unchecked)
            item.spec = spec
            mList.addItem(item)

        for mList in mAsiLists.values():
            mList.itemChanged.connect(self.onSpectralIndexChecked)

    def updateSpectralIndices(self):
        availableAsiBands = list(self.eeFullCollectionInfo.wavebandMapping.keys())
        availableAsiBands.extend(list(CreateSpectralIndicesAlgorithm.ConstantMapping.keys()))
        availableAsiBands = set(availableAsiBands)

        mLists = [self.mAsiVegatation, self.mAsiBurn, self.mAsiWater, self.mAsiSnow, self.mAsiDrought, self.mAsiUrban,
                  self.mAsiOther]
        for mList in mLists:
            mList.blockSignals(True)
            for row in range(mList.count()):
                item = mList.item(row)
                spec = item.spec

                # - check all indices that have a default color specified
                if spec['short_name'] in self.eeFullCollectionInfo.defaultBandColors:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)

                # - disable all indices that can't be calculated
                requiredAsiBands = spec['bands']
                if len(availableAsiBands.intersection(requiredAsiBands)) < len(requiredAsiBands):
                    item.setForeground(QColor(0, 0, 0, 128))
                    item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
                else:
                    item.setForeground(QColor(0, 0, 0, 255))
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            mList.blockSignals(False)

    def onSpectralIndexChecked(self):
        self.updateBandRendering()
        self.sigCollectionChanged.emit()

    def selectedSpectralIndices(self) -> List[Dict]:
        specs = list()
        mLists = [self.mAsiVegatation, self.mAsiBurn, self.mAsiWater, self.mAsiSnow, self.mAsiDrought, self.mAsiUrban,
                  self.mAsiOther]
        for mList in mLists:
            for row in range(mList.count()):
                item = mList.item(row)
                if item.checkState() == Qt.Checked:
                    specs.append(item.spec)
        return specs

    def initDataCatalog(self):
        self.mOpenCatalog.url = 'https://developers.google.com/earth-engine/datasets'

        self.mLANDSAT_LC09_C02_T1_L2.clicked.connect(self.onCollectionClicked)
        self.mLANDSAT_LC08_C02_T1_L2.clicked.connect(self.onCollectionClicked)
        self.mLANDSAT_LE07_C02_T1_L2.clicked.connect(self.onCollectionClicked)
        self.mLANDSAT_LT05_C02_T1_L2.clicked.connect(self.onCollectionClicked)
        self.mLANDSAT_LT04_C02_T1_L2.clicked.connect(self.onCollectionClicked)

        self.mMODIS_006_MCD43A4.clicked.connect(self.onCollectionClicked)
        self.mMODIS_006_MOD09GQ.clicked.connect(self.onCollectionClicked)
        self.mMODIS_006_MOD09GA.clicked.connect(self.onCollectionClicked)
        self.mMODIS_006_MOD09Q1.clicked.connect(self.onCollectionClicked)
        self.mMODIS_006_MOD09A1.clicked.connect(self.onCollectionClicked)

        self.mCOPERNICUS_S1_GRD.clicked.connect(self.onCollectionClicked)
        self.mCOPERNICUS_S2_SR.clicked.connect(self.onCollectionClicked)
        self.mCOPERNICUS_S3_OLCI.clicked.connect(self.onCollectionClicked)

        self.mEO1_HYPERION.clicked.connect(self.onCollectionClicked)

        self.mLANDSAT_COMBINED_C02_T1_L2.clicked.connect(self.onUserCollectionClicked)

        # load user defined collections
        @typechecked
        class UserCollection():

            def __init__(self, pyFilename: str):
                self.id = splitext(basename(pyFilename))[0]
                self.title = ''
                self.pyFilename = pyFilename
                info = dict()
                if exists(pyFilename.replace('.py', '.json')):
                    self.jsonUrl = pyFilename.replace('.py', '.json')
                    self.title = Utils.jsonLoad(self.jsonUrl)['title']
                else:
                    with open(pyFilename) as file:
                        for line in file.readlines():
                            for key, prefix in [('title', '# Title:'), ('id', '# ID:')]:
                                if line.startswith(prefix):
                                    info[key] = line.replace(prefix, '').strip()
                    self.id = info.get('id', self.id)
                    self.title = info.get('title', self.title)

                    subfolder = self.id.split('_')[0]
                    self.jsonUrl = f'https://earthengine-stac.storage.googleapis.com/catalog/{subfolder}/{self.id}.json'

        root = join(dirname(__file__), 'user_collections')
        self.userCollections = [UserCollection(join(root, name)) for name in listdir(root) if name.endswith('.py')]
        self.mUserCollection.setRowCount(len(self.userCollections))
        for row, userCollection in enumerate(self.userCollections):
            self.mUserCollection.setCellWidget(row, 0, QLabel(userCollection.id))
            self.mUserCollection.setCellWidget(row, 1, QLabel(userCollection.title))
        self.mUserCollection.resizeColumnsToContents()

    def onVisualizationChanged(self):
        if self.mVisualization.currentIndex() > 0:
            v = self.eeFullCollectionJson.visualizations()[self.mVisualization.currentIndex() - 1]
            bandNames = v['image_visualization']['band_vis']['bands']
            for bandName, mBand in zip(bandNames, (self.mRedBand, self.mGreenBand, self.mBlueBand)):
                mBand.blockSignals(True)
                mBand.setCurrentText(bandName)
                mBand.blockSignals(False)

    def onBandChanged(self):
        self.mVisualization.setCurrentIndex(0)

    def onAvailableImagesSelectionChanged(self):
        indices = self.mAvailableImages.selectedIndexes()
        if len(indices) == 0:
            return

        # set last image as current image
        index = indices[-1]
        imageId = self.mAvailableImages.item(index.row(), 0).data(Qt.DisplayRole)
        self.mImageId.setText(imageId)

    def onImageIdChanged(self):
        if self.mLiveStretchLayer.isChecked():
            # self.mStretchAndUpdateLayer.click()
            # self.onUpdateLayerClicked()
            self.onStretchAndUpdateLayerClicked()
        else:
            if self.mLiveUpdateLayer.isChecked():
                # self.mUpdateLayer.click()
                self.onUpdateLayerClicked()

        # select image in data table
        imageId = self.currentImageId()
        if imageId is not None:
            self.profileDock.mData.blockSignals(True)
            self.profileDock.setCurrentDataSelectionId(imageId)
            self.profileDock.mData.blockSignals(False)

        self.profileDock.plotProfile()

    def onCurrentLocationChanged(self):
        if self.mLiveQueryAvailableImages.isChecked():
            self.mQueryAvailableImages.click()

    def onLoadCollectionClicked(self):
        eeImported, ee = importEarthEngine(False)
        self.eeInitialize()

        namespace = dict(ee=ee)
        code = self.mCode.text()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec(code, namespace)

        with GeeWaitCursor():
            try:
                eeCollection = namespace['collection']
                assert isinstance(eeCollection, ee.ImageCollection)
            except Exception as error:
                self.mMessageBar.pushCritical('Error', str(error))
                self.eeFullCollection = None
                self.eeFullCollectionInfo = None
                return

        self.eeFullCollection = eeCollection
        self.eeFullCollectionInfo = ImageInfo(eeCollection.first().getInfo())
        self.eeFullCollectionInfo.addDefaultBandColors(namespace.get('bandColors', {}))
        self.eeFullCollectionInfo.addDefaultQaFlags(namespace.get('qaFlags', {}))
        self.eeFullCollectionInfo.addWavebandMappings(namespace.get('wavebandMapping', {}))
        self.updateBandProperties()
        self.updateSpectralIndices()
        self.updateFilterProperties(namespace.get('propertyNames'))
        self.updateFilterBitmask()
        self.updateBandRendering()
        self.updateReducer()
        self.mVisualization.setCurrentIndex(1)
        self.mMessageBar.pushSuccess('Success', 'Image Collection loaded')

        self.sigCollectionChanged.emit()

    def onCenterLayerClicked(self):
        layer = self.currentLayer()
        mapCanvas = self.currentMapCanvas()
        if layer is None or mapCanvas is None:
            return

        if self.mImageExplorerTab.currentIndex() == 0:
            layer = self.currentLayer()
            if layer.customProperty('ee-layer'):
                provider: GeetseEarthEngineRasterDataProvider = layer.dataProvider()
                centroid = SpatialPoint(
                    'EPSG:4326', *provider.eeImage.geometry().centroid(0.01).getInfo()['coordinates']
                ).toCrs(self.currentCrs())
                mapCanvas.setCenter(centroid)
            else:
                raise NotImplementedError()

        if self.mImageExplorerTab.currentIndex() == 1:
            raise NotImplementedError()

        mapCanvas.refresh()

    def onUpdateLayerClicked(self, cumulativeCountCut=False):

        layerName = self.currentLayerName()

        if self.mImageExplorerTab.currentIndex() == 0:  # image viewer

            if self.eeImage() is None:
                return

            eeImageProfile, eeImageRgb, visParams, visBands = self.eeImage()
            self.createWmsLayer(eeImageProfile, eeImageRgb, visParams, layerName)

        elif self.mImageExplorerTab.currentIndex() == 1:  # compositing

            if self.eeComposite() is None:
                return

            eeCompositeProfile, eeCompositeRgb, visParams = self.eeComposite()
            self.createWmsLayer(eeCompositeProfile, eeCompositeRgb, visParams, layerName)

        else:
            raise ValueError()

    def onStretchAndUpdateLayerClicked(self):
        self.calculateCumulativeCountCutStretch()
        self.onUpdateLayerClicked()

    def onOpenCatalogClicked(self):
        webbrowser.open_new_tab(self.mOpenCatalog.url)

    def onOpenJsonClicked(self):
        webbrowser.open_new_tab(self.mOpenJson.url)

    def onUserCollectionClicked(self):
        button = self.sender()
        assert isinstance(button, QToolButton)
        id = button.objectName()[1:]
        for row in range(self.mUserCollection.rowCount()):
            if self.mUserCollection.cellWidget(row, 0).text() == id:
                self.mUserCollection.selectRow(row)
                return
        raise RuntimeError(f'unknown collection: {id}')

    def loadJsonUrlData(self, jsonUrl: str) -> Dict:
        if exists(jsonUrl):
            data = Utils.jsonLoad(jsonUrl)
        else:
            with GeeWaitCursor():
                try:
                    import urllib.request
                    import json
                    with urllib.request.urlopen(jsonUrl) as url:
                        data = json.loads(url.read().decode())
                except Exception as error:
                    QgsMessageLog.logMessage(
                        f'url not found: {jsonUrl}', tag="GEE Time Series Explorer", level=Qgis.MessageLevel.Critical
                    )
                    self.mMessageBar.pushCritical('Error', str(error))
                    self.eeFullCollectionJson = None
                    raise error
        return data

    def onCollectionClicked(self):

        # https://earthengine-stac.storage.googleapis.com/catalog/catalog.json  # main catalog
        #    https://earthengine-stac.storage.googleapis.com/catalog/LANDSAT/catalog.json  # sub catalog
        #        https://earthengine-stac.storage.googleapis.com/catalog/LANDSAT/LANDSAT_LC08_C02_T1_L2.json  # collection

        if isinstance(self.sender(), QToolButton):
            self.mUserCollection.clearSelection()
            mCollection: QToolButton = self.sender()
            id = mCollection.objectName()[1:]
            subfolder = id.split('_')[0]
            jsonUrl = f'https://earthengine-stac.storage.googleapis.com/catalog/{subfolder}/{id}.json'
            pyFilename = join(dirname(__file__), 'standard_collections', id + '.py')
        elif isinstance(self.sender(), QTableWidget):
            indices: List[QModelIndex] = self.mUserCollection.selectedIndexes()
            if len(indices) == 0:
                return
            collection = self.userCollections[indices[0].row()]
            jsonUrl = collection.jsonUrl
            pyFilename = collection.pyFilename
        else:
            assert 0

        data = self.loadJsonUrlData(jsonUrl)
        code = Utils.fileLoad(pyFilename)
        code = f'# {basename(pyFilename)} ({pyFilename})\n\n' + code

        self.eeFullCollectionJson = CollectionInfo(data)
        self.mOpenCatalog.url = self.eeFullCollectionJson.googleEarthEngineUrl()
        self.mOpenJson.url = jsonUrl

        # update GUI and load collection
        self.mCollectionTitle.setText(data['title'])
        self.mCollectionTitle.setCursorPosition(0)
        self.mCode.setText(code)
        self.mAvailableImages.setRowCount(0)
        self.mAvailableImages.setColumnCount(2)
        self.mImageId.setText('')
        self.onLoadCollectionClicked()

    def eeInitialize(self):
        eeImported, ee = importEarthEngine(False)
        if not self.eeInitialized:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ee.Initialize()
        self.eeInitialized = True

    def currentImageLayerTemporalRange(self) -> Optional[QgsDateTimeRange]:
        if self.mTemporalEnabled:
            if self.mTemporalStartFixed:
                start = self.mTemporalStart.dateTime()
            else:
                start = QDateTime()  # the bound is considered to be infinite
            if self.mTemporalEndFixed:
                end = self.mTemporalEnd.dateTime()
            else:
                end = QDateTime()  # the bound is considered to be infinite
            return QgsDateTimeRange(start, end)
        else:
            return None

    def updateBandProperties(self):
        self.mBandProperty.setRowCount(len(self.eeFullCollectionInfo.bandNames))

        for i, bandName in enumerate(self.eeFullCollectionInfo.bandNames):
            wavelength = self.eeFullCollectionJson.bandWavelength(i + 1)
            if isnan(wavelength):
                wavelength = ''
            offset = self.eeFullCollectionJson.bandOffset(i + 1)
            if offset == 0.:
                offset = ''
            scale = self.eeFullCollectionJson.bandScale(i + 1)
            if scale == 1.:
                scale = ''
            sname = self.eeFullCollectionInfo.wavebandMapping.get(bandName)
            if sname is None:
                waveband = ''
            else:
                lname = CreateSpectralIndicesAlgorithm.LongNameMapping[sname]
                waveband = f' ({lname})'

            showInZProfile = QCheckBox()
            showInZProfile.setCheckState(Qt.Checked)
            label = self.eeFullCollectionJson.bandDescription(i + 1)

            self.mBandProperty.setCellWidget(i, 0, QLabel(bandName))
            self.mBandProperty.setCellWidget(i, 1, QLabel(f'{wavelength}{waveband}'))
            self.mBandProperty.setCellWidget(i, 2, QLabel(str(offset)))
            self.mBandProperty.setCellWidget(i, 3, QLabel(str(scale)))
            self.mBandProperty.setCellWidget(i, 4, showInZProfile)
            self.mBandProperty.setCellWidget(i, 5, QLabel(label))
        self.mBandProperty.resizeColumnsToContents()
        self.mBandProperty.horizontalHeader().setStretchLastSection(True)

    def updateFilterProperties(self, propertyNames: List[str] = None):
        self.mFilterProperties.setRowCount(10)
        operators = [
            '', 'equals', 'less_than', 'greater_than', 'not_equals', 'not_less_than', 'not_greater_than', 'starts_with',
            'ends_with', 'not_starts_with', 'not_ends_with', 'contains', 'not_contains'
        ]

        if propertyNames is None:
            propertyNames = self.eeFullCollectionInfo.propertyNames

        for row in range(10):
            w = QComboBox()
            w.addItems([''] + propertyNames)
            self.mFilterProperties.setCellWidget(row, 0, w)
            w = QComboBox()
            w.addItems(operators)
            self.mFilterProperties.setCellWidget(row, 1, w)
            w = QLineEdit()
            self.mFilterProperties.setCellWidget(row, 2, w)

        # self.mFilterProperties.resizeColumnsToContents()

        # set default date range filter dates
        d1, d2 = self.eeFullCollectionJson.temporalInterval()
        self.mFilterDateStart.setDate(d1)
        self.mFilterDateEnd.setDate(d2)

        # set default compositing dates to the last month of available data
        d1 = d2.addMonths(-1)
        d1 = d1.addDays(- d1.day() + 1)
        self.blockSignals(True)
        self.mCompositeDateStart.setDate(d1)
        self.mCompositeDateEnd.setDate(d2)
        self.blockSignals(False)

    def updateFilterBitmask(self):
        self.mFilterBitmask.clear()
        for eo_band in self.eeFullCollectionJson.data['summaries']['eo:bands']:

            # add bitmask bands
            if 'gee:bitmask' in eo_band:
                name = f"{eo_band['description']} [{eo_band['name']}]"
                bandItem = QTreeWidgetItem([name])
                bandItem.setExpanded(False)
                self.mFilterBitmask.addTopLevelItem(bandItem)
                for part in eo_band['gee:bitmask']['bitmask_parts']:
                    values = part['values']
                    partsItem = PixelQualityBitmaskItem(
                        part['description'], eo_band['name'], part['first_bit'], part['bit_count'], 1
                    )
                    bandItem.addChild(partsItem)
                    if len(values) == 0:

                        # set default QA flags
                        partsItem.setCheckState(0, Qt.Unchecked)
                        if eo_band['name'] in self.eeFullCollectionInfo.defaultQaFlags:
                            defaultQaFlags = self.eeFullCollectionInfo.defaultQaFlags[eo_band['name']]
                            if partsItem.text(0) in defaultQaFlags:
                                partsItem.setCheckState(0, Qt.Checked)
                                bandItem.setExpanded(True)

                    for value in values:
                        valueItem = PixelQualityBitmaskItem(
                            value['description'], eo_band['name'], part['first_bit'], part['bit_count'], value['value']
                        )

                        # set default QA flags
                        valueItem.setCheckState(0, Qt.Unchecked)
                        if eo_band['name'] in self.eeFullCollectionInfo.defaultQaFlags:
                            defaultQaFlags = self.eeFullCollectionInfo.defaultQaFlags[eo_band['name']]
                            if (partsItem.text(0), valueItem.text(0)) in defaultQaFlags:
                                valueItem.setCheckState(0, Qt.Checked)
                                bandItem.setExpanded(True)

                        partsItem.addChild(valueItem)
                    partsItem.setExpanded(True)

            # add classification bands
            if 'gee:classes' in eo_band:
                name = f"{eo_band['description']} [{eo_band['name']}]"
                bandItem = QTreeWidgetItem([name])
                bandItem.setExpanded(False)
                self.mFilterBitmask.addTopLevelItem(bandItem)
                for class_ in eo_band['gee:classes']:
                    classItem = CategoryMaskItem(class_['description'], eo_band['name'], class_['value'])

                    # set default QA flags
                    classItem.setCheckState(0, Qt.Unchecked)
                    if eo_band['name'] in self.eeFullCollectionInfo.defaultQaFlags:
                        defaultQaFlags = self.eeFullCollectionInfo.defaultQaFlags[eo_band['name']]
                        if classItem.text(0) in defaultQaFlags:
                            classItem.setCheckState(0, Qt.Checked)
                            bandItem.setExpanded(True)

                    pixmap = QPixmap(16, 16)
                    pixmap.fill(QColor('#' + class_['color']))
                    icon = QIcon(pixmap)
                    classItem.setIcon(0, icon)
                    classItem.setExpanded(True)
                    bandItem.addChild(classItem)

    def updateBandRendering(self):
        for mBand in [self.mRedBand, self.mBlueBand, self.mGreenBand, self.mPseudoColorBand]:
            mBand.clear()
        if self.eeFullCollection is None:
            return

        bandNames = self.eeFullCollectionInfo.bandNames
        bandToolTips = [self.eeFullCollectionJson.bandTooltip(bandNo) for bandNo in range(1, len(bandNames) + 1)]
        spectralIndices = self.selectedSpectralIndices()
        siNames = [si['short_name'] for si in spectralIndices]
        siToolTips = [si['long_name'] for si in spectralIndices]

        for mBand in [self.mRedBand, self.mBlueBand, self.mGreenBand, self.mPseudoColorBand]:
            mBand.addItems(bandNames + siNames)
            for i, toolTip in enumerate(bandToolTips + siToolTips):
                mBand.setItemData(i, toolTip, Qt.ToolTipRole)

        self.mVisualization.clear()

        visualizations = [''] + [v['display_name'] for v in self.eeFullCollectionJson.visualizations()]
        self.mVisualization.addItems(visualizations)

    def eeReducers(self) -> Dict:
        eeImported, ee = importEarthEngine(False)
        return OrderedDict(
            [('Mean', ee.Reducer.mean()), ('StdDev', ee.Reducer.stdDev()), ('Variance', ee.Reducer.variance()),
             ('Kurtosis', ee.Reducer.kurtosis()), ('Skewness', ee.Reducer.skew()), ('First', ee.Reducer.firstNonNull()),
             ('Last', ee.Reducer.lastNonNull()), ('Min', ee.Reducer.min()), ('P5', ee.Reducer.percentile([5])),
             ('P10', ee.Reducer.percentile([10])), ('P25', ee.Reducer.percentile([25])),
             ('Median', ee.Reducer.median()), ('P75', ee.Reducer.percentile([75])),
             ('P90', ee.Reducer.percentile([90])), ('P95', ee.Reducer.percentile([95])), ('Max', ee.Reducer.max()),
             ('Count', ee.Reducer.count())]
        )

    def updateReducer(self):
        eeReducers = self.eeReducers()
        reducerNames = list(self.eeReducers().keys())
        self.mReducerRed.addItems(reducerNames)
        self.mReducerGreen.addItems(reducerNames)
        self.mReducerBlue.addItems(reducerNames)
        self.mReducerPseudoColor.addItems(reducerNames)
        self.mReducerUniform.addItems(reducerNames)
        self.mReducerBandWise.setRowCount(len(self.eeFullCollectionInfo.bandNames))
        for i, bandName in enumerate(self.eeFullCollectionInfo.bandNames):
            self.mReducerBandWise.setCellWidget(i, 0, QLabel(bandName))
            w = QComboBox()
            w.addItems(list(eeReducers.keys()))
            self.mReducerBandWise.setCellWidget(i, 1, w)
        self.mReducerBandWise.resizeColumnsToContents()

    def copyAvailableImages(self):

        model = self.mAvailableImages.model()
        header = [self.mAvailableImages.horizontalHeaderItem(i).text() for i in
                  range(self.mAvailableImages.columnCount())]
        data = [header]
        for row in range(model.rowCount()):
            data.append([])
            for column in range(model.columnCount()):
                index = model.index(row, column)
                data[row].append(model.data(index))

        text = '\n'.join([';'.join(row) for row in data])
        QApplication.clipboard().setText(text)

    def copyImageInfo(self):

        with GeeWaitCursor():
            try:
                eeImage, eeImageRgb, visParams, visBands = self.eeImage()
                info = eeImage.getInfo()
            except Exception as error:
                print_exc()
                self.mMessageBar.pushCritical('Error', str(error))
                return

        text = json.dumps(info, indent=2)
        QApplication.clipboard().setText(text)

    def showImageInfo(self):
        self.copyImageInfo()
        text = QApplication.clipboard().text()
        mainWindow = QMainWindow(self)
        mainWindow.setWindowTitle('Image Info  — ' + self.mImageId.text())
        textEdit = QPlainTextEdit(text, self)
        textEdit.setReadOnly(True)
        mainWindow.setCentralWidget(textEdit)
        mainWindow.resize(600, 600)
        mainWindow.show()

    def queryAvailableImages(self):
        eeImported, ee = importEarthEngine(False)
        eeCollection = self.eeCollection()
        if eeCollection is None:
            self.pushInfoMissingCollection()
            return None

        point = self.currentLocation()
        point = point.toCrs(self.crsEpsg4326)
        eePoint = ee.Geometry.Point(point.x(), point.y())

        if self.mLimitImages.isChecked():
            limit = self.mLimitImagesValue.value()
        else:
            limit = int(1e6)

        task = QueryAvailableImagesTask(eeCollection, eePoint, limit, self.mMessageBar)
        task.taskCompleted.connect(lambda: self.onQueryAvailableImagesTaskCompleted(task))
        self.taskManager.addTask(task)

        self.refs.append(task)

    def onQueryAvailableImagesTaskCompleted(self, task: QueryAvailableImagesTask):
        if len(task.data) == 0:
            self.pushInfoQueryEmpty()

        if len(task.data) == task.limit:
            self.pushInfoQueryCut(task.limit)

        self.availableImagesData = task.header, task.data  # cache the data to avoid slow reading from table later

        # fill table
        self.mAvailableImages.setRowCount(len(task.data))
        self.mAvailableImages.setColumnCount(len(task.header))
        self.mAvailableImages.setHorizontalHeaderLabels(task.header)
        for row, values in enumerate(task.data):
            for column, value in enumerate(values):
                self.mAvailableImages.setItem(row, column, QTableWidgetItem(value))
        self.mAvailableImages.resizeColumnsToContents()

        # select first image
        self.mAvailableImages.clearSelection()
        self.mAvailableImages.selectRow(0)
        self.mIconList.setCurrentRow(5)

    def calculateCumulativeCountCutStretch(self):
        self.calculateCumulativeCountCutStretchForWms()

    def calculateCumulativeCountCutStretchForWms(self):
        eeImported, ee = importEarthEngine(False)
        if self.currentMapCanvas() is None:
            return

        extent = SpatialExtent(self.currentCrs(), self.currentMapCanvas().extent()).toCrs(self.crsEpsg4326)
        percentageMin = self.mPercentileMin.value()
        percentageMax = self.mPercentileMax.value()

        # calculate percentile stretch
        if self.mImageExplorerTab.currentIndex() == 0:  # Image Viewer
            result = self.eeImage()
            if result is None:
                return
            eeImageProfile, eeImageRgb, visParams, visBands = result
        elif self.mImageExplorerTab.currentIndex() == 1:  # Composite Viewer
            limit = 100  # better limit the collection before calc stats!
            eeCompositeProfile, eeCompositeRgb, visParams = self.eeComposite(limit)
            eeImageRgb = eeCompositeRgb
        else:
            assert 0

        eeExtent = ee.Geometry.Rectangle(
            [extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()], None, False
        )

        with GeeWaitCursor():
            try:
                percentiles = eeImageRgb.reduceRegion(
                    ee.Reducer.percentile([percentageMin, percentageMax]),
                    bestEffort=True, maxPixels=100000, geometry=eeExtent,
                    scale=self.currentMapCanvas().mapUnitsPerPixel()
                ).getInfo()
            except Exception as error:
                print_exc()
                self.mMessageBar.pushCritical('Error', str(error))
                return

        percentiles = {k: str(v) for k, v in percentiles.items()}

        # update min-max range
        ndigits = 3
        if self.mRendererType.currentIndex() == self.MultibandColorRenderer:
            self.mRedMin.setText(str(tofloat(percentiles[f'vis-red_p{percentageMin}'], 0, ndigits)))
            self.mRedMax.setText(str(tofloat(percentiles[f'vis-red_p{percentageMax}'], 0, ndigits)))
            self.mGreenMin.setText(str(tofloat(percentiles[f'vis-green_p{percentageMin}'], 0, ndigits)))
            self.mGreenMax.setText(str(tofloat(percentiles[f'vis-green_p{percentageMax}'], 0, ndigits)))
            self.mBlueMin.setText(str(tofloat(percentiles[f'vis-blue_p{percentageMin}'], 0, ndigits)))
            self.mBlueMax.setText(str(tofloat(percentiles[f'vis-blue_p{percentageMax}'], 0, ndigits)))
        elif self.mRendererType.currentIndex() == self.SinglebandPseudocolorRenderer:
            self.mPseudoColorMin.setText(str(tofloat(percentiles[f'vis-pseudo_p{percentageMin}'], 0, ndigits)))
            self.mPseudoColorMax.setText(str(tofloat(percentiles[f'vis-pseudo_p{percentageMax}'], 0, ndigits)))

    def eeVisualizationParameters(self) -> Dict:

        if self.mRendererType.currentIndex() == self.MultibandColorRenderer:
            visParams = {
                'bands': [self.mRedBand.currentText(), self.mGreenBand.currentText(), self.mBlueBand.currentText()],
                'min': [tofloat(mMin.text()) for mMin in [self.mRedMin, self.mGreenMin, self.mBlueMin]],
                'max': [tofloat(mMax.text()) for mMax in [self.mRedMax, self.mGreenMax, self.mBlueMax]],
            }
        elif self.mRendererType.currentIndex() == self.SinglebandPseudocolorRenderer:
            ramp: QgsColorRamp = self.mPseudoColorRamp.colorRamp()
            colors = [ramp.color(i / (ramp.count() - 1)) for i in range(ramp.count())]
            visParams = {
                'bands': [self.mPseudoColorBand.currentText()],
                'min': tofloat(self.mPseudoColorMin.text()),
                'max': tofloat(self.mPseudoColorMax.text()),
                'palette': [color.name().strip('#') for color in colors]
            }
        else:
            assert 0
        return visParams

    def eeCollection(
            self, addIndices=True, filterDate=True, filterProperty=True, filterQuality=True
    ):
        eeImported, ee = importEarthEngine(False)

        eeCollection = self.eeFullCollection

        if eeCollection is None:
            return None

        # add spectral index bands
        def addSpectralIndexBands(eeImage: ee.Image) -> ee.Image:
            for spectralIndex in self.selectedSpectralIndices():
                name = spectralIndex['short_name']  # NDVI
                formula = spectralIndex['formula']  # (N - R)/(N + R)
                mapping = {identifier: eeImage.select(bandName)
                           for identifier, bandName in self.eeFullCollectionInfo.wavebandMapping.items()}
                mapping.update({key: ee.Image(value)
                                for key, value in CreateSpectralIndicesAlgorithm.ConstantMapping.items()})
                eeImage = eeImage.addBands(eeImage.expression(formula, mapping).rename(name))
            return eeImage

        if addIndices:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                eeCollection = eeCollection.map(addSpectralIndexBands)

        # filter date range
        if filterDate:
            eeCollection = eeCollection.filterDate(
                self.mFilterDateStart.date().toString('yyyy-MM-dd'),
                self.mFilterDateEnd.date().addDays(1).toString('yyyy-MM-dd')  # GEE end date is exclusive
            )

        # filter metadata
        if filterProperty:
            for row in range(self.mFilterProperties.rowCount()):
                name: QComboBox = self.mFilterProperties.cellWidget(row, 0).currentText()
                operator: QComboBox = self.mFilterProperties.cellWidget(row, 1).currentText()
                value: QLineEdit = self.mFilterProperties.cellWidget(row, 2).text()
                if name == '' or operator == '' or value == '':
                    continue

                evalType = type(self.eeFullCollectionInfo.properties[name])
                eeCollection = eeCollection.filterMetadata(name, operator, evalType(value))

        # filter pixel quality
        if filterQuality:
            items = list()
            for i in range(self.mFilterBitmask.topLevelItemCount()):
                bandItem = self.mFilterBitmask.topLevelItem(i)
                for i2 in range(bandItem.childCount()):
                    classOrPartItem = bandItem.child(i2)
                    items.append(classOrPartItem)
                    for i3 in range(classOrPartItem.childCount()):
                        valueItem = classOrPartItem.child(i3)
                        items.append(valueItem)

            def maskPixel(eeImage: ee.Image) -> ee.Image:
                masks = list()
                for item in items:
                    if isinstance(item, (PixelQualityBitmaskItem, CategoryMaskItem)) and item.checkState(
                            0) == Qt.Checked:
                        masks.append(item.eeMask(eeImage))

                if len(masks) == 0:
                    return eeImage

                mask = ee.ImageCollection.fromImages(masks).reduce(ee.Reducer.bitwiseAnd())
                return eeImage.updateMask(mask)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                eeCollection = eeCollection.map(maskPixel)

        return eeCollection

    def compositeDates(self) -> Tuple[QDate, QDate]:
        dateStart = self.mCompositeDateStart.date()
        dateEnd = self.mCompositeDateEnd.date()
        if dateEnd >= dateStart:
            return dateStart, dateEnd
        else:
            return dateEnd, dateStart

    def eeComposite(self, limit: int = None):
        eeImported, ee = importEarthEngine(False)

        eeCollection = self.eeCollection()

        if eeCollection is None:
            return None

        # filter date range
        dateStart, dateEnd = self.compositeDates()
        eeCollection = eeCollection.filterDate(
            dateStart.toString('yyyy-MM-dd'),
            dateEnd.addDays(1).toString('yyyy-MM-dd')  # GEE end date is exclusive
        )

        # filter season
        eeCollection = eeCollection.filter(
            ee.Filter.calendarRange(
                self.mCompositeSeasonStart.date().dayOfYear(), self.mCompositeSeasonEnd.date().dayOfYear()
            )
        )

        # filter extent
        extentIndex = self.mCompositeExtent.currentIndex()
        if limit is not None:
            extentIndex = self.MapViewExtent  # when limiting the collection always use the map extent

        if extentIndex == self.MapViewExtent:
            extent = Utils.transformMapCanvasExtent(self.currentMapCanvas(), self.crsEpsg4326)
            eeExtent = ee.Geometry.Rectangle(
                [extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()], self.epsg4326, False
            )
            eeCollection = eeCollection.filterBounds(eeExtent)
            eeCollection = eeCollection.map(lambda eeImage: eeImage.clip(eeExtent))

        if extentIndex == self.LocationExtent:
            point = self.currentLocation()
            if point is None:
                point = SpatialPoint.fromMapCanvasCenter(self.currentMapCanvas())
            point = point.toCrs(self.crsEpsg4326)
            eePoint = ee.Geometry.Point(point.x(), point.y())
            eeCollection = eeCollection.filterBounds(eePoint)

        if extentIndex == self.GlobalExtent:
            pass

        # limit the collection
        if limit is not None:
            eeCollection = eeCollection.limit(limit)

        # scale data
        spectralIndexCount = len(self.selectedSpectralIndices())
        if self.mScaleBands.isChecked():
            offsets = [self.eeFullCollectionJson.bandOffset(bandNo)
                       for bandNo in range(1, self.eeFullCollectionInfo.bandCount + spectralIndexCount + 1)]
            scales = [self.eeFullCollectionJson.bandScale(bandNo)
                      for bandNo in range(1, self.eeFullCollectionInfo.bandCount + spectralIndexCount + 1)]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                if any([scale != 1. for scale in scales]):
                    eeCollection = eeCollection.map(lambda eeImage: eeImage.multiply(ee.Image(scales)))
                if any([offset != 0. for offset in offsets]):
                    eeCollection = eeCollection.map(lambda eeImage: eeImage.add(ee.Image(offsets)))

        # composite
        eeReducers = self.eeReducers()
        bandNames = self.eeFullCollectionInfo.bandNames + self.currentSpectralIndexBandNames()

        # - create composite used for z-profiles
        if self.mReducerType.currentIndex() == 0:  # uniform
            reducer = eeReducers[self.mReducerUniform.currentText()]
            eeCompositeProfile = eeCollection.reduce(reducer)
        elif self.mReducerType.currentIndex() == 1:  # band-wise
            eeBands = list()
            for i, bandName in enumerate(bandNames):
                w: QComboBox = self.mReducerBandWise.cellWidget(i, 1)
                reducer = eeReducers[w.currentText()]
                eeBand = eeCollection.select(bandName).reduce(reducer)
                eeBands.append(eeBand)
            eeCompositeProfile = ee.ImageCollection.fromImages(eeBands).toBands()
        else:
            assert 0

        eeCompositeProfile = eeCompositeProfile.rename(bandNames)

        # - create composite used for WMS layer
        if self.mRendererType.currentIndex() == self.MultibandColorRenderer:
            bandNamesRgb = [self.mRedBand.currentText(), self.mGreenBand.currentText(), self.mBlueBand.currentText()]
            eeCompositeRed = eeCollection \
                .select(bandNamesRgb[0]) \
                .reduce(eeReducers[self.mReducerRed.currentText()])
            eeCompositeGreen = eeCollection \
                .select(bandNamesRgb[1]) \
                .reduce(eeReducers[self.mReducerGreen.currentText()])
            eeCompositeBlue = eeCollection \
                .select(bandNamesRgb[2]) \
                .reduce(eeReducers[self.mReducerBlue.currentText()])
            eeCompositeRgb = ee.Image.rgb(eeCompositeRed, eeCompositeGreen, eeCompositeBlue)

            visParams = {
                'min': [tofloat(mMin.text()) for mMin in [self.mRedMin, self.mGreenMin, self.mBlueMin]],
                'max': [tofloat(mMax.text()) for mMax in [self.mRedMax, self.mGreenMax, self.mBlueMax]],
            }

        elif self.mRendererType.currentIndex() == self.SinglebandPseudocolorRenderer:
            bandNamePseudoColor = self.mPseudoColorBand.currentText()
            eeCompositeRgb = eeCollection \
                .select(bandNamePseudoColor) \
                .reduce(eeReducers[self.mReducerPseudoColor.currentText()]) \
                .rename('vis-pseudo')

            ramp = self.mPseudoColorRamp.colorRamp()
            colors = [ramp.color(i / (ramp.count() - 1)) for i in range(ramp.count())]
            visParams = {
                'min': tofloat(self.mPseudoColorMin.text()),
                'max': tofloat(self.mPseudoColorMax.text()),
                'palette': [color.name().strip('#') for color in colors]
            }
        else:
            assert 0

        return eeCompositeProfile, eeCompositeRgb, visParams

    def currentCompositeLayerName(self):
        seperator = ' – '
        items = list()
        if self.mAppendName.isChecked():
            items.append(self.mLayerName.text())

        if self.mAppendId.isChecked():
            items.append(self.eeFullCollectionJson.id().replace('/', '_'))

        if self.mAppendDate.isChecked():
            dateStart, dateEnd = self.compositeDates()
            if dateStart.daysTo(dateEnd) == 1:
                item = dateStart.CompositeDateStart.text()
            else:
                item = dateStart.toString('yyyy-MM-dd') + ' to ' + dateEnd.toString('yyyy-MM-dd')
            items.append(item)

            # append season if not the whole year
            seasonStart = self.mCompositeSeasonStart.date().toString('MM-dd')
            seasonEnd = self.mCompositeSeasonEnd.date().toString('MM-dd')
            if seasonStart != '01-01' or seasonEnd != '12-31':
                items.append(seasonStart + ' to ' + seasonEnd)

        if self.mAppendBandNames.isChecked():
            if self.mRendererType.currentIndex() == self.MultibandColorRenderer:
                items.append(self.mRedBand.currentText())
                items.append(self.mGreenBand.currentText())
                items.append(self.mBlueBand.currentText())
            elif self.mRendererType.currentIndex() == self.SinglebandPseudocolorRenderer:
                items.append(self.mPseudoColorBand.currentText())

        name = seperator.join(items)
        return name

    def eeImage(self, imageId: str = None):
        eeImported, ee = importEarthEngine(False)

        eeCollection = self.eeCollection(filterDate=False, filterProperty=False)

        if eeCollection is None:
            return None

        # select image by ID
        if imageId is None:
            imageId = self.mImageId.text()
            if imageId == '':
                self.pushInfoMissingImage()
                return

        eeImage = eeCollection.filter(ee.Filter.eq('system:index', imageId)).first()

        # scale data
        if self.mScaleBands.isChecked():
            spectralIndexCount = len(self.selectedSpectralIndices())
            offsets = [self.eeFullCollectionJson.bandOffset(bandNo)
                       for bandNo in range(1, self.eeFullCollectionInfo.bandCount + spectralIndexCount + 1)]
            scales = [self.eeFullCollectionJson.bandScale(bandNo)
                      for bandNo in range(1, self.eeFullCollectionInfo.bandCount + spectralIndexCount + 1)]

            if any([scale != 1. for scale in scales]):
                eeImage = eeImage.multiply(ee.Image(scales))
            if any([offset != 0. for offset in offsets]):
                eeImage = eeImage.add(ee.Image(offsets))

        if self.mRendererType.currentIndex() == self.MultibandColorRenderer:
            visBands = [self.mRedBand.currentText(), self.mGreenBand.currentText(), self.mBlueBand.currentText()]
            eeImageRed = eeImage.select(visBands[0])
            eeImageGreen = eeImage.select(visBands[1])
            eeImageBlue = eeImage.select(visBands[2])
            eeImageRgb = ee.Image.rgb(eeImageRed, eeImageGreen, eeImageBlue)
            visParams = {
                'min': [tofloat(mMin.text()) for mMin in [self.mRedMin, self.mGreenMin, self.mBlueMin]],
                'max': [tofloat(mMax.text()) for mMax in [self.mRedMax, self.mGreenMax, self.mBlueMax]],
            }
        elif self.mRendererType.currentIndex() == self.SinglebandPseudocolorRenderer:
            visBands = [self.mPseudoColorBand.currentText()]
            eeImageRgb = eeImage.select(visBands[0]).rename('vis-pseudo')
            ramp = self.mPseudoColorRamp.colorRamp()
            colors = [ramp.color(i / (ramp.count() - 1)) for i in range(ramp.count())]
            visParams = {
                'min': tofloat(self.mPseudoColorMin.text()),
                'max': tofloat(self.mPseudoColorMax.text()),
                'palette': [color.name().strip('#') for color in colors]
            }
        else:
            assert 0

        return eeImage, eeImageRgb, visParams, visBands

    def currentImageAcquisitionDate(self) -> QDateTime:
        eeImported, ee = importEarthEngine(False)

        key = 'currentImageAcquisitionDate', self.mImageId.text()
        if key not in self.cache:  # cache date for later
            eeImage = self.eeCollection(False, False, False, False) \
                .filter(ee.Filter.eq('system:index', self.mImageId.text())).first()
            msec = eeImage.get('system:time_start').getInfo()
            self.cache[key] = msec
        msec = self.cache[key]
        return utilsMsecToDateTime(msec)

    def currentImageLayerName(self):

        if self.mImageId.text() == '':
            return ''

        seperator = ' – '
        items = list()
        if self.mAppendName.isChecked():
            items.append(self.mLayerName.text())

        if self.mAppendId.isChecked():
            items.append(self.mImageId.text())

        if self.mAppendDate.isChecked():
            dateTime = self.currentImageAcquisitionDate()
            items.append(dateTime.toString('yyyy-MM-dd'))

        if self.mAppendBandNames.isChecked():
            if self.mRendererType.currentIndex() == self.MultibandColorRenderer:
                items.append(self.mRedBand.currentText())
                items.append(self.mGreenBand.currentText())
                items.append(self.mBlueBand.currentText())
            elif self.mRendererType.currentIndex() == self.SinglebandPseudocolorRenderer:
                items.append(self.mPseudoColorBand.currentText())

        name = seperator.join(items)
        return name

    def currentLayerName(self) -> str:
        if self.mImageExplorerTab.currentIndex() == 0:  # image viewer
            return self.currentImageLayerName()
        elif self.mImageExplorerTab.currentIndex() == 1:  # compositing
            return self.currentCompositeLayerName()
        else:
            assert 0

    def updateLayerNamePreview(self):
        self.mLayerNamePreview.setText(self.currentLayerName())

    def currentImageId(self) -> Optional[str]:
        imageId = self.mImageId.text()
        if imageId == '':
            return None
        return imageId

    def currentSpectralIndexBandNames(self) -> List[str]:
        return [si['short_name'] for si in self.selectedSpectralIndices()]

    def currentVisualizationBandNames(self) -> List[str]:
        if self.mRendererType.currentIndex() == self.MultibandColorRenderer:
            return [self.mRedBand.currentText(), self.mGreenBand.currentText(), self.mBlueBand.currentText()]
        elif self.mRendererType.currentIndex() == self.SinglebandPseudocolorRenderer:
            return [self.mPseudoColorBand.currentText()]
        assert 0

    def currentImageChipBandNames(self) -> Optional[List[str]]:
        allBandNames = self.eeFullCollectionInfo.bandNames + self.currentSpectralIndexBandNames()
        selectedBandNames = set()

        VisualizationBands, ReflectanceBands, PixelQualityBands, SpectralIndexBands, ProfileBands, \
        AllBands = range(6)
        if self.profileDock.mImageChipBands.itemCheckState(VisualizationBands) == Qt.Checked:
            selectedBandNames.update(self.currentVisualizationBandNames())
        if self.profileDock.mImageChipBands.itemCheckState(ReflectanceBands) == Qt.Checked:
            reflectanceBandNames = [bandName for bandNo, bandName in enumerate(self.eeFullCollectionInfo.bandNames, 1)
                                    if isfinite(self.eeFullCollectionJson.bandWavelength(bandNo))]
            selectedBandNames.update(reflectanceBandNames)
        if self.profileDock.mImageChipBands.itemCheckState(PixelQualityBands) == Qt.Checked:
            bitmaskBandNames = [bandName for bandNo, bandName in enumerate(self.eeFullCollectionInfo.bandNames, 1)
                                if self.eeFullCollectionJson.isBitmaskBand(bandNo)]
            classificationBandNames = [bandName for bandNo, bandName in
                                       enumerate(self.eeFullCollectionInfo.bandNames, 1)
                                       if self.eeFullCollectionJson.isClassificationBand(bandNo)]
            selectedBandNames.update(bitmaskBandNames)
            selectedBandNames.update(classificationBandNames)
        if self.profileDock.mImageChipBands.itemCheckState(SpectralIndexBands) == Qt.Checked:
            selectedBandNames.update(self.currentSpectralIndexBandNames())
        if self.profileDock.mImageChipBands.itemCheckState(ProfileBands) == Qt.Checked:
            profileBandNames = self.profileDock.selectedBandNames()
            if profileBandNames is not None:
                selectedBandNames.update(profileBandNames)
        if self.profileDock.mImageChipBands.itemCheckState(AllBands) == Qt.Checked:
            selectedBandNames.update(allBandNames)

        bandNames = [bandName for bandName in allBandNames if bandName in selectedBandNames]  # this assures band order

        if len(bandNames) == 0:
            return None
        return bandNames

    def currentLocation(self) -> SpatialPoint:
        return self.profileDock.currentLocation()

    def currentMapCanvas(self) -> Optional[QgsMapCanvas]:
        if self.interfaceType == self.InterfaceType.EnmapBox:
            return self.enmapBoxInterface().currentMapCanvas()
        elif self.interfaceType == self.InterfaceType.Qgis:
            return self.qgisInterface().mapCanvas()
        else:
            raise ValueError()

    def currentExtent(self) -> SpatialExtent:
        return SpatialExtent(self.currentCrs(), self.currentMapCanvas().extent())

    def currentCrs(self) -> QgsCoordinateReferenceSystem:
        mapSettings: QgsMapSettings = self.currentMapCanvas().mapSettings()
        return mapSettings.destinationCrs()

    def currentLayer(self) -> Optional[QgsMapLayer]:
        if self.interfaceType == self.InterfaceType.EnmapBox:
            return self.enmapBoxInterface().currentLayer()
        elif self.interfaceType == self.InterfaceType.Qgis:
            return self.qgisInterface().activeLayer()
        else:
            raise ValueError()

    def setCurrentLayer(self, layer: QgsMapLayer):
        if self.interfaceType == self.InterfaceType.EnmapBox:
            self.enmapBoxInterface().setCurrentLayer(layer)
        elif self.interfaceType == self.InterfaceType.Qgis:
            self.qgisInterface().setActiveLayer(layer)
        else:
            raise ValueError()

    def currentDownloadFolder(self) -> str:
        return self.profileDock.currentDownloadFolder()

    def downloadFilenameImageChipBandTif(self, location: SpatialPoint, imageId: str, bandName: str):
        # eeCollection = self.eeCollection(filterDate=False, filterProperty=False, filterQuality=True)
        collectionId = self.eeFullCollectionJson.id().replace('/', '_')
        filename = join(
            self.profileDock.mDownloadFolder.filePath(),
            'chips',
            collectionId,
            # str(hash(eeCollection.serialize())),
            'X%018.13f_Y%018.13f' % (location.x(), location.y()),
            imageId,
            imageId + '_' + bandName + '.tif'
        )
        if not exists(dirname(filename)):
            makedirs(dirname(filename))
        return filename

    def downloadFilenameImageChipVrt(self, location: SpatialPoint, imageId: str, bandNames: List[str]):
        collectionId = self.eeFullCollectionJson.id().replace('/', '_')
        filename = join(
            'c:/vsimem/GEETSE', collectionId, 'X%018.13f_Y%018.13f' % (location.x(), location.y()),
            imageId, imageId + '_' + "-".join(bandNames) + '.vrt'
        )
        if not filename.startswith('/vsimem/') and not exists(dirname(filename)):
            makedirs(dirname(filename))

        return filename

    def createWmsLayer(self, eeImage, eeImageRgb, visParams: Dict, layerName: str):

        if self.currentMapCanvas() is None:
            return

        # update/create WMS layer
        with GeeWaitCursor():
            try:
                from geetimeseriesexplorerapp.externals.ee_plugin import Map
                layer = Map.addLayer(eeImageRgb, visParams, layerName, self.currentMapCanvas())
            except Exception as error:
                print_exc()
                self.mMessageBar.pushCritical('Error', str(error))
                return

        # set collection information
        provider: GeetseEarthEngineRasterDataProvider = layer.dataProvider()
        provider.setInformation(self.eeFullCollectionJson, self.eeFullCollectionInfo)
        showBandInProfile = [self.mBandProperty.cellWidget(row, 4).isChecked()
                             for row in range(self.mBandProperty.rowCount())]
        provider.setImageForProfile(eeImage, showBandInProfile)
        # layer.dataSourceChanged.emit()  # wait for issue #1270

    def pushInfoMissingCollection(self):
        self.mMessageBar.pushInfo('Missing parameter', 'select a collection')

    def pushInfoMissingImage(self):
        self.mMessageBar.pushInfo('Missing parameter', 'select an image')

    def pushInfoQueryCut(self, max_: int):
        self.mMessageBar.pushInfo('Query', f'collection query result cut after accumulating over {max_} elements')

    def pushInfoQueryEmpty(self):
        self.mMessageBar.pushInfo('Query', 'collection query result is empty')

    LocationExtent = 0
    MapViewExtent = 1
    GlobalExtent = 2

    MultibandColorRenderer = 0
    SinglebandPseudocolorRenderer = 1


def tofloat(obj, default=0, ndigits=None):
    try:
        value = float(obj)
    except Exception:
        value = default
    if ndigits is not None:
        value = round(value, ndigits)
    return value


@typechecked
class CategoryMaskItem(QTreeWidgetItem):

    def __init__(self, text: str, bandName: str, value: int):
        QTreeWidgetItem.__init__(self, [text])
        self.bandName = bandName
        self.value = value

    def eeMask(self, eeImage):
        return eeImage.select(self.bandName).neq(self.value)


@typechecked
class PixelQualityBitmaskItem(QTreeWidgetItem):

    def __init__(self, text: str, bandName: str, firstBit: int, bitCount: int, value: int):
        QTreeWidgetItem.__init__(self, [text])
        self.bandName = bandName
        self.firstBit = firstBit
        self.bitCount = bitCount
        self.value = value

    def eeMask(self, eeImage):
        return eeImage.select(self.bandName).rightShift(self.firstBit).bitwiseAnd(2 ** self.bitCount - 1).neq(
            self.value)


class GeeWaitCursor(object):

    def __enter__(self):
        QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))

    def __exit__(self, exc_type, exc_value, tb):
        QApplication.restoreOverrideCursor()
