# -*- coding: utf-8 -*-
"""
Utils functions GEE
"""
import json

from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.utils import importEarthEngine
from qgis.gui import QgsMapCanvas
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.core import QgsPointXY, QgsRectangle
from qgis.core import QgsProject
from qgis.core import QgsRasterLayer

eeImported, ee = importEarthEngine(False)


def get_ee_image_url(image):
    map_id = ee.data.getMapId({'image': image})
    url = map_id['tile_fetcher'].url_format
    return url


def update_ee_layer_properties(layer, eeObject, visParams, shown, opacity):
    layer.setCustomProperty('ee-layer', True)

    if not (opacity is None):
        renderer = layer.renderer()
        if renderer:
            renderer.setOpacity(opacity)

    # serialize EE code
    ee_object = eeObject.serialize()
    ee_object_vis = json.dumps(visParams)
    layer.setCustomProperty('ee-plugin-version', '0.0')  # ee_plugin.ee_plugin.VERSION)
    layer.setCustomProperty('ee-object', ee_object)
    layer.setCustomProperty('ee-object-vis', ee_object_vis)

    # update EE script in provider
    if eeObject.getInfo()['type'] == 'Image':  # TODO
        layer.dataProvider().set_ee_object(eeObject)


def add_ee_image_layer(image, name, mapCanvas, shown, opacity):
    check_version()

    url = "type=xyz&url=" + get_ee_image_url(image)

    # EE raster data provider
    if image.ee_type == ee.Image:
        layer = QgsRasterLayer(url, name, "GEETSE_EE")
    else:
        raise ValueError()

    if isinstance(mapCanvas, MapCanvas):  # add to EnMAP-Box
        from enmapbox import EnMAPBox
        enmapBox = EnMAPBox.instance()
        mapDock = enmapBox.currentMapDock()
        mapDock.insertLayer(0, layer)
    elif isinstance(mapCanvas, QgsMapCanvas):  # add to QGIS
        QgsProject.instance().addMapLayer(layer)
    else:
        raise ValueError(str(mapCanvas))

    return layer


def update_ee_image_layer(image, layer, mapCanvas, shown=True, opacity=1.0):
    check_version()

    url = "type=xyz&url=" + get_ee_image_url(image)

    provider = layer.dataProvider()

    provider.setDataSourceUri(url)
    provider.reloadData()
    layer.triggerRepaint()
    layer.reload()
    mapCanvas.refresh()


def get_layer_by_name(name):
    layers = QgsProject.instance().mapLayers().values()

    for layer in layers:
        if layer.name() == name:
            return layer

    return None


def add_or_update_ee_layer(eeObject, visParams, name, mapCanvas, shown, opacity):
    if visParams is None:
        visParams = {}

    if isinstance(eeObject, ee.Image):
        image = eeObject.visualize(**visParams)

    image.ee_type = type(eeObject)

    layer = add_or_update_ee_image_layer(image, name, mapCanvas, shown, opacity)
    update_ee_layer_properties(layer, eeObject, visParams, shown, opacity)

    return layer


def add_or_update_ee_image_layer(image, name, mapCanvas, shown=True, opacity=1.0):
    layer = get_layer_by_name(name)

    if layer is not None:
        if not layer.customProperty('ee-layer'):
            raise Exception('Layer is not an EE layer: ' + name)

        update_ee_image_layer(image, layer, mapCanvas, shown, opacity)
    else:
        layer = add_ee_image_layer(image, name, mapCanvas, shown, opacity)

    return layer


def add_ee_catalog_image(name, asset_name, visParams, collection_props):
    image = None

    if collection_props:
        raise Exception('Not supported yet')
    else:
        image = ee.Image(asset_name).visualize(visParams)

    add_or_update_ee_image_layer(image, name)


def check_version():
    # check if we have the latest version only once plugin is used, not once it is loaded
    pass
    # qgis.utils.plugins['ee_plugin'].check_version()


def geom_to_geo(geom):
    crs_src = QgsCoordinateReferenceSystem(QgsProject.instance().crs())
    crs_dst = QgsCoordinateReferenceSystem('EPSG:4326')
    proj2geo = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())

    if isinstance(geom, QgsPointXY):
        return proj2geo.transform(geom)
    elif isinstance(geom, QgsRectangle):
        return proj2geo.transformBoundingBox(geom)
    else:
        return geom.transform(proj2geo)
