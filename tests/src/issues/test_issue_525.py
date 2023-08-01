import math

from qgis.core import QgsProject

from enmapbox.gui.dataviews.docks import SpectralLibraryDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibraryplotunitmodels import SpectralProfilePlotXAxisUnitModel
from enmapbox.qgispluginsupport.qps.unitmodel import UnitConverterFunctionModel, BAND_INDEX
from enmapbox.testing import start_app, EnMAPBoxTestCase, TestObjects

start_app()


class TestSpeclibUnitModel(EnMAPBoxTestCase):

    def test_unitModel(self):
        eb = EnMAPBox(load_core_apps=False, load_other_apps=False)
        eb.loadExampleData()
        speclib = TestObjects.createSpectralLibrary()
        sld: SpectralLibraryDock = eb.createSpectralLibraryDock(speclib=speclib, name='Test')

        # describes a new unit
        unitModel = SpectralProfilePlotXAxisUnitModel.instance()
        unitModel.addUnit('mumpitz', description='My Mumpitz Unit [mpx]')

        # describes how to convert from other units into this unit
        converterModel = UnitConverterFunctionModel.instance()

        import numpy as np

        def exampleFunction(value, *args):
            if isinstance(value, (list, np.ndarray)):
                f = np.vectorize(exampleFunction)
                return f(value)
            else:
                return value - 100

        for srcUnit in converterModel.sourceUnits():
            # define a conversion from source units to destination units
            converterModel.addConvertFunc(srcUnit, 'mumpitz', exampleFunction)

        self.showGui(eb.ui)
        eb.close()
        QgsProject.instance().removeAllMapLayers()
