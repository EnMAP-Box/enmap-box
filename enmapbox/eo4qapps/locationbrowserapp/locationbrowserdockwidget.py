import json
from os.path import join, dirname
from typing import Optional

from PyQt5.QtWidgets import QListWidgetItem, QCheckBox, QToolButton

from enmapbox import EnMAPBox
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint, SpatialExtent
from geetimeseriesexplorerapp import MapTool
from locationbrowserapp.locationbrowserresultwidget import LocationBrowserResultWidget
from qgis.PyQt import uic
from qgis._core import QgsCoordinateReferenceSystem, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, \
    QgsSingleSymbolRenderer
from qgis._gui import QgsFilterLineEdit
from qgis.gui import QgsDockWidget, QgisInterface
from typeguard import typechecked


@typechecked
class LocationBrowserDockWidget(QgsDockWidget):
    mSearch: QgsFilterLineEdit
    mResult: LocationBrowserResultWidget

    EnmapBoxInterface, QgisInterface = 0, 1

    def __init__(self, currentLocationMapTool: Optional[MapTool], parent=None):
        QgsDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        self.currentLocationMapTool = currentLocationMapTool

        # set from outside
        self.interface = None
        self.interfaceType = None

        # connect signals
        self.mSearch.editingFinished.connect(self.onTextEditingFinished)

    def enmapBoxInterface(self) -> EnMAPBox:
        return self.interface

    def qgisInterface(self) -> QgisInterface:
        return self.interface

    def setInterface(self, interface: QgisInterface):
        self.interface = interface
        if isinstance(interface, EnMAPBox):
            self.interfaceType = 0
        elif isinstance(interface, QgisInterface):
            self.interfaceType = 1
        else:
            raise ValueError()

        # connect current location changed signal
        if self.interfaceType == self.EnmapBoxInterface:
            self.enmapBoxInterface().sigCurrentLocationChanged.connect(self.onCurrentLocationChanged)
            parent = self.enmapBoxInterface().ui
        elif self.interfaceType == self.QgisInterface:
            self.currentLocationMapTool.sigClicked.connect(self.onCurrentLocationChanged)
            parent = None
            assert 0
        else:
            raise ValueError()

        self.mResult = LocationBrowserResultWidget(parent=parent)
        self.mResult.mList.currentItemChanged.connect(self.onResultSelectionChanged)
        self.mResult.mZoomToSelection.clicked.connect(self.onZoomToSelectionClicked)

    def onZoomToSelectionClicked(self):
        item = self.mResult.mList.currentItem()
        self.mResult.mDetails.clear()
        if not hasattr(item, 'json') or item.json is None:
            return
        self.mResult.mDetails.setText(json.dumps(item.json, indent=4))
        point = SpatialPoint(
            QgsCoordinateReferenceSystem.fromEpsgId(4326), float(item.json['lon']), float(item.json['lat'])
        )

        # remove existing polygon layer
        baseNamePolygon = 'Location Browser Boundary'
        baseNameLine = 'Location Browser Course'

        if self.interfaceType == self.EnmapBoxInterface:
            mapCanvas = self.enmapBoxInterface().currentMapCanvas()
            for aLayer in mapCanvas.layers():
                if aLayer.name() in [baseNamePolygon, baseNameLine]:
                    self.enmapBoxInterface().removeMapLayer(aLayer)
        elif self.interfaceType == self.QgisInterface:
            raise NotImplementedError()
        else:
            raise ValueError()

        type = item.json['geojson']['type']
        if type == 'MultiPolygon':
            layer = QgsVectorLayer('MultiPolygon?crs=epsg:4326', baseNamePolygon, 'memory')
            coordinates = item.json['geojson']['coordinates']
            coordinates = [[QgsPointXY(x, y) for x, y in polygon] for polygon in coordinates[0]]
            geometry = QgsGeometry.fromMultiPolygonXY([coordinates])
        elif type == 'Polygon':
            layer = QgsVectorLayer('MultiPolygon?crs=epsg:4326', baseNamePolygon, 'memory')
            coordinates = item.json['geojson']['coordinates']
            coordinates = [[QgsPointXY(x, y) for x, y in polygon] for polygon in coordinates]
            geometry = QgsGeometry.fromMultiPolygonXY([coordinates])
        elif type == 'LineString':
            layer = QgsVectorLayer('Linestring?crs=epsg:4326', baseNameLine, 'memory')
            coordinates = item.json['geojson']['coordinates']
            coordinates = [QgsPointXY(x, y) for x, y in coordinates]
            geometry = QgsGeometry.fromPolylineXY(coordinates)
        else:
            layer = QgsVectorLayer('MultiPolygon?crs=epsg:4326', baseNamePolygon, 'memory')
            y1, y2, x1, x2 = [float(v) for v in item.json['boundingbox']]
            coordinates = [
                [QgsPointXY(x1, y1), QgsPointXY(x1, y2), QgsPointXY(x2, y2), QgsPointXY(x2, y1), QgsPointXY(x1, y1)]
            ]
            geometry = QgsGeometry.fromMultiPolygonXY([coordinates])
        assert layer.isValid()

        provider = layer.dataProvider()
        feature = QgsFeature()
        feature.setGeometry(geometry)
        provider.addFeatures([feature])
        layer.updateExtents()
        if layer.name() == baseNamePolygon:
            qmlFile = join(dirname(__file__), 'defaultPolygonStyle.qml')
        elif layer.name() == baseNameLine:
            qmlFile = join(dirname(__file__), 'defaultLineStyle.qml')
        else:
            raise ValueError()
        layer.loadNamedStyle(qmlFile, False)

        if self.interfaceType == self.EnmapBoxInterface:
            mapCanvas = self.enmapBoxInterface().currentMapCanvas()
            mapCanvas.setCrosshairPosition(point, True)

            self.enmapBoxInterface().setCurrentLocation(point, self.enmapBoxInterface().currentMapCanvas())
            if coordinates is None:
                mapCanvas.setCenter(point.toCrs(mapCanvas.crs()))
            else:
                mapCanvas.setExtent(SpatialExtent(layer.crs(), layer.extent()))
                self.enmapBoxInterface().currentMapDock().insertLayer(0, layer)
            mapCanvas.refresh()

        elif self.interfaceType == self.QgisInterface:
            self.currentLocationMapTool.setCurrentLocation(point)
        else:
            raise ValueError()

    def onExtentClicked(self):
        pass

    def onResultSelectionChanged(self):
        self.liveUpdate()

    def onCurrentLocationChanged(self):
        pass

    def onTextEditingFinished(self):
        import requests
        import urllib.parse

        address = self.mSearch.value()
        #url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(address) + '?format=json'
        url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(address) + '?limit=50&extratags=1&polygon_geojson=1&format=json'

        jsons = requests.get(url).json()

        self.mResult.mList.clear()
        item = QListWidgetItem('')
        item.json = None
        self.mResult.mList.addItem(item)
        for json in jsons:
            item = QListWidgetItem(json['display_name'])
            item.json = json
            self.mResult.mList.addItem(item)

        self.mResult.show()

    def liveUpdate(self):
        if self.mResult.mLiveUpdate.isChecked():
            self.onZoomToSelectionClicked()

    def parseLocation(self, text:str):
        pass