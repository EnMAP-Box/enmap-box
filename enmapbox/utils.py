from typing import Optional, Tuple

from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMessageBox

from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from qgis.core import QgsRasterLayer
from typeguard import typechecked


@typechecked
def findBroadBand(raster: QgsRasterLayer, name: str, strict=False) -> Optional[int]:
    """
    Return raster band that best matches the given broad-band.
    If strict is True, return None, if matched band is outside the FWHM range.
    """

    return CreateSpectralIndicesAlgorithm.findBroadBand(raster, name, strict)


@typechecked
class BlockSignals(object):
    """Context manager for blocking QObject signals."""

    def __init__(self, *objects: QObject):
        self.objects = objects

    def __enter__(self):
        self.signalsBlocked = [obj.signalsBlocked() for obj in self.objects]
        for object in self.objects:
            object.blockSignals(True)

    def __exit__(self, exc_type, exc_value, tb):
        for object, signalsBlocked in zip(self.objects, self.signalsBlocked):
            object.blockSignals(signalsBlocked)


@typechecked
def isEarthEngineModuleInstalled() -> bool:
    import importlib
    spec = importlib.util.find_spec('ee')
    found = spec is not None
    return found


@typechecked
def isEarthEnginePluginInstalled() -> bool:
    from pyplugin_installer.installer_data import plugins
    ee_plugin = plugins.all()['ee_plugin']
    return ee_plugin['installed']


@typechecked
def importEarthEngine(showMessage=True, parent=None) -> Tuple[bool, object]:
    if isEarthEngineModuleInstalled():
        import ee

        # ## debugging
        # import traceback
        # traceback.print_stack()
        # QMessageBox.information(parent, 'DEBUG', 'Just imported the "ee" module!')
        # ##

        return True, ee
    else:
        if showMessage:
            message = "Google Earth Engine plugin not installed. Can't import 'ee' module."
            QMessageBox.information(parent, 'Missing dependency', message)
        return False, None
