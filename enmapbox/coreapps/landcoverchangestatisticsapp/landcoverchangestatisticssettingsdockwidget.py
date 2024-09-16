from enmapbox.gui.widgets.multiplemaplayerselectionwidget.multiplemaplayerselectionwidget import \
    MultipleMapLayerSelectionWidget
from enmapbox.typeguard import typechecked
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QCheckBox, QComboBox
from qgis.PyQt.QtWidgets import QToolButton
from qgis.PyQt.uic import loadUi
from qgis.gui import QgsDockWidget, QgsSpinBox, QgsColorButton


@typechecked
class LandCoverChangeStatisticsSettingsDockWidget(QgsDockWidget):
    mLayers: MultipleMapLayerSelectionWidget
    mExtent: QComboBox
    mAccuracy: QComboBox
    mShowNodePadding: QCheckBox
    mShowClassNames: QCheckBox
    mShowLayerNames: QCheckBox
    mShowClassSizes: QCheckBox
    mClassSizeUnits: QComboBox
    mHideDiscardedClasses: QCheckBox
    mRescaleOtherClasses: QCheckBox
    mLinkOpacity: QgsSpinBox

    mHighlightCurrentLocation: QCheckBox
    mHighlightColor: QgsColorButton

    mLiveUpdate: QCheckBox
    mApply: QToolButton

    sigStateChanged = pyqtSignal()
    sigLayersChanged = pyqtSignal()

    def __init__(self, *args, **kwds):
        QgsDockWidget.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        self.mLayers.setAllowRaster(True)
        self.mLayers.setAllowVector(False)
        self.mLayers.setInfoType(MultipleMapLayerSelectionWidget.LongInfo)

        self.mLayers.sigLayersChanged.connect(self.onLayersChanged)

        self.mHideDiscardedClasses.stateChanged.connect(self.onStateChanged)
        self.mRescaleOtherClasses.stateChanged.connect(self.onStateChanged)
        self.mLinkOpacity.valueChanged.connect(self.onStateChanged)
        self.mShowNodePadding.stateChanged.connect(self.onStateChanged)
        self.mShowClassNames.stateChanged.connect(self.onStateChanged)
        self.mShowLayerNames.stateChanged.connect(self.onStateChanged)
        self.mShowClassSizes.stateChanged.connect(self.onStateChanged)
        self.mClassSizeUnits.currentIndexChanged.connect(self.onStateChanged)
        self.mHighlightCurrentLocation.stateChanged.connect(self.onStateChanged)
        self.mHighlightColor.colorChanged.connect(self.onStateChanged)

        # hide stuff that is not yet implemented
        self.mHighlightCurrentLocation.hide()
        self.mHighlightColor.hide()

    def onStateChanged(self):
        self.sigStateChanged.emit()

    def onLayersChanged(self):
        self.sigLayersChanged.emit()
