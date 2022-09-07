from math import nan
from os.path import normcase
from typing import Dict, Optional

from osgeo import gdal

from enmapbox.qgispluginsupport.qps.speclib.io.envi import readENVIHeader
from enmapboxprocessing.algorithm.editrastersourcebandpropertiesalgorithm import EditRasterSourceBandPropertiesAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtWidgets import QToolButton, QMainWindow, QTableWidget, QComboBox, QCheckBox, \
    QLineEdit, QAbstractSpinBox, QMessageBox
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRasterLayer, QgsProject
from qgis.gui import QgsFilterLineEdit, QgsDateTimeEdit, QgsCollapsibleGroupBox
from typeguard import typechecked


@typechecked
class RasterSourceBandPropertiesEditorDialog(QMainWindow):
    mSource: QComboBox
    mTable: QTableWidget
    mColumn: QComboBox
    mSetValues: QToolButton
    mRevertValues: QToolButton
    mCode: QLineEdit
    mPreview: QLineEdit
    mSaveToSource: QToolButton

    mEnviGroupBox: QgsCollapsibleGroupBox
    mAcquisitionTime: QLineEdit
    mReflactanceScaleFactor: QLineEdit
    mWavelength: QLineEdit
    mFwhm: QLineEdit
    mBbl: QLineEdit
    mSetAcquisitionTime: QToolButton
    mSetReflactanceScaleFactor: QToolButton
    mSetWavelength: QToolButton
    mSetFwhm: QToolButton
    mSetBbl: QToolButton

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox import EnMAPBox
        self.enmapBox = EnMAPBox.instance()
        self.defaultValues: Dict = dict()
        self.mSource.addItems([''] + self.enmapBox.dataSources('RASTER', True))
        self.mSource.setCurrentIndex(0)
        self.mEnviGroupBox.hide()

        # connect signals
        self.mSource.currentTextChanged.connect(self.onSourceChanged)
        self.mCode.textChanged.connect(self.onCodeChanged)
        self.mSetValues.clicked.connect(self.onSetValuesClicked)
        self.mRevertValues.clicked.connect(self.onRevertValuesClicked)
        self.mSaveToSource.clicked.connect(self.onSaveToSourceClicked)
        self.mSetAcquisitionTime.clicked.connect(self.onSetAcquisitionTimeClicked)
        self.mSetReflactanceScaleFactor.clicked.connect(self.onSetReflactanceScaleFactorClicked)
        self.mSetWavelength.clicked.connect(self.onSetWavelengthClicked)
        self.mSetFwhm.clicked.connect(self.onSetFwhmClicked)
        self.mSetBbl.clicked.connect(self.onSetBblClicked)

    def currentSource(self) -> Optional[str]:
        source = self.mSource.currentText()
        if source == '':
            return None
        return source

    def onSourceChanged(self):
        self.mTable.setRowCount(0)

        source = self.mSource.currentText()
        if source == '':
            return

        ds = gdal.Open(source)
        if ds is None:
            QMessageBox.information(self, 'Invalid source', 'Selected source is not a valid GDAL dataset.')
            self.mSource.setCurrentIndex(0)
            return

        layer = QgsRasterLayer(source)
        for layer in QgsProject.instance().mapLayers().values():
            if normcase(layer.source()) == normcase(source):
                QMessageBox.information(
                    self, 'Source owned by QGIS',
                    "Selected source is currently opened in QGIS project and can't be modified.")
                self.mSource.setCurrentIndex(0)
                return

        reader = RasterReader(layer)

        # init gui
        self.mTable.setRowCount(reader.bandCount())
        self.defaultValues = dict()
        for bandNo in reader.bandNumbers():
            row = bandNo - 1

            bandName = reader.bandName(bandNo)
            if bandName is None:
                bandName = reader.bandName(bandNo)
            w = QgsFilterLineEdit()
            w.setNullValue(bandName)
            w.setText(bandName)
            w.setFrame(False)
            self.mTable.setCellWidget(row, 0, w)
            self.defaultValues[(row, 0)] = bandName

            wavelength = reader.wavelength(bandNo)
            if wavelength is None:
                wavelength = ''
            else:
                wavelength = str(round(wavelength, 3))
            w = QgsFilterLineEdit()
            w.setNullValue(wavelength)
            w.setText(wavelength)
            w.setFrame(False)
            self.mTable.setCellWidget(row, 1, w)
            self.defaultValues[(row, 1)] = wavelength

            fwhm = reader.fwhm(bandNo)
            if fwhm is None:
                fwhm = ''
            else:
                fwhm = str(round(fwhm, 3))
            w = QgsFilterLineEdit()
            w.setNullValue(fwhm)
            w.setText(fwhm)
            w.setFrame(False)
            self.mTable.setCellWidget(row, 2, w)
            self.defaultValues[(row, 2)] = fwhm

            isBadBand = reader.badBandMultiplier(bandNo) == 0
            w = QCheckBox()
            w.setChecked(isBadBand)
            self.mTable.setCellWidget(row, 3, w)
            self.defaultValues[(row, 3)] = isBadBand

            self.dateTimeFormat = 'yyyy-MM-ddTHH:mm:ss'
            startTime = reader.startTime(bandNo)
            w = QgsDateTimeEdit()
            w.setDisplayFormat(self.dateTimeFormat)
            w.setFrame(False)
            w.setNullRepresentation('')
            w.setCalendarPopup(False)
            w.setButtonSymbols(QAbstractSpinBox.NoButtons)
            if startTime is None:
                w.clear()
            else:
                w.setDateTime(startTime)
            self.mTable.setCellWidget(row, 4, w)
            self.defaultValues[(row, 4)] = startTime

            endTime = reader.endTime(bandNo)
            w = QgsDateTimeEdit()
            w.setDisplayFormat(self.dateTimeFormat)
            w.setFrame(False)
            w.setNullRepresentation('')
            w.setCalendarPopup(False)
            w.setButtonSymbols(QAbstractSpinBox.NoButtons)
            if endTime is None:
                w.clear()
            else:
                w.setDateTime(endTime)
            self.mTable.setCellWidget(row, 5, w)
            self.defaultValues[(row, 5)] = endTime

            offset = reader.bandOffset(bandNo)
            if offset is None:
                offset = ''
            else:
                offset = str(offset)
            w = QgsFilterLineEdit()
            w.setNullValue(offset)
            w.setText(offset)
            w.setFrame(False)
            self.mTable.setCellWidget(row, 6, w)
            self.defaultValues[(row, 6)] = offset

            scale = reader.bandScale(bandNo)
            if scale is None:
                scale = ''
            else:
                scale = str(scale)
            w = QgsFilterLineEdit()
            w.setNullValue(scale)
            w.setText(scale)
            w.setFrame(False)
            self.mTable.setCellWidget(row, 7, w)
            self.defaultValues[(row, 7)] = scale

            noDataValue = reader.noDataValue(bandNo)
            if noDataValue is None:
                noDataValue = ''
            else:
                noDataValue = str(noDataValue)
            w = QgsFilterLineEdit()
            w.setNullValue(noDataValue)
            w.setText(noDataValue)
            w.setFrame(False)
            self.mTable.setCellWidget(row, 8, w)
            self.defaultValues[(row, 8)] = noDataValue

        self.mTable.resizeColumnToContents(0)

        # special ENVI file handling
        gdalDriver: gdal.Driver = reader.gdalDataset.GetDriver()
        if gdalDriver.ShortName == 'ENVI':
            metadata = {k.lower(): v for k, v in readENVIHeader(source).items()}

            key = 'acquisition time'
            if key in metadata:
                self.mAcquisitionTime.setText(metadata[key])
                self.mSetAcquisitionTime.setEnabled(True)
            else:
                self.mAcquisitionTime.setText('')
                self.mSetAcquisitionTime.setEnabled(False)

            key = 'reflectance scale factor'
            if key in metadata:
                self.mReflactanceScaleFactor.setText(str(metadata[key]))
                self.mSetReflactanceScaleFactor.setEnabled(True)
            else:
                self.mReflactanceScaleFactor.setText('')
                self.mSetReflactanceScaleFactor.setEnabled(False)

            key = 'wavelength'
            if key in metadata:
                units = metadata['wavelength units']
                factor = Utils.wavelengthUnitsConversionFactor(units, 'nm')
                values = [round(float(value) * factor, 3) for value in metadata[key]]
                self.mWavelength.setText(str(values))
                self.mSetWavelength.setEnabled(True)
            else:
                self.mWavelength.setText('')
                self.mSetWavelength.setEnabled(False)

            key = 'fwhm'
            if key in metadata:
                units = metadata['wavelength units']
                factor = Utils.wavelengthUnitsConversionFactor(units, 'nm')
                values = [round(float(value) * factor, 3) for value in metadata[key]]
                self.mFwhm.setText(str(values))
                self.mSetFwhm.setEnabled(True)
            else:
                self.mFwhm.setText('')
                self.mSetFwhm.setEnabled(False)

            key = 'bbl'
            if key in metadata:
                self.mBbl.setText(str(metadata[key]))
                self.mSetBbl.setEnabled(True)
            else:
                self.mBbl.setText('')
                self.mSetBbl.setEnabled(False)

            self.mEnviGroupBox.show()
        else:
            self.mEnviGroupBox.hide()

    def onCodeChanged(self):
        source = self.currentSource()
        if source is None:
            return

        code = self.mCode.text()
        reader = RasterReader(source)
        try:
            values = list()
            for bandNo in reader.bandNumbers():
                value = eval(code, {'bandNo': bandNo, 'layer': reader.layer, 'reader': reader})
                values.append(value)
        except Exception as error:
            self.mPreview.setText(str(error))
            self.mSetValues.setEnabled(False)
            self.mEvalValues = None
            return

        self.mSetValues.setEnabled(True)
        self.mPreview.setText(str(values))
        self.mEvalValues = values

    def onSetValuesClicked(self):
        source = self.currentSource()
        if source is None:
            return

        reader = RasterReader(source)
        column = self.mColumn.currentIndex()
        for bandNo, value in zip(reader.bandNumbers(), self.mEvalValues):
            row = bandNo - 1

            widget = self.mTable.cellWidget(row, column)
            if isinstance(widget, QgsFilterLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QgsDateTimeEdit):
                widget.setDateTime(Utils.parseDateTime(value))
            else:
                raise NotImplementedError(f'unexpected attribute type: {type(widget)}')

    def onRevertValuesClicked(self):
        for column in range(self.mTable.columnCount()):
            for row in range(self.mTable.rowCount()):
                widget = self.mTable.cellWidget(row, column)
                value = self.defaultValues[(row, column)]
                if isinstance(widget, QgsFilterLineEdit):
                    widget.setText(value)
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(value)
                elif isinstance(widget, QgsDateTimeEdit):
                    if value is None:
                        widget.clear()
                        widget.displayNull()
                    else:
                        widget.setDateTime(value)
                else:
                    raise NotImplementedError(f'unexpected attribute type: {type(widget)}')

    def onSaveToSourceClicked(self):
        source = self.currentSource()
        print(source)
        if source is None:
            return

        names = list()
        wavelengths = list()
        fwhms = list()
        badBandMultipliers = list()
        startTimes = list()
        endTimes = list()
        offsets = list()
        scales = list()
        noDataValues = list()

        def tofloat(text: str, default: Optional[float]):
            try:
                return float(text)
            except Exception:
                return default

        reader = RasterReader(source)
        for bandNo in reader.bandNumbers():
            row = bandNo - 1

            w: QgsFilterLineEdit = self.mTable.cellWidget(row, 0)
            names.append(w.text())

            w: QgsFilterLineEdit = self.mTable.cellWidget(row, 1)
            wavelengths.append(tofloat(w.text(), nan))

            w: QgsFilterLineEdit = self.mTable.cellWidget(row, 2)
            fwhms.append(tofloat(w.text(), nan))

            w: QCheckBox = self.mTable.cellWidget(row, 3)
            if w.checkState():
                badBandMultipliers.append(0)
            else:
                badBandMultipliers.append(1)

            w: QgsDateTimeEdit = self.mTable.cellWidget(row, 4)
            if w.isNull():
                startTimes.append('')
            else:
                startTimes.append(w.dateTime().toString('yyyy-MM-ddTHH:mm:ss'))

            w: QgsDateTimeEdit = self.mTable.cellWidget(row, 5)
            if w.isNull():
                endTimes.append('')
            else:
                endTimes.append(w.dateTime().toString('yyyy-MM-ddTHH:mm:ss'))

            w: QgsFilterLineEdit() = self.mTable.cellWidget(row, 6)
            offsets.append(tofloat(w.text(), 0))

            w: QgsFilterLineEdit() = self.mTable.cellWidget(row, 7)
            scales.append(tofloat(w.text(), 1))

            w: QgsFilterLineEdit = self.mTable.cellWidget(row, 8)
            noDataValues.append(tofloat(w.text(), None))

        del reader

        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: source,
            alg.P_NAMES: str(names),
            alg.P_WAVELENGTHS: str(wavelengths),
            alg.P_FWHMS: str(fwhms),
            alg.P_BAD_BAND_MULTIPLIERS: str(badBandMultipliers),
            alg.P_START_TIMES: str(startTimes),
            alg.P_END_TIMES: str(endTimes),
            alg.P_OFFSETS: str(offsets),
            alg.P_SCALES: str(scales),
            alg.P_NO_DATA_VALUES: str(noDataValues)
        }
        self.enmapBox.showProcessingAlgorithmDialog(alg, parameters, True, True, None, True, self)

        self.onSourceChanged()

    def onSetAcquisitionTimeClicked(self):
        dateTime = Utils.parseDateTime(self.mAcquisitionTime.text())
        for row in range(self.mTable.rowCount()):
            widget: QgsDateTimeEdit = self.mTable.cellWidget(row, 4)
            widget.setDateTime(dateTime)
            widget: QgsDateTimeEdit = self.mTable.cellWidget(row, 5)
            widget.clear()
            widget.displayNull()

    def onSetReflactanceScaleFactorClicked(self):
        reflactanceScaleFactor = float(self.mReflactanceScaleFactor.text())
        scale = 1. / reflactanceScaleFactor
        for row in range(self.mTable.rowCount()):
            widget: QgsFilterLineEdit = self.mTable.cellWidget(row, 7)
            widget.setText(str(scale))

    def onSetWavelengthClicked(self):
        values = eval(self.mWavelength.text())
        for row, value in enumerate(values):
            widget: QgsFilterLineEdit = self.mTable.cellWidget(row, 1)
            widget.setText(str(value))

    def onSetFwhmClicked(self):
        values = eval(self.mFwhm.text())
        for row, value in enumerate(values):
            widget: QgsFilterLineEdit = self.mTable.cellWidget(row, 2)
            widget.setText(str(value))

    def onSetBblClicked(self):
        values = eval(self.mFwhm.text())
        for row, value in enumerate(values):
            widget: QCheckBox = self.mTable.cellWidget(row, 3)
            widget.setChecked(value == 0)
