from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QCheckBox
from qgis.PyQt.QtWidgets import QWidget, QLabel, QLineEdit, QSlider, QSpinBox
from qgis.gui import QgsRasterBandComboBox
from enmapboxexternal.typeguard import typechecked


@typechecked
class RasterLayerStylingBandWidget(QWidget):
    mName: QLabel
    mBandNo: QgsRasterBandComboBox
    mIsBadBand: QCheckBox
    mMin: QLineEdit
    mMax: QLineEdit
    mSlider: QSlider
    mWavelength: QSpinBox

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)
