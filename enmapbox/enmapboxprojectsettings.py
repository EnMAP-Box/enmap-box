from typing import Dict

from PyQt5.QtXml import QDomDocument, QDomElement

from qgis._core import QgsXmlUtils
from qgis._gui import QgsDockWidget


class EnMAPBoxProjectSettings(object):
    # (adopted from Data Plotly plugin)

    def writeToProject(self, document: QDomDocument):
        element = self.writeXml(document)
        parent_element = document.createElement('EnMAP-Box')
        parent_element.appendChild(element)

        root_node = document.elementsByTagName("qgis").item(0)
        root_node.appendChild(parent_element)

    def readFromProject(self, document: QDomDocument):
        root_node = document.elementsByTagName("qgis").item(0)
        node = root_node.toElement().firstChildElement('EnMAP-Box')
        element = node.toElement()
        return self.readXml(element.firstChildElement())

    def writeXml(self, document: QDomDocument):
        settings = self.getSettings()

        self.writeProject.emit(settings)

        element = QgsXmlUtils.writeVariant(settings, document)
        return element

    def readXml(self, element: QDomElement):
        settings = QgsXmlUtils.readVariant(element)
        self.setSettings(settings)

    def getSettings(self) -> Dict:
        from geetimeseriesexplorerapp import GeeTimeseriesExplorerDockWidget
        from locationbrowserapp import LocationBrowserDockWidget
        from profileanalyticsapp import ProfileAnalyticsDockWidget
        from rasterbandstackingapp import RasterBandStackingDockWidget
        from sensorproductimportapp import SensorProductImportDockWidget
        from enmapbox.gui.datasources.manager import DataSourceManagerPanelUI
        from enmapbox.gui.dataviews.dockmanager import DockPanelUI
        from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprofilesources import SpectralProfileSourcePanel

        from qgis.utils import iface
        from enmapbox import EnMAPBox
        enmapBox = EnMAPBox.instance()

        settings = dict()

        # QGIS GUI
        qgisMainWindow = iface.mapCanvas().parent().parent().parent()
        # - EO4Q apps (inside QGIS)
        for dockWidget in qgisMainWindow.findChildren(QgsDockWidget):
            if isinstance(dockWidget, GeeTimeseriesExplorerDockWidget):
                pass  # don't save GUI state
            if isinstance(dockWidget, LocationBrowserDockWidget):
                pass  # don't save GUI state
            if isinstance(dockWidget, ProfileAnalyticsDockWidget):
                settings[f'EO4Q/{ProfileAnalyticsDockWidget.__name__}'] = dockWidget.projectSettings()
            if isinstance(dockWidget, RasterBandStackingDockWidget):
                pass  # don't save GUI state
            if isinstance(dockWidget, SensorProductImportDockWidget):
                pass  # don't save GUI state

        # EnMAP-Box GUI
        if enmapBox is not None:
            enmapBoxMainWindow = enmapBox.ui
            for dockWidget in enmapBoxMainWindow.findChildren(QgsDockWidget):
                # - EO4Q apps (inside EnMAP-Box)
                if isinstance(dockWidget, GeeTimeseriesExplorerDockWidget):
                    pass  # don't save GUI state
                if isinstance(dockWidget, LocationBrowserDockWidget):
                    pass  # don't save GUI state
                if isinstance(dockWidget, ProfileAnalyticsDockWidget):
                    settings[ProfileAnalyticsDockWidget.__name__] = dockWidget.projectSettings()
                if isinstance(dockWidget, RasterBandStackingDockWidget):
                    pass  # don't save GUI state
                if isinstance(dockWidget, SensorProductImportDockWidget):
                    pass  # don't save GUI state

                # other panels
                if isinstance(dockWidget, DataSourceManagerPanelUI):
                    settings[DataSourceManagerPanelUI.__name__] = dockWidget.projectSettings()
                if isinstance(dockWidget, DockPanelUI):
                    pass  # todo
                if isinstance(dockWidget, SpectralProfileSourcePanel):
                    pass  # todo

        return settings

    def setSettings(self, settings: Dict):
        from geetimeseriesexplorerapp import GeeTimeseriesExplorerDockWidget
        from locationbrowserapp import LocationBrowserDockWidget
        from profileanalyticsapp import ProfileAnalyticsDockWidget
        from rasterbandstackingapp import RasterBandStackingDockWidget
        from sensorproductimportapp import SensorProductImportDockWidget
        from enmapbox.gui.datasources.manager import DataSourceManagerPanelUI
        from enmapbox.gui.dataviews.dockmanager import DockPanelUI
        from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprofilesources import SpectralProfileSourcePanel

        from qgis.utils import iface
        from enmapbox import EnMAPBox
        enmapBox = EnMAPBox.instance()

        # QGIS GUI
        qgisMainWindow = iface.mapCanvas().parent().parent().parent()
        # - EO4Q apps (inside QGIS)
        for dockWidget in qgisMainWindow.findChildren(QgsDockWidget):
            if isinstance(dockWidget, GeeTimeseriesExplorerDockWidget):
                pass
            if isinstance(dockWidget, LocationBrowserDockWidget):
                pass
            if isinstance(dockWidget, ProfileAnalyticsDockWidget):
                dockWidget.setProjectSettings(settings[f'EO4Q/{ProfileAnalyticsDockWidget.__name__}'])
            if isinstance(dockWidget, RasterBandStackingDockWidget):
                pass
            if isinstance(dockWidget, SensorProductImportDockWidget):
                pass

        # EnMAP-Box GUI
        if enmapBox is not None:
            enmapBoxMainWindow = enmapBox.ui
            for dockWidget in enmapBoxMainWindow.findChildren(QgsDockWidget):
                # - EO4Q apps (inside EnMAP-Box)
                if isinstance(dockWidget, GeeTimeseriesExplorerDockWidget):
                    pass  # don't save GUI state
                if isinstance(dockWidget, LocationBrowserDockWidget):
                    pass  # don't save GUI state
                if isinstance(dockWidget, ProfileAnalyticsDockWidget):
                    dockWidget.setProjectSettings(settings[ProfileAnalyticsDockWidget.__name__])
                if isinstance(dockWidget, RasterBandStackingDockWidget):
                    pass  # don't save GUI state
                if isinstance(dockWidget, SensorProductImportDockWidget):
                    pass  # don't save GUI state

                # other panels
                if isinstance(dockWidget, DataSourceManagerPanelUI):
                    dockWidget.setProjectSettings(settings[DataSourceManagerPanelUI.__name__])
                if isinstance(dockWidget, DockPanelUI):
                    pass  # todo
                if isinstance(dockWidget, SpectralProfileSourcePanel):
                    pass  # todo
