from qgis.PyQt.QtWidgets import QLineEdit, QToolButton, QCheckBox, QSpinBox
from qgis.PyQt.uic import loadUi
from qgis.gui import QgsColorRampButton, QgsDockWidget


class SpectralSurfacePlottingSettingsDockWidget(QgsDockWidget):
    mShowSurface: QCheckBox
    mShowPoints: QCheckBox
    mShowEdges: QCheckBox
    mShowGrid: QCheckBox
    mShowAxes: QCheckBox
    mShowAxisX: QCheckBox
    mShowAxisY: QCheckBox
    mShowAxisZ: QCheckBox
    mShowAxisLabelX: QCheckBox
    mShowAxisLabelY: QCheckBox
    mShowAxisLabelZ: QCheckBox
    mAxisLabelX: QLineEdit
    mAxisLabelY: QLineEdit
    mAxisLabelZ: QLineEdit
    mColorRamp: QgsColorRampButton
    scaleBase = 2
    mScaleX: QSpinBox
    mScaleY: QSpinBox
    mScaleZ: QSpinBox
    mAutoScale: QToolButton
    mNTicks: QSpinBox
    mResetCamera: QToolButton

    def __init__(self, *args, **kwds):
        QgsDockWidget.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)
