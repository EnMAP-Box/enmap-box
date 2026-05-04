import json
import urllib.parse
from os.path import join, dirname
from typing import Optional

import requests
from PyQt5.QtWidgets import QDateEdit, QSpinBox

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint, SpatialExtent
from enmapbox.typeguard import typechecked
from enmapboxprocessing.utils import Utils
from geetimeseriesexplorerapp import MapTool
from locationbrowserapp.locationbrowserresultwidget import LocationBrowserResultWidget
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QListWidgetItem, QToolButton
from qgis.core import QgsCoordinateReferenceSystem, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject
from qgis.gui import QgsFilterLineEdit, QgsDockWidget, QgisInterface


@typechecked
class EnmapQuicklooksDockWidget(QgsDockWidget):
    mStartDate: QDateEdit
    mEndDate: QDateEdit
    mLimit: QSpinBox
    mApply: QToolButton
    EnmapBoxInterface, QgisInterface = 0, 1

    def __init__(self, currentLocationMapTool: Optional[MapTool], parent=None):
        QgsDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        self.currentLocationMapTool = currentLocationMapTool

        # set from outside
        self.interface = None
        self.interfaceType = None

        # connect signals
        self.mApply.clicked.connect(self.onApplyClicked)

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

    def onApplyClicked(self):

        if self.interface is None:  # not yet initialized
            return

        if not self.isUserVisible():
            return

        import requests
        from qgis.core import QgsRasterLayer, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform, \
            QgsLayerTreeGroup
        from qgis.utils import iface

        # Get current canvas extent
        if self.interfaceType == self.EnmapBoxInterface:
            mapDock = self.enmapBoxInterface().currentMapDock()
            mapCanvas = self.enmapBoxInterface().currentMapCanvas()
        elif self.interfaceType == self.QgisInterface:
            mapCanvas = self.qgisInterface().mapCanvas()
        else:
            raise NotImplementedError()

        if mapCanvas is None:
            return

        extent = mapCanvas.extent()

        # Convert the QGIS extent to WGS84 (EPSG:4326) using the coordinate transformation
        source_crs = mapCanvas.mapSettings().destinationCrs()  # Current CRS of the map canvas
        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS84

        # Set up the coordinate transform
        transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())

        # Transform the bounding box corners
        min_lon, min_lat = transform.transform(extent.xMinimum(), extent.yMinimum())
        max_lon, max_lat = transform.transform(extent.xMaximum(), extent.yMaximum())

        # Updated bbox in lon/lat
        bbox = [min_lon, min_lat, max_lon, max_lat]

        print(f"Using map extent as bbox (WGS84): {bbox}")

        # STAC API endpoint
        search_url = "https://geoservice.dlr.de/eoc/ogc/stac/v1/search"

        # Define the date range (from Dec 1, 2024 to Apr 15, 2025)
        datetime_range = "2025-03-29/2025-03-29"

        # Build the STAC search payload
        payload = {
            "collections": ["ENMAP_HSI_L0_QL"],
            "limit": 200,
            "bbox": bbox,
            "datetime": datetime_range  # Filter by date
        }

        # Print the request URL and payload for debugging
        print(f"Request URL: {search_url}")
        print(f"Request Payload: {payload}")

        headers = {
            "Content-Type": "application/json"
        }

        # Make the API call
        response = requests.post(search_url, json=payload, headers=headers, verify=False)

        # Check response status and process data
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response: {response_data}")  # Print full response for debugging

            features = response_data.get("features", [])
            print(f"Found {len(features)} items.")

            # Create a new group in the QGIS layer panel for this date range
            #group_name = f"{datetime_range.replace('/', '_')}"
            #root = QgsProject.instance().layerTreeRoot()

            # Instead of addGroup, we create and insert the group at the top
            #date_range_group = QgsLayerTreeGroup(group_name)  # Create the group
            #root.insertChildNode(0, date_range_group)  # Insert at the top of the root
            #print(f"Created and added group at the top: {group_name}")

            for feature in features:
                assets = feature.get("assets", {})
                print(f"Assets for {feature.get('id')}: {assets}")  # Print assets for debugging

                vnir = assets.get("VNIR")

                if vnir:
                    url = vnir.get("href")
                    scene_id = feature.get("id", "ENMAP_VNIR")
                    layer = QgsRasterLayer(f"/vsicurl/{url}", scene_id)

                    if layer.isValid():
                        # Add the layer to the new group
                        #QgsProject.instance().addMapLayer(layer,False)  # False ensures it's not added to the root group
                        #date_range_group.addLayer(layer)  # Add to the new date range group

                        if self.interfaceType == self.EnmapBoxInterface:
                            #self.enmapBoxInterface().onDataDropped([layer])
                            mapDock.insertLayer(0,layer)


                        print(f"Loaded: {scene_id}")
                    else:
                        print(f"Failed to load: {scene_id}")
                else:
                    print(f"No VNIR asset for {feature.get('id')}")
        else:
            print(f"STAC API request failed with status {response.status_code}")
            print(f"Response content: {response.content}")  # Print response error details
