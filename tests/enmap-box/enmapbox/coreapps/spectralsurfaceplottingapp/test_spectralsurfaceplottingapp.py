import numpy as np
from qgis.core import QgsVectorLayer

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import surfaceLongFormat
from spectralsurfaceplottingapp.spectralsurfaceplottingwindow import SpectralSurfacePlottingWindow

qgsApp = start_app()
initAll()


class TestSpectralSurfacePlottingApp(TestCase):

    def testGui(self):
        enmapBox = EnMAPBox(None)
        table = QgsVectorLayer(surfaceLongFormat, 'long_format.csv')
        enmapBox.onDataDropped([table])

        widget = SpectralSurfacePlottingWindow()
        widget.show()

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)

    def testPlotter(self):
        enmapBox = EnMAPBox(None)
        x, y, z = getRandomData()
        x, y, z = getLmuWeizen()

        widget = SpectralSurfacePlottingWindow()
        widget.setData(y, x, z)
        widget.plotData()
        # widget.autoScale()
        # widget.setScale(100, 100, 100)
        widget.show()
        if False:
            qgsApp.exec()

        widget.show()

        if not False:
            qgsApp.exec()

        self.dispose_widget(enmapBox.ui)
        self.dispose_widget(widget)


def getRandomData():
    rng = np.random.default_rng(seed=42)
    number_of_points = 500
    x = rng.random(number_of_points) * 100
    y = rng.random(number_of_points) * 100
    z = np.sinc((x - 20) / 100 * np.pi) + np.sinc((y - 50) / 100 * np.pi)
    return x, y, z


def getLmuWeizen():
    data = np.genfromtxt(r'C:\Users\janzandr\Downloads\STS_Weizen_2017_orig.csv', delimiter=';')
    wavelength = data[0, 3:]
    doys = data[2:, 0]
    values = data[2:, 3:]
    x = list()
    y = list()
    z = list()
    for xi, doyi in enumerate(doys):
        for yi, wli in enumerate(wavelength):
            x.append(doyi)
            y.append(wli)
            z.append(values[xi, yi])
    return x, y, z
