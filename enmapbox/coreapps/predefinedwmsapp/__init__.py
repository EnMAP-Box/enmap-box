from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu
from qgis.core import QgsRasterLayer


def enmapboxApplicationFactory(enmapBox):
    return [PredefinedWmsApp(enmapBox)]


class PredefinedWmsApp(EnMAPBoxApplication):
    WMS = [
        ('Bing VirtualEarth',
         'type=xyz&url=http://ecn.t3.tiles.virtualearth.net/tiles/a%7Bq%7D.jpeg?g%3D1&zmax=19&zmin=1'),
        ('CartoDb Dark Matter',
         'referer=Map%20tiles%20by%20CartoDB,%20under%20CC%20BY%203.0.%20Data%20by%20OpenStreetMap,%20under%20ODbL.&type=xyz&url=http://basemaps.cartocdn.com/dark_all/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=20&zmin=0'),
        ('CartoDb Positron',
         'referer=Map%20tiles%20by%20CartoDB,%20under%20CC%20BY%203.0.%20Data%20by%20OpenStreetMap,%20under%20ODbL.&type=xyz&url=http://basemaps.cartocdn.com/light_all/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=20&zmin=0'),
        ('Esri Boundaries Places',
         'type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=20&zmin=0'),
        ('Esri Gray (dark)',
         'type=xyz&url=http://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=16&zmin=0'),
        ('Esri Gray (light)',
         'type=xyz&url=http://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=16&zmin=0'),
        ('Esri National Geographic',
         'type=xyz&url=http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=12&zmin=0'),
        ('Esri Ocean',
         'type=xyz&url=https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=10&zmin=0'),
        ('Esri Satellite',
         'type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=17&zmin=0'),
        ('Esri Standard',
         'type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=17&zmin=0'),
        ('Esri Terrain',
         'type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=13&zmin=0'),
        ('Esri Topo World',
         'type=xyz&url=http://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=20&zmin=0'),
        ('Google Maps',
         'type=xyz&url=https://mt1.google.com/vt/lyrs%3Dm%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'),
        ('Google Satellite',
         'type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'),
        ('Google Satellite Hybrid',
         'type=xyz&url=https://mt1.google.com/vt/lyrs%3Dy%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'),
        ('Google Terrain',
         'type=xyz&url=https://mt1.google.com/vt/lyrs%3Dt%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'),
        ('Google Terrain Hybrid',
         'type=xyz&url=https://mt1.google.com/vt/lyrs%3Dp%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'),
        ('Open Weather Map Clouds',
         'referer=Map%20tiles%20by%20OpenWeatherMap,%20under%20CC%20BY-SA%204.0&type=xyz&url=http://tile.openweathermap.org/map/clouds_new/%7Bz%7D/%7Bx%7D/%7By%7D.png?APPID%3Def3c5137f6c31db50c4c6f1ce4e7e9dd&zmax=19&zmin=0'),
        ('Open Weather Map Temperature',
         'referer=Map%20tiles%20by%20OpenWeatherMap,%20under%20CC%20BY-SA%204.0&type=xyz&url=http://tile.openweathermap.org/map/temp_new/%7Bz%7D/%7Bx%7D/%7By%7D.png?APPID%3D1c3e4ef8e25596946ee1f3846b53218a&zmax=19&zmin=0'),
        ('Open Weather Map Wind Speed',
         'referer=Map%20tiles%20by%20OpenWeatherMap,%20under%20CC%20BY-SA%204.0&type=xyz&url=http://tile.openweathermap.org/map/wind_new/%7Bz%7D/%7Bx%7D/%7By%7D.png?APPID%3Df9d0069aa69438d52276ae25c1ee9893&zmax=19&zmin=0'),
        ('OpenStreetMap',
         'type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0'),
        ('OpenStreetMap Standard',
         'referer=OpenStreetMap%20contributors,%20CC-BY-SA&type=xyz&url=http://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0'),
        ('OpenTopoMap',
         'referer=Kartendaten:%20%C2%A9%20OpenStreetMap-Mitwirkende,%20SRTM%20%7C%20Kartendarstellung:%20%C2%A9%20OpenTopoMap%20(CC-BY-SA)&type=xyz&url=https://tile.opentopomap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=17&zmin=1'),
        ('Stamen Terrain',
         'referer=Map%20tiles%20by%20Stamen%20Design,%20under%20CC%20BY%203.0.%20Data%20by%20OpenStreetMap,%20under%20ODbL&type=xyz&url=http://tile.stamen.com/terrain/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=20&zmin=0'),
        ('Stamen Toner',
         'referer=Map%20tiles%20by%20Stamen%20Design,%20under%20CC%20BY%203.0.%20Data%20by%20OpenStreetMap,%20under%20ODbL&type=xyz&url=http://tile.stamen.com/toner/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=20&zmin=0'),
        ('Stamen Toner Light',
         'referer=Map%20tiles%20by%20Stamen%20Design,%20under%20CC%20BY%203.0.%20Data%20by%20OpenStreetMap,%20under%20ODbL&type=xyz&url=http://tile.stamen.com/toner-lite/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=20&zmin=0'),
        ('Stamen Watercolor',
         'referer=Map%20tiles%20by%20Stamen%20Design,%20under%20CC%20BY%203.0.%20Data%20by%20OpenStreetMap,%20under%20ODbL&type=xyz&url=http://tile.stamen.com/watercolor/%7Bz%7D/%7Bx%7D/%7By%7D.jpg&zmax=18&zmin=0'),
        ('Strava All',
         'referer=OpenStreetMap%20contributors,%20CC-BY-SA&type=xyz&url=https://heatmap-external-b.strava.com/tiles/all/bluered/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=15&zmin=0'),
        ('Strava Run',
         'referer=OpenStreetMap%20contributors,%20CC-BY-SA&type=xyz&url=https://heatmap-external-b.strava.com/tiles/run/bluered/%7Bz%7D/%7Bx%7D/%7By%7D.png?v%3D19&zmax=15&zmin=0'),
        ('Wikimedia Map',
         'referer=OpenStreetMap%20contributors,%20under%20ODbL&type=xyz&url=https://maps.wikimedia.org/osm-intl/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=20&zmin=1'),
    ]

    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = PredefinedWmsApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'
        self.wms: dict = dict()

    def menu(self, appMenu):
        appMenu = self.enmapbox.menu('Project')
        menu = QMenu('Add Web Map Service (WMS)')
        menu.setIcon(QIcon(':/images/themes/default/mActionAddWmsLayer.svg'))
        before = self.enmapbox.ui.mMenuCreateDataSource.menuAction()
        appMenu.insertMenu(before, menu)

        self.wms = dict()

        def addWms(name, uri):
            action = menu.addAction(name)
            action.triggered.connect(self.start)
            self.wms[action] = name, uri

        for (name, uri) in self.WMS:
            addWms(name, uri)

        return menu

    def start(self, *args):
        a = self.sender()
        name, uri = self.wms[a]
        layer = QgsRasterLayer(uri, name, 'wms')
        self.enmapbox.addMapLayer(layer)
