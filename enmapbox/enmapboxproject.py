from typing import Any, List, Dict, Tuple

from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer


class EnMAPBoxProject(QgsProject):
    """
    A QgsProject subclass that provides additional functionality for managing map layers
    and selections in the EnMAP-Box application.

    Main purpose: ensure that layer references are not lost and killed by the Python garbage collector.
    """

    sigSelectionChanged = pyqtSignal(str)

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.setTitle('EnMAP-Box')
        self.mLayerRefs: list[QgsMapLayer] = []
        self.mLayerConnections: Dict[str, List[Tuple]] = {}

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.title()}">'

    def removeAllMapLayers(self):
        """
        Removes all map layers from the project.
        But does not call the super class method removeAllMapLayers() to keep existing layer refs alive.
        """
        all_layers = self.mapLayers().values()
        for layer in all_layers:
            self.__remove_layer_ref(layer)
            self.takeMapLayer(layer)
        self.mLayerRefs.clear()

    def addMapLayer(self, mapLayer: QgsMapLayer, *args, **kwds) -> QgsMapLayer | None:
        # self.debugPrint('addMapLayer')
        lyr = super().addMapLayer(mapLayer, *args, **kwds)
        self.__add_layer_ref(lyr)
        return lyr

    def __add_layer_ref(self, layer: QgsMapLayer | Any):
        if not isinstance(layer, QgsMapLayer):
            return
        if layer not in self.mLayerRefs:
            self.mLayerRefs.append(layer)
        if isinstance(layer, QgsVectorLayer):
            signal = layer.selectionChanged
            conn = signal.connect(lambda *args, lid=layer.id(): self.sigSelectionChanged.emit(lid))
            connections = self.mLayerConnections.get(layer.id(), [])
            connections.append((signal, conn))
            self.mLayerConnections[layer.id()] = connections

    def __remove_layer_ref(self, layer: Any):
        if not isinstance(layer, QgsMapLayer):
            return
        if layer in self.mLayerRefs:
            for (signal, conn) in self.mLayerConnections.get(layer.id(), []):
                signal.disconnect(conn)
            self.mLayerRefs.remove(layer)

    def addMapLayers(self, mapLayers: QgsMapLayer, *args, **kwargs) -> List[QgsMapLayer]:
        # self.debugPrint(f'addMapLayers {mapLayers}')
        added_layers = super().addMapLayers(mapLayers)
        for lyr in added_layers:
            self.__add_layer_ref(lyr)
        return added_layers

    def removeMapLayers(self, layers: List[QgsMapLayer | str]):
        """
        Removes the layers from the project, but does never all super().removeMapLayer to not
        destroy a reference to the layer
        """
        for lyr in layers:
            if isinstance(lyr, str):
                lyr = self.mapLayer(lyr)

            if isinstance(lyr, QgsMapLayer):
                self.takeMapLayer(lyr)

    def takeMapLayer(self, layer: QgsMapLayer) -> QgsMapLayer:
        self.__remove_layer_ref(layer)
        return super().takeMapLayer(layer)

    def debugPrint(self, msg: str = ''):

        keysE = list(self.mapLayers().keys())
        if len(keysE) != len(self.mLayerRefs):
            print('Warning: differing layer refs')
        keysQ = list(QgsProject.instance().mapLayers().keys())

        rows = [['EnMAPBox', 'QGIS', 'Layer ID']]
        for k in sorted(set(keysE + keysQ)):
            rows.append([str(k in keysE), str(k in keysQ), k])
        info = '\n'.join(['{:<8}\t{:<4}\t{}'.format(*row) for row in rows])
        if len(rows) == 1:
            info += '\t - no map layers -'
        print(info, flush=True)
