import traceback

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.typeguard import typechecked
from enmapboxprocessing.rasterreader import RasterReader
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QTableWidget, QComboBox, QLineEdit, QCheckBox, QTableWidgetItem, QLabel, QToolButton
from qgis.core import QgsMapLayerProxyModel, QgsProcessingContext, QgsProject
from qgis.gui import QgsMapLayerComboBox, QgsCheckableComboBox, QgsRasterBandComboBox, QgsFilterLineEdit, QgsDockWidget, \
    QgisInterface, QgsMessageBar


@typechecked
class SpectralIndexExplorerDockWidget(QgsDockWidget):
    mLayer: QgsMapLayerComboBox
    mFilterText: QgsFilterLineEdit
    mFilterCase: QToolButton
    mFilterDomain: QgsCheckableComboBox
    mInfo: QLabel
    mTableIndices: QTableWidget
    mTableBands: QTableWidget
    mTableConstants: QTableWidget
    mMode: QComboBox
    mEditLayerName: QLineEdit
    mEditFormula: QLineEdit
    mLiveUpdate: QCheckBox
    mApply: QToolButton
    mMessageBar: QgsMessageBar

    EnmapBoxInterface, QgisInterface = 0, 1

    def __init__(self, parent=None):
        # QgsDockWidget.__init__(self, parent)
        super().__init__(parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        # set from outside
        self.interface = None
        self.interfaceType = None

        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.loadIndices()
        self.loadBands()
        self.loadConstants()

        # connect signals
        self.mLayer.layerChanged.connect(self.onLayerChanged)
        self.mFilterText.valueChanged.connect(self.onFilterChanged)
        self.mFilterCase.clicked.connect(self.onFilterChanged)
        self.mFilterDomain.checkedItemsChanged.connect(self.onFilterChanged)
        self.mTableIndices.itemSelectionChanged.connect(self.onSelectionChanged)
        self.mApply.clicked.connect(self.onApplyClicked)

    def enmapBoxInterface(self) -> EnMAPBox:
        return self.interface

    def qgisInterface(self):
        return self.interface

    def setInterface(self, interface):
        self.interface = interface
        if isinstance(interface, EnMAPBox):
            self.interfaceType = 0
            self.mLayer.setProject(interface.project())
        elif isinstance(interface, QgisInterface):
            self.interfaceType = 1
        else:
            raise ValueError()

    def setRowDisabled(self, row: int, disable: bool):
        if disable:
            italic = True
            color = QColor('gray')
        else:
            italic = False
            color = QColor('black')

        item = self.mTableIndices.verticalHeaderItem(row)
        font = item.font()
        font.setItalic(italic)
        item.setFont(font)
        item.setForeground(color)
        for col in range(self.mTableIndices.columnCount()):
            item = self.mTableIndices.item(row, col)
            font = item.font()
            font.setItalic(italic)
            item.setFont(font)
            item.setForeground(color)

    def onFilterChanged(self):
        caseSensitive = self.mFilterCase.isChecked()
        filterText = self.mFilterText.text()
        filterDomains = [domain.lower() for domain in self.mFilterDomain.checkedItems()]
        allBands = set()
        mappedBands = set()
        for row in range(self.mTableBands.rowCount()):
            mBand: QgsRasterBandComboBox = self.mTableBands.cellWidget(row, 3)
            bandName = self.mTableBands.verticalHeaderItem(row).text()
            allBands.add(bandName)
            if mBand.currentBand() >= 1:
                mappedBands.add(bandName)

        hidden = 0
        for row in range(self.mTableIndices.rowCount()):
            # text filter
            itemText = self.mTableIndices.verticalHeaderItem(row).text()
            for col in range(self.mTableIndices.columnCount()):
                itemText += self.mTableIndices.item(row, col).text()

            if caseSensitive:
                show = filterText in itemText
            else:
                show = filterText.lower() in itemText.lower()

            itemDomain = self.mTableIndices.item(row, 2).text()

            # domain filter
            if itemDomain == 'kernel':
                show = False
            elif len(filterDomains) == 0:
                pass
            elif itemDomain not in filterDomains:
                show = False

            # missing band indicator (italic and gray font)
            requiredBands = set(self.mTableIndices.item(row, 5).text().split(', ')).intersection(allBands)
            disabled = not requiredBands.issubset(mappedBands)
            self.setRowDisabled(row, disabled)

            self.mTableIndices.setRowHidden(row, not show)
            if not show:
                hidden += 1

        self.mInfo.setText(
            '[' + str(self.mTableIndices.rowCount() - hidden) + '/' + str(self.mTableIndices.rowCount()) + ']')

    def onSelectionChanged(self):
        row = self.mTableIndices.currentRow()
        name = self.mTableIndices.verticalHeaderItem(row).text()
        formula = self.mTableIndices.item(row, 0).text()
        longName = self.mTableIndices.item(row, 1).text()
        disabled = self.mTableIndices.verticalHeaderItem(row).font().italic()
        if disabled:
            return
        else:
            self.mEditLayerName.setText(name + ' - ' + longName)
            self.mEditFormula.setText(formula)

        self.onLiveUpdate()

    def onLayerChanged(self):
        layer = self.mLayer.currentLayer()
        if layer is None:
            for row in range(self.mTableBands.rowCount()):
                mBand: QgsRasterBandComboBox = self.mTableBands.cellWidget(row, 3)
                mBand.setLayer(None)
                mBand.setBand(-1)
            return
        reader = RasterReader(layer)
        for row in range(self.mTableBands.rowCount()):
            vmin, vmax = map(int, self.mTableBands.item(row, 2).text().split(' - '))
            vcenter = (vmin + vmax) / 2
            mBand: QgsRasterBandComboBox = self.mTableBands.cellWidget(row, 3)
            mBand.setLayer(layer)
            bandNo = reader.findWavelength(vcenter)
            if bandNo is None:
                bandNo = -1
            elif reader.wavelength(bandNo) < vmin:
                bandNo = -1
            elif reader.wavelength(bandNo) > vmax:
                bandNo = -1
            mBand.setBand(bandNo)
        self.onFilterChanged()

    def onLiveUpdate(self):
        if not self.mLiveUpdate.isChecked():
            return

        self.onApplyClicked()

    def onApplyClicked(self):
        self.apply()

    def loadBands(self):
        from spectralindexexplorerapp import SpectralIndexLayerAlgorithm
        self.mTableBands.setRowCount(len(SpectralIndexLayerAlgorithm.Bands))
        self.mTableBands.setVerticalHeaderLabels(SpectralIndexLayerAlgorithm.Bands)
        for i, (k, v) in enumerate(SpectralIndexLayerAlgorithm.Bands.items()):
            self.mTableBands.setItem(i, 0, QTableWidgetItem(v['long_name'])),
            self.mTableBands.setItem(i, 1, QTableWidgetItem(v['common_name']))
            self.mTableBands.setItem(i, 2, QTableWidgetItem(f"{v['min_wavelength']} - {v['max_wavelength']}"))
            w = QgsRasterBandComboBox()
            w.bandChanged.connect(self.onFilterChanged)
            self.mTableBands.setCellWidget(i, 3, w)

    def loadConstants(self):
        from spectralindexexplorerapp import SpectralIndexLayerAlgorithm
        self.mTableConstants.setRowCount(len(SpectralIndexLayerAlgorithm.Constants))
        self.mTableConstants.setVerticalHeaderLabels(SpectralIndexLayerAlgorithm.Constants)
        for i, (k, v) in enumerate(SpectralIndexLayerAlgorithm.Constants.items()):
            try:
                self.mTableConstants.setItem(i, 0, QTableWidgetItem(str(float(v['default'])))),
            except Exception:
                self.mTableConstants.setItem(i, 0, QTableWidgetItem('')),
            self.mTableConstants.setItem(i, 1, QTableWidgetItem(v['description']))

    def loadIndices(self):
        from spectralindexexplorerapp import SpectralIndexLayerAlgorithm
        domains = set()
        self.mTableIndices.setRowCount(len(SpectralIndexLayerAlgorithm.Indices))
        self.mTableIndices.setVerticalHeaderLabels(SpectralIndexLayerAlgorithm.Indices)
        for i, (k, v) in enumerate(SpectralIndexLayerAlgorithm.Indices.items()):
            tooltip = '''<div style="font-family:Arial, sans-serif; line-height:1.6;">'''
            tooltip += f"<h2>{v['long_name']}</h2>"
            tooltip += f"<p><strong>Short Name</strong><br>{v['short_name']}</p>"
            tooltip += f"<p><strong>Formula</strong><br><code>{v['formula']}</code></p>"
            tooltip += f"<p><strong>Application Domain</strong><br>{v['application_domain']}</p>"
            tooltip += f"<p><strong>Platforms</strong><br>{", ".join(v['platforms'])}</p>"
            tooltip += f"<p><strong>Bands</strong><br>{", ".join(v['bands'])}</p>"
            tooltip += '</div>'

            self.mTableIndices.setItem(i, 0, QTableWidgetItem(v['formula'])),
            self.mTableIndices.setItem(i, 1, QTableWidgetItem(v['long_name'])),
            self.mTableIndices.setItem(i, 2, QTableWidgetItem(v['application_domain']))
            self.mTableIndices.setItem(i, 3, QTableWidgetItem(v['contributor']))
            self.mTableIndices.setItem(i, 4, QTableWidgetItem(v['reference']))
            self.mTableIndices.setItem(i, 5, QTableWidgetItem(', '.join(v['bands'])))

            for j in range(self.mTableIndices.columnCount()):
                self.mTableIndices.item(i, j).setToolTip(tooltip)
            self.mTableIndices.verticalHeaderItem(i).setToolTip(tooltip)

            domains.add(v['application_domain'])

        self.mFilterDomain.clear()
        self.mFilterDomain.addItems(domains)

        self.onFilterChanged()

    def apply(self):
        from spectralindexexplorerapp import SpectralIndexLayerAlgorithm
        layer = self.mLayer.currentLayer()
        if layer is None:
            self.mMessageBar.pushInfo('Missing parameter', 'select a source layer')
            return

        formula = self.mEditFormula.text()
        if formula == '':
            self.mMessageBar.pushInfo('Missing parameter', 'select a spectral index')
            return

        layerName = self.mEditLayerName.text()
        if layerName == '':
            layerName = formula

        # for predef index, use shortname as formula for better metadata support
        shortName = layerName.split(' - ')[0]
        if shortName in SpectralIndexLayerAlgorithm.Indices:
            if formula == SpectralIndexLayerAlgorithm.Indices[shortName]['formula']:
                formula = shortName

        mapping = []
        for row in range(self.mTableBands.rowCount()):
            name = self.mTableBands.verticalHeaderItem(row).text()
            w: QgsRasterBandComboBox = self.mTableBands.cellWidget(row, 3)
            bandNo = w.currentBand()
            if bandNo >= 1:
                mapping.append(name)
                mapping.append(str(bandNo))
        for row in range(self.mTableConstants.rowCount()):
            name = self.mTableConstants.verticalHeaderItem(row).text()
            value = self.mTableConstants.item(row, 0).text()
            try:
                value = float(value)
                mapping.append(name)
                mapping.append(value)
            except Exception:
                pass

        alg = SpectralIndexLayerAlgorithm()
        parameters = {
            alg.P_RASTER: layer,
            alg.P_FORMULA: formula,
            alg.P_BAND_MAPPING: mapping,
            alg.P_LAYER_NAME: layerName
        }
        context = QgsProcessingContext()

        try:
            result = alg.runAlg(alg, parameters, None, None, context)
            layer = context.takeResultLayer(result[alg.P_OUTPUT_RASTER])
            if not layer.isValid():
                self.mMessageBar.pushCritical('Error', 'spectral index creation failed')
                return
            self.mMessageBar.pushSuccess('Success', 'spectral index layer created')
        except Exception as error:
            traceback.print_exc()
            self.mMessageBar.pushCritical('Error', str(error))

        if self.interfaceType == self.EnmapBoxInterface:
            mapDock = self.enmapBoxInterface().currentMapDock()
            if mapDock is None:
                self.enmapBoxInterface().onDataDropped([layer])
            else:
                mapDock.insertLayer(0, layer)
        elif self.interfaceType == self.QgisInterface:
            QgsProject.instance().addMapLayer(layer)
        else:
            raise ValueError()
