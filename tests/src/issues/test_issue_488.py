from enmapboxprocessing.testcase import TestCase


class Issue488Tests(TestCase):

    def test_issue_488(self):
        from qgis.core import QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsFeatureRenderer
        symbol = QgsMarkerSymbol.createSimple({'name': 'square', 'color': 'white'})
        renderer = QgsSingleSymbolRenderer(symbol)
        assert isinstance(renderer, QgsFeatureRenderer)

        from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibraryplotwidget import SpectralProfilePlotModel
        model = SpectralProfilePlotModel()
