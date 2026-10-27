from qgis.PyQt.QtWidgets import QComboBox, QToolButton, QCheckBox
from qgis.PyQt.uic import loadUi
from qgis.gui import QgsMapLayerComboBox, QgsFilterLineEdit, QgsFieldComboBox, QgsDockWidget


class SpectralSurfacePlottingDataDockWidget(QgsDockWidget):
    mDataFormat: QComboBox
    mTable: QgsMapLayerComboBox
    mLibrary: QgsMapLayerComboBox
    mLibrarySelectedOnly: QCheckBox
    mCollection: QgsMapLayerComboBox
    mXMin: QgsFilterLineEdit
    mXMax: QgsFilterLineEdit
    mYMin: QgsFilterLineEdit
    mYMax: QgsFilterLineEdit
    mZMin: QgsFilterLineEdit
    mZMax: QgsFilterLineEdit
    mXScale: QgsFilterLineEdit
    mYScale: QgsFilterLineEdit
    mZScale: QgsFilterLineEdit
    mFieldLfX: QgsFieldComboBox
    mFieldLfY: QgsFieldComboBox
    mFieldLfZ: QgsFieldComboBox
    mFieldLibraryProfiles: QgsFieldComboBox
    mFieldLibraryY: QgsFieldComboBox
    mFieldLibraryYSorted: QCheckBox
    mFieldLibraryC: QgsFieldComboBox
    mFieldCollectionY: QgsFieldComboBox
    mFieldCollectionC: QgsFieldComboBox
    mLoadData: QToolButton
    LongFormat, LibraryFormat, CollectionFormat = 0, 1, 2

    def __init__(self, *args, **kwds):
        QgsDockWidget.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)
