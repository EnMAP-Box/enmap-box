import json
import urllib.parse
from os.path import join, dirname
from typing import Optional

import requests
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint, SpatialExtent
from enmapboxprocessing.utils import Utils
from geetimeseriesexplorerapp import MapTool
from locationbrowserapp.locationbrowserresultwidget import LocationBrowserResultWidget
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QListWidgetItem, QToolButton
from qgis.core import QgsCoordinateReferenceSystem, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject
from qgis.gui import QgsFilterLineEdit, QgsDockWidget, QgisInterface
from typeguard import typechecked


@typechecked
class LocationBrowserDockWidget(QgsDockWidget):
    mSearch: QgsFilterLineEdit
    mGoToLocation: QToolButton
    mRequestNominatim: QToolButton
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
        self.mGoToLocation.clicked.connect(self.onGoToLocationClicked)
        self.mRequestNominatim.clicked.connect(self.onRequestNominatimClicked)

    def enmapBoxInterface(self) -> EnMAPBox:
        return self.interface

    def qgisInterface(self):
        return self.interface

    def setInterface(self, interface):
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
            parent = self.qgisInterface().mapCanvas()
        else:
            raise ValueError()

        self.mResult = LocationBrowserResultWidget(parent=parent)
        self.mResult.mList.currentItemChanged.connect(self.onResultSelectionChanged)
        self.mResult.mZoomToSelection.clicked.connect(self.onZoomToSelectionClicked)

    def onExtentClicked(self):
        pass

    def onResultSelectionChanged(self):
        self.liveUpdate()

    def onCurrentLocationChanged(self):
        pass

    def onTextEditingFinished(self):
        self.mGoToLocation.animateClick(100)

    def onGoToLocationClicked(self):
        text = self.mSearch.value()

        point = None
        extent = None

        try:
            point = Utils.parseSpatialPoint(text)
            extent = None
        except Exception:
            pass

        if point is None:
            try:
                extent = Utils.parseSpatialExtent(text)
                point = extent.spatialCenter()
                if extent.isEmpty():
                    extent = None
            except Exception:
                pass

        if point is None:
            return

        if self.interfaceType == self.EnmapBoxInterface:
            mapCanvas = self.enmapBoxInterface().currentMapCanvas()
            mapCanvas.setCrosshairPosition(point, True)
        elif self.interfaceType == self.QgisInterface:
            mapCanvas = self.qgisInterface().mapCanvas()
            self.currentLocationMapTool.setCurrentLocation(point)
        else:
            raise ValueError()

        if extent is None:
            mapCanvas.setCenter(point.toCrs(Utils.mapCanvasCrs(mapCanvas)))
        else:
            mapCanvas.setExtent(extent)

        mapCanvas.refresh()

    def onRequestNominatimClicked(self):
        text = self.mSearch.value()

        # for details see https://nominatim.org/release-docs/latest/api/Search/
        url = 'https://nominatim.openstreetmap.org/search/' \
              f'{urllib.parse.quote(text)}' \
              '?limit=50&extratags=1&polygon_geojson=1&format=json'

        nominatimResults = requests.get(url).json()
        self.mResult.mList.clear()
        item = QListWidgetItem('')
        item.json = None
        self.mResult.mList.addItem(item)
        for result in nominatimResults:
            item = QListWidgetItem(result['display_name'])
            item.result = result
            self.mResult.mList.addItem(item)

        self.mResult.show()

    def onZoomToSelectionClicked(self):
        item = self.mResult.mList.currentItem()
        self.mResult.mDetails.clear()
        if not hasattr(item, 'result') or item.result is None:
            return
        self.mResult.mDetails.setText(json.dumps(item.result, indent=4))
        point = SpatialPoint(
            QgsCoordinateReferenceSystem.fromEpsgId(4326), float(item.result['lon']), float(item.result['lat'])
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
            mapCanvas = self.qgisInterface().mapCanvas()
            for aLayer in mapCanvas.layers():
                if aLayer.name() in [baseNamePolygon, baseNameLine]:
                    QgsProject.instance().removeMapLayer(aLayer)
        else:
            raise ValueError()

        type = item.result['geojson']['type']
        if type == 'MultiPolygon':
            layer = QgsVectorLayer('MultiPolygon?crs=epsg:4326', baseNamePolygon, 'memory')
            coordinates = item.result['geojson']['coordinates']
            coordinates = [[QgsPointXY(x, y) for x, y in polygon] for polygon in coordinates[0]]
            geometry = QgsGeometry.fromMultiPolygonXY([coordinates])
        elif type == 'Polygon':
            layer = QgsVectorLayer('MultiPolygon?crs=epsg:4326', baseNamePolygon, 'memory')
            coordinates = item.result['geojson']['coordinates']
            coordinates = [[QgsPointXY(x, y) for x, y in polygon] for polygon in coordinates]
            geometry = QgsGeometry.fromMultiPolygonXY([coordinates])
        elif type == 'LineString':
            layer = QgsVectorLayer('Linestring?crs=epsg:4326', baseNameLine, 'memory')
            coordinates = item.result['geojson']['coordinates']
            coordinates = [QgsPointXY(x, y) for x, y in coordinates]
            geometry = QgsGeometry.fromPolylineXY(coordinates)
        else:
            layer = QgsVectorLayer('MultiPolygon?crs=epsg:4326', baseNamePolygon, 'memory')
            y1, y2, x1, x2 = [float(v) for v in item.result['boundingbox']]
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
            mapCanvas.setCrosshairPosition(point, True)
            self.enmapBoxInterface().setCurrentLocation(point, self.enmapBoxInterface().currentMapCanvas())
            if not (coordinates is None or type == 'Point'):
                self.enmapBoxInterface().currentMapDock().insertLayer(0, layer)
        elif self.interfaceType == self.QgisInterface:
            self.currentLocationMapTool.setCurrentLocation(point)
            if not (coordinates is None or type == 'Point'):
                QgsProject.instance().addMapLayer(layer)
        else:
            raise ValueError()

        crs = Utils.mapCanvasCrs(mapCanvas)
        if coordinates is None or type == 'Point':
            mapCanvas.setCenter(point.toCrs(crs))
        else:
            extent = SpatialExtent(layer.crs(), layer.extent()).toCrs(crs)
            mapCanvas.setExtent(extent)
            print(crs)
            print(extent)

        mapCanvas.refresh()

    def liveUpdate(self):
        if self.mResult.mLiveUpdate.isChecked():
            self.onZoomToSelectionClicked()
