from pprint import pformat
from typing import Optional

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QToolButton, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QSlider, QSizePolicy, \
    QLineEdit
from qgis.core import QgsRasterLayer
from qgis.gui import QgsRasterBandComboBox

from enmapboxprocessing.rasterreader import RasterReader

ASI_BANDS = {
    "A": {
        "description": "Aerosols",
        "wavelength": (400, 455),
        "sentinel2": "B1",
        "landsat89": "B1",
        "landsat457": None,
        "modis": None,
    },
    "B": {
        "description": "Blue",
        "wavelength": (450, 530),
        "sentinel2": "B2",
        "landsat89": "B2",
        "landsat457": "B1",
        "modis": "B3",
    },
    "G": {
        "description": "Green",
        "wavelength": (510, 600),
        "sentinel2": "B3",
        "landsat89": "B3",
        "landsat457": "B2",
        "modis": "B4",
    },
    "G1": {
        "description": "Green 1",
        "wavelength": (510, 550),
        "sentinel2": None,
        "landsat89": None,
        "landsat457": None,
        "modis": "B11",
    },
    "Y": {
        "description": "Yellow",
        "wavelength": (585, 625),
        "sentinel2": None,
        "landsat89": None,
        "landsat457": None,
        "modis": None,
    },
    "R": {
        "description": "Red",
        "wavelength": (620, 690),
        "sentinel2": "B4",
        "landsat89": "B4",
        "landsat457": "B3",
        "modis": "B1",
    },
    "RE1": {
        "description": "Red Edge 1",
        "wavelength": (695, 715),
        "sentinel2": "B5",
        "landsat89": None,
        "landsat457": None,
        "modis": None,
    },
    "RE2": {
        "description": "Red Edge 2",
        "wavelength": (730, 750),
        "sentinel2": "B6",
        "landsat89": None,
        "landsat457": None,
        "modis": None,
    },
    "RE3": {
        "description": "Red Edge 3",
        "wavelength": (765, 795),
        "sentinel2": "B7",
        "landsat89": None,
        "landsat457": None,
        "modis": None,
    },
    "N": {
        "description": "Near-Infrared (NIR)",
        "wavelength": (760, 900),
        "sentinel2": "B8",
        "landsat89": "B5",
        "landsat457": "B4",
        "modis": "B2",
    },
    "N2": {
        "description": "Near-Infrared (NIR) 2",
        "wavelength": (850, 880),
        "sentinel2": "B8A",
        "landsat89": None,
        "landsat457": None,
        "modis": None,
    },
    "WV": {
        "description": "Water Vapour",
        "wavelength": (930, 960),
        "sentinel2": "B9",
        "landsat89": None,
        "landsat457": None,
        "modis": None,
    },
    "S1": {
        "description": "Short-wave Infrared (SWIR) 1",
        "wavelength": (1550, 1750),
        "sentinel2": "B11",
        "landsat89": "B6",
        "landsat457": "B5",
        "modis": "B6",
    },
    "S2": {
        "description": "Short-wave Infrared (SWIR) 2",
        "wavelength": (2080, 2350),
        "sentinel2": "B12",
        "landsat89": "B7",
        "landsat457": "B7",
        "modis": "B7",
    },
    "T": {
        "description": "Thermal Infrared",
        "wavelength": (10400, 12500),
        "sentinel2": None,
        "landsat89": None,
        "landsat457": "B6",
        "modis": None,
    },
    "T1": {
        "description": "Thermal Infrared 1",
        "wavelength": (10600, 11190),
        "sentinel2": None,
        "landsat89": "B10",
        "landsat457": None,
        "modis": None,
    },
    "T2": {
        "description": "Thermal Infrared 2",
        "wavelength": (11500, 12510),
        "sentinel2": None,
        "landsat89": "B11",
        "landsat457": None,
        "modis": None,
    },
}


class SpectralRasterBandComboBox(QWidget):
    mLayout: QVBoxLayout
    mName: QLabel
    mBandNo: QgsRasterBandComboBox
    mSlider: QSlider
    mWavelength: QLineEdit

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        self.mBandNo.bandChanged.connect(self.onBandChanged)
        self.mSlider.valueChanged.connect(self.mBandNo.setBand)

        self.layer: QgsRasterLayer = None
        self.reader: RasterReader = None

    def initBandButtons(self, names=None):
        if names is None:
            names = ('A', 'B', 'G', 'R', 'RE1', 'RE2', 'RE3', 'N', 'S1', 'S2', 'T1', 'T2')

        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(2)
        buttonLayout.setContentsMargins(0, 0, 0, 0)
        for name in names:
            button = QToolButton()
            button.setText(name)
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            button.setToolTip(str(pformat(ASI_BANDS[name], indent=4, sort_dicts=False)))
            buttonLayout.addWidget(button)
            button.clicked.connect(self.onAsiBandClicked)

        self.mLayout.addLayout(buttonLayout)

    def setLayer(self, layer: Optional[QgsRasterLayer]):
        if layer is None:
            self.mBandNo.setBand(-1)
            self.reader = None
        else:
            self.mBandNo.setBand(1)
            self.reader = RasterReader(layer)
            self.mSlider.setMinimum(1)
            self.mSlider.setMaximum(self.reader.bandCount())
        self.mBandNo.setLayer(layer)
        self.onBandChanged()

    def onBandChanged(self):
        bandNo = self.mBandNo.currentBand()
        if bandNo == -1:
            self.mWavelength.setText('N/A')
            self.mSlider.setEnabled(False)
        else:
            self.mSlider.setEnabled(True)
            wavelength = self.reader.wavelength(bandNo)
            if wavelength is None:
                self.mWavelength.setText('N/A')
            else:
                self.mWavelength.setText(str(int(wavelength)) + ' nm')
        self.mSlider.setValue(bandNo)

    def onAsiBandClicked(self):
        button: QToolButton = self.sender()
        name = button.text()
        vmin, vmax = ASI_BANDS[name]['wavelength']
        vcenter = (vmin + vmax) / 2
        bandNo = self.reader.findWavelength(vcenter)
        if bandNo is None:
            return
        self.mBandNo.setBand(bandNo)
