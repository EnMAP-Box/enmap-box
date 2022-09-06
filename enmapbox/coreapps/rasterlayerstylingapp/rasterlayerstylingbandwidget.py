from qgis.PyQt.QtWidgets import QWidget, QLabel, QLineEdit, QSlider, QSpinBox
from qgis.gui import QgsRasterBandComboBox

from qgis.PyQt import uic
from typeguard import typechecked


@typechecked
class RasterLayerStylingBandWidget(QWidget):
    mName: QLabel
    mBandNo: QgsRasterBandComboBox
    mMin: QLineEdit
    mMax: QLineEdit
    mSlider: QSlider
    mWavelength: QSpinBox

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)
