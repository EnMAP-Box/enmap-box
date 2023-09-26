from typing import List, Tuple, Dict

from qgis.PyQt.QtCore import QSize

from deploy.enmapboxplugin.enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import prepareProfileValueDict
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprofilesources import SpectralProfileSource
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapbox.testing import start_app
from enmapbox import initAll
from qgis.core import QgsExpressionContext, QgsExpressionContextScope

app = start_app()

initAll()


class MyProfileSource(SpectralProfileSource):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def __eq__(self, other):
        if not isinstance(other, MyProfileSource):
            return False
        # todo: distinguish between other sources of same type
        return id(self) == id(other)

    def collectProfiles(self,
                        point: SpatialPoint,
                        kernel_size: QSize = QSize(1, 1), **kwargs) -> List[Tuple[Dict, QgsExpressionContext]]:
        profiles = []

        # todo: collect profiles for point 'point' within a pixel kernel of size 'kernel_size'

        context = QgsExpressionContext()
        scope = QgsExpressionContextScope('myScope')
        scope.setVariable('source', 'mySource', True)
        scope.setVariable('geo_x', point.x())
        scope.setVariable('geo_y', point.y())
        context.appendScope(scope)

        profileDict = prepareProfileValueDict(x=[300, 340, 360, 380],
                                              y=[0.4, 0.5, 0.43, 0.3],
                                              xUnit='μm')

        profiles.append((profileDict, context))
        return profiles

    def expressionContext(self) -> QgsExpressionContext:
        """
        Exemplary expression context. Should contain an example for each variable that is returned
        with collectProfiles()
        """
        context = QgsExpressionContext()
        scope = QgsExpressionContextScope('myScope')
        scope.setVariable('source', 'mySource', True)
        scope.setVariable('geo_x', 42.777, True)
        scope.setVariable('geo_y', 24.999, True)
        context.appendScope(scope)
        return context


source = MyProfileSource(name='MySource')
box = EnMAPBox(load_core_apps=False, load_other_apps=False)
box.loadExampleData()
box.spectralProfileSourcePanel().spectralProfileBridge().addSources(source)

box.ui.show()

app.exec_()
