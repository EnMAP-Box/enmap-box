from math import inf
from typing import Optional

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QToolButton, QMainWindow, QTableWidget, QListWidget, \
    QListWidgetItem, QLabel, QCheckBox, QLineEdit
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMapLayerProxyModel, QgsRasterLayer, QgsProcessing, QgsRasterBandStats
from qgis.gui import QgsRasterBandComboBox, QgsMapLayerComboBox, QgsFilterLineEdit, QgsDoubleSpinBox, QgsFileWidget

import processing
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from typeguard import typechecked


@typechecked
class SpectralIndexCreatorDialog(QMainWindow):
    mLayer: QgsMapLayerComboBox
    mUseReflectanceScaleFactor: QCheckBox
    mReflectanceScaleFactor: QLineEdit
    mEstimateReflectanceScaleFactor: QToolButton

    mSelectAll: QToolButton
    mClearSelection: QToolButton

    mAsiVegatation: QListWidget
    mAsiBurn: QListWidget
    mAsiWater: QListWidget
    mAsiSnow: QListWidget
    mAsiDrought: QListWidget
    mAsiUrban: QListWidget
    mAsiOther: QListWidget
    mAsiCustom: QListWidget

    mBandMapping: QTableWidget
    mAdditionalIndexParameters: QTableWidget

    mFilename: QgsFileWidget
    mRun: QToolButton

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        self.mAsiLists = {
            'vegetation': self.mAsiVegatation, 'burn': self.mAsiBurn, 'water': self.mAsiWater, 'snow': self.mAsiSnow,
            'drought': self.mAsiDrought, 'urban': self.mAsiUrban, 'other': self.mAsiOther
        }

        # init gui
        self.initSpectralIndices()
        self.initBandMapping()
        self.initAdditionalIndexParameters()
        self.onSelectAllClicked()
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        lineEdit: QgsFilterLineEdit = self.mFilename.lineEdit()
        lineEdit.setShowClearButton(True)
        lineEdit.setNullValue('[Save to temporary file]')
        lineEdit.clearValue()

        # connect signals
        self.mLayer.layerChanged.connect(self.onLayerChanged)
        self.mEstimateReflectanceScaleFactor.clicked.connect(self.onEstimateReflectanceScaleFactorClicked)
        self.mSelectAll.clicked.connect(self.onSelectAllClicked)
        self.mClearSelection.clicked.connect(self.onClearSelectionClicked)
        self.mRun.clicked.connect(self.onRunClicked)

    def initSpectralIndices(self):

        for name, spec in CreateSpectralIndicesAlgorithm.IndexDatabase.items():
            mList: QListWidget = self.mAsiLists.get(spec['type'])
            if mList is None:
                continue
            item = QListWidgetItem(f"{spec['short_name']}: {spec['long_name']}")
            item.setToolTip(f"{spec['formula']}")
            item.setCheckState(Qt.Unchecked)
            item.spec = spec
            mList.addItem(item)

    def initBandMapping(self):
        self.mBandMapping.setRowCount(len(CreateSpectralIndicesAlgorithm.ShortNames))
        for row, identifier in enumerate(CreateSpectralIndicesAlgorithm.ShortNames):
            wavelength, fwhm = CreateSpectralIndicesAlgorithm.WavebandMapping[identifier]
            wavelengthRange = f'{round(wavelength - fwhm / 2, 1)} - {round(wavelength + fwhm / 2, 1)}'
            self.mBandMapping.setCellWidget(row, 0, QLabel(CreateSpectralIndicesAlgorithm.LongNameMapping[identifier]))
            self.mBandMapping.setCellWidget(row, 1, QLabel(identifier))
            self.mBandMapping.setCellWidget(row, 2, QLabel(wavelengthRange))
            self.mBandMapping.setCellWidget(row, 3, QgsRasterBandComboBox())

    def initAdditionalIndexParameters(self):
        self.mAdditionalIndexParameters.setRowCount(len(CreateSpectralIndicesAlgorithm.ConstantMapping))
        for row, identifier in enumerate(CreateSpectralIndicesAlgorithm.ConstantMapping):
            self.mAdditionalIndexParameters.setCellWidget(
                row, 0, QLabel(CreateSpectralIndicesAlgorithm.LongNameMapping[identifier])
            )
            self.mAdditionalIndexParameters.setCellWidget(row, 1, QLabel(identifier))
            w = QgsDoubleSpinBox()
            w.setSingleStep(0)
            w.setMinimum(-inf)
            w.setMaximum(inf)
            w.setShowClearButton(True)
            w.setButtonSymbols(QgsDoubleSpinBox.NoButtons)
            w.setValue(CreateSpectralIndicesAlgorithm.ConstantMapping[identifier])
            w.setClearValue(CreateSpectralIndicesAlgorithm.ConstantMapping[identifier])

            self.mAdditionalIndexParameters.setCellWidget(row, 2, w)
        self.mAdditionalIndexParameters.setColumnWidth(0, 250)

    def currentFilename(self) -> Optional[str]:
        filename = self.mFilename.filePath()
        lineEdit: QgsFilterLineEdit = self.mFilename.lineEdit()
        if filename == lineEdit.nullValue():
            return QgsProcessing.TEMPORARY_OUTPUT
        else:
            return filename

    def onLayerChanged(self):

        layer = self.mLayer.currentLayer()
        self.mReflectanceScaleFactor.setText('')
        self.mUseReflectanceScaleFactor.setChecked(False)
        if layer is None:
            for row in range(self.mBandMapping.rowCount()):
                mBand: QgsRasterBandComboBox = self.mBandMapping.cellWidget(row, 3)
                mBand.setLayer(None)
                mBand.setBand(-1)
            return
        reader = RasterReader(layer)
        for row in range(self.mBandMapping.rowCount()):
            identifier = self.mBandMapping.cellWidget(row, 1).text()
            mBand: QgsRasterBandComboBox = self.mBandMapping.cellWidget(row, 3)
            mBand.setLayer(layer)
            wavelength, fwhm = CreateSpectralIndicesAlgorithm.WavebandMapping[identifier]
            bandNo = reader.findWavelength(wavelength)
            if bandNo is not None:
                inFwhmRange = abs(wavelength - reader.wavelength(bandNo)) < (fwhm / 2)
                if not inFwhmRange:
                    bandNo = None
            if bandNo is None:
                bandNo = -1
            mBand.setBand(bandNo)

    def onEstimateReflectanceScaleFactorClicked(self):
        layer = self.mLayer.currentLayer()
        if layer is None:
            return
        stats: QgsRasterBandStats = layer.dataProvider().bandStatistics(1, QgsRasterBandStats.Stats.Mean)
        if 0 <= stats.mean < 1:
            factor = '1'
        elif stats.mean < 100:
            factor = '100'
        elif stats.mean < 1000:
            factor = '10000'
        else:
            factor = ''
        self.mReflectanceScaleFactor.setText(factor)

    def onSelectAllClicked(self):
        for mList in self.mAsiLists.values():
            for row in range(mList.count()):
                item: QListWidgetItem = mList.item(row)
                item.setCheckState(Qt.Checked)

    def onClearSelectionClicked(self):
        for mList in self.mAsiLists.values():
            for row in range(mList.count()):
                item: QListWidgetItem = mList.item(row)
                item.setCheckState(Qt.Unchecked)

    def onRunClicked(self):

        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return

        # get band mapping
        bandMapping = dict()
        for row in range(self.mBandMapping.rowCount()):
            w: QLabel = self.mBandMapping.cellWidget(row, 1)
            identifier = w.text()
            w: QgsRasterBandComboBox = self.mBandMapping.cellWidget(row, 3)
            bandNo = w.currentBand()
            if bandNo != -1:
                bandMapping[identifier] = bandNo

        # get additional index parameters
        additionalIndexParameters = dict()
        for row in range(self.mAdditionalIndexParameters.rowCount()):
            w: QLabel = self.mAdditionalIndexParameters.cellWidget(row, 1)
            identifier = w.text()
            w: QgsDoubleSpinBox = self.mAdditionalIndexParameters.cellWidget(row, 2)
            value = w.value()
            if value == w.clearValue():  # skip defaults
                continue
            additionalIndexParameters[identifier] = value

        # get selected indices
        formulas = list()
        for mList in self.mAsiLists.values():
            for row in range(mList.count()):
                item: QListWidgetItem = mList.item(row)

                if item.checkState() == Qt.Unchecked:
                    continue

                short_name = item.text().split(':')[0]
                spectralIndex = CreateSpectralIndicesAlgorithm.IndexDatabase.get(short_name)
                spectralIndexBands = spectralIndex['bands']

                skip = False
                for band in spectralIndexBands:
                    if band in CreateSpectralIndicesAlgorithm.ConstantMapping:
                        continue
                    if band not in bandMapping:
                        skip = True
                if skip:
                    continue

                formulas.append(short_name)

        if len(formulas) == 0:
            return

        # get reflectance scale factor
        if self.mUseReflectanceScaleFactor.isChecked():
            try:
                reflectanceScaleFactor = float(self.mReflectanceScaleFactor.text())
            except Exception:
                reflectanceScaleFactor = None
                self.mReflectanceScaleFactor.setText('')
        else:
            reflectanceScaleFactor = None

        # create VRT layer
        filename = self.currentFilename()
        alg = CreateSpectralIndicesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: layer,
            alg.P_SCALE: reflectanceScaleFactor,
            alg.P_INDICES: ', '.join(formulas),
            alg.P_OUTPUT_VRT: filename
        }
        for name, bandNo in bandMapping.items():
            parameters[name] = bandNo
        for name, value in additionalIndexParameters.items():
            parameters[name] = value

        result = processing.runAndLoadResults(alg, parameters)

        self.enmapBox.addSource(result[alg.P_OUTPUT_VRT])
