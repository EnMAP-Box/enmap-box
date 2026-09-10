import importlib.util
import unittest

import numpy as np
from qgis.core import QgsVectorLayer

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import surfaceLongFormat

pyvista_error = None
if importlib.util.find_spec('pyvista') is not None:
    try:
        import pyvista as pv

        print(pv.__version__)
        from spectralsurfaceplottingapp.spectralsurfaceplottingwindow import SpectralSurfacePlottingWindow

    except ImportError as e:
        pyvista_error = f'Unable to import pyvista: {e}'

qgsApp = start_app()
initAll()


@unittest.skipIf(pyvista_error, str(pyvista_error))
class TestSpectralSurfacePlottingApp(TestCase):

    def testGui(self):
        enmapBox = EnMAPBox()
        table = QgsVectorLayer(surfaceLongFormat, 'long_format.csv')
        enmapBox.onDataDropped([table])

        widget = SpectralSurfacePlottingWindow()
        self.showGui([enmapBox.ui, widget])
        widget.close()
        enmapBox.close()

    def testPlotter(self):
        enmapBox = EnMAPBox()
        x, y, z = getRandomData()

        widget = SpectralSurfacePlottingWindow()
        widget.setData(y, x, z, z)
        widget.plotData()
        # widget.autoScale()
        # widget.setScale(100, 100, 100)
        # self.showGui([enmapBox.ui, widget])
        enmapBox.close()


def getRandomData():
    rng = np.random.default_rng(seed=42)
    number_of_points = 500
    x = rng.random(number_of_points) * 100
    y = rng.random(number_of_points) * 100
    z = np.sinc((x - 20) / 100 * np.pi) + np.sinc((y - 50) / 100 * np.pi)
    return x, y, z
