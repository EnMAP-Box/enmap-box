from qgis.PyQt.QtWidgets import QDoubleSpinBox, QWidget

from qgis.PyQt import uic
from typeguard import typechecked


@typechecked
class RasterLayerStylingPercentilesWidget(QWidget):
    mP1: QDoubleSpinBox
    mP2: QDoubleSpinBox

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)
