import pickle
import typing
import uuid
from os.path import basename
from typing import List

from enmapbox import debugLog
from qgis.PyQt.QtCore import QMimeData, QUrl, QByteArray
from qgis.PyQt.QtXml import QDomNamedNodeMap, QDomDocument
from qgis.core import QgsLayerItem
from qgis.core import QgsMapLayer, QgsRasterLayer, QgsProject, QgsReadWriteContext, \
    QgsMimeDataUtils, QgsLayerTree
from .datasources.datasources import DataSource
from ..qgispluginsupport.qps.layerproperties import defaultRasterRenderer
from ..qgispluginsupport.qps.speclib.core import is_spectral_library
from ..qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibrary

MDF_RASTERBANDS = 'application/enmapbox.rasterbanddata'

MDF_DATASOURCETREEMODELDATA = 'application/enmapbox.datasourcetreemodeldata'
MDF_DATASOURCETREEMODELDATA_XML = 'data_source_tree_model_data'

MDF_ENMAPBOX_LAYERTREEMODELDATA = 'application/enmapbox.layertreemodeldata'
MDF_QGIS_LAYERTREEMODELDATA = 'application/qgis.layertreemodeldata'
MDF_QGIS_LAYERTREEMODELDATA_XML = 'layer_tree_model_data'

MDF_PYTHON_OBJECTS = 'application/enmapbox/objectreference'
MDF_SPECTRALLIBRARY = 'application/hub-spectrallibrary'

MDF_URILIST = 'text/uri-list'
MDF_TEXT_HTML = 'text/html'
MDF_TEXT_PLAIN = 'text/plain'

MDF_QGIS_LAYER_STYLE = 'application/qgis.style'
QGIS_URILIST_MIMETYPE = "application/x-vnd.qgis.qgis.uri"


def attributesd2dict(attributes: QDomNamedNodeMap) -> str:
    d = {}
    assert isinstance(attributes, QDomNamedNodeMap)
    for i in range(attributes.count()):
        attribute = attributes.item(i)
        d[attribute.nodeName()] = attribute.nodeValue()
    return d


def fromDataSourceList(dataSources):
    if not isinstance(dataSources, list):
        dataSources = [dataSources]

    from enmapbox.gui.datasources.datasources import DataSource

    uriList = []
    urlList = []
    for ds in dataSources:

        assert isinstance(ds, DataSource)

        dataItem = ds.dataItem()
        uris = dataItem.mimeUris()
        if not isinstance(dataItem, QgsLayerItem):
            uri = QgsMimeDataUtils.Uri()
            uri.name = dataItem.name()
            uri.filePath = dataItem.path()
            uri.uri = dataItem.path()
            uri.providerKey = dataItem.providerKey()
            uris = [uri]
        uriList.extend(uris)

    urlList = [QUrl.fromLocalFile(u.uri) for u in uriList]

    mimeData: QMimeData = QgsMimeDataUtils.encodeUriList(uriList)
    mimeData.setUrls(urlList)
    return mimeData


def toDataSourceList(mimeData) -> typing.List[DataSource]:
    assert isinstance(mimeData, QMimeData)

    uriList = QgsMimeDataUtils.decodeUriList(mimeData)
    dataSources = []
    from enmapbox.gui.datasources.manager import DataSourceFactory
    for uri in uriList:
        dataSources.extend(DataSourceFactory.create(uri))
    return dataSources


def fromLayerList(mapLayers):
    """
    Converts a list of QgsMapLayers into a QMimeData object
    :param mapLayers: [list-of-QgsMapLayers]
    :return: QMimeData
    """
    for lyr in mapLayers:
        assert isinstance(lyr, QgsMapLayer)

    tree = QgsLayerTree()
    mimeData = QMimeData()

    urls = []
    for lyr in mapLayers:
        tree.addLayer(lyr)
        urls.append(QUrl.fromLocalFile(lyr.source()))
    doc = QDomDocument()
    context = QgsReadWriteContext()
    node = doc.createElement(MDF_QGIS_LAYERTREEMODELDATA_XML)
    doc.appendChild(node)
    for c in tree.children():
        c.writeXml(node, context)

    mimeData.setData(MDF_QGIS_LAYERTREEMODELDATA, doc.toByteArray())

    return mimeData


def containsMapLayers(mimeData: QMimeData) -> bool:
    """
    Checks if the mimeData contains any format suitable to describe QgsMapLayers
    :param mimeData:
    :return:
    """
    valid = [MDF_RASTERBANDS, MDF_DATASOURCETREEMODELDATA, MDF_QGIS_LAYERTREEMODELDATA, QGIS_URILIST_MIMETYPE,
             MDF_URILIST]

    for f in valid:
        if f in mimeData.formats():
            return True
    return False


def extractMapLayers(mimeData: QMimeData,
                     project: QgsProject = QgsProject.instance()) -> List[QgsMapLayer]:
    """
    Extracts QgsMapLayers from QMimeData
    :param mimeData:
    :param project:
    :return: A list if QgsMapLayers
    """
    assert isinstance(mimeData, QMimeData)

    from enmapbox.gui.datasources.datasources import DataSource
    from enmapbox.gui.datasources.datasources import SpatialDataSource
    from enmapbox.gui.datasources.manager import DataSourceFactory

    newMapLayers = []

    QGIS_LAYERTREE_FORMAT = None
    if MDF_ENMAPBOX_LAYERTREEMODELDATA in mimeData.formats():
        QGIS_LAYERTREE_FORMAT = MDF_ENMAPBOX_LAYERTREEMODELDATA
    elif MDF_QGIS_LAYERTREEMODELDATA in mimeData.formats():
        QGIS_LAYERTREE_FORMAT = MDF_QGIS_LAYERTREEMODELDATA

    if QGIS_LAYERTREE_FORMAT in mimeData.formats():
        doc = QDomDocument()
        doc.setContent(mimeData.data(QGIS_LAYERTREE_FORMAT))
        node = doc.firstChildElement(MDF_QGIS_LAYERTREEMODELDATA_XML)
        context = QgsReadWriteContext()
        # context.setPathResolver(QgsProject.instance().pathResolver())
        layerTree = QgsLayerTree.readXml(node, context)

        for layerId in layerTree.findLayerIds():
            lyr = project.mapLayer(layerId)
            if isinstance(lyr, QgsMapLayer):
                newMapLayers.append(lyr)
                break

    elif MDF_RASTERBANDS in mimeData.formats():
        data = pickle.loads(mimeData.data(MDF_RASTERBANDS))

        for t in data:
            uri, baseName, providerKey, band = t
            lyr = QgsRasterLayer(uri, baseName=baseName, providerType=providerKey)
            lyr.setRenderer(defaultRasterRenderer(lyr, bandIndices=[band]))
            newMapLayers.append(lyr)

    elif MDF_DATASOURCETREEMODELDATA in mimeData.formats():
        # this drop comes from the datasource tree
        dsUUIDs = pickle.loads(mimeData.data(MDF_DATASOURCETREEMODELDATA))

        for uuid4 in dsUUIDs:
            assert isinstance(uuid4, uuid.UUID)
            dataSource = DataSource.fromUUID(uuid4)

            if isinstance(dataSource, SpatialDataSource):
                lyr = dataSource.asMapLayer()
                if isinstance(lyr, QgsMapLayer):
                    if isinstance(lyr, QgsRasterLayer):
                        lyr.setRenderer(defaultRasterRenderer(lyr))
                    newMapLayers.append(lyr)

    elif MDF_ENMAPBOX_LAYERTREEMODELDATA in mimeData.formats():
        # this drop comes from the dock tree

        s = ""

    elif QGIS_URILIST_MIMETYPE in mimeData.formats():
        for uri in QgsMimeDataUtils.decodeUriList(mimeData):

            dataSources = DataSourceFactory.create(uri, project=project)
            for dataSource in dataSources:
                if isinstance(dataSource, SpatialDataSource):
                    lyr = dataSource.asMapLayer(project=project)
                    if isinstance(lyr, QgsMapLayer):
                        if isinstance(lyr, QgsRasterLayer):
                            lyr.setRenderer(defaultRasterRenderer(lyr))
                        newMapLayers.append(lyr)

    elif MDF_URILIST in mimeData.formats():
        for url in mimeData.urls():

            if basename(url.url()) == 'MTD_MSIL2A.xml':  # resolves #42
                dataSources = [None]
            elif basename(url.url()).startswith('PRS_L') and  basename(url.url()).endswith('.he5'):  # resolves #100
                dataSources = [None]
            else:
                dataSources = DataSourceFactory.create(url)

            for dataSource in dataSources:
                if isinstance(dataSource, SpatialDataSource):
                    lyr = dataSource.asMapLayer()
                    if isinstance(lyr, QgsMapLayer):
                        if isinstance(lyr, QgsRasterLayer):
                            lyr.setRenderer(defaultRasterRenderer(lyr))
                        newMapLayers.append(lyr)
                else:
                    # check if URL is associated with an external product,
                    # if so, the product is created by running the appropriate processing algorithm
                    from enmapboxprocessing.algorithm.importproductsdraganddropsupport import tryToImportSensorProducts
                    filename = url.toLocalFile()
                    mapLayers = tryToImportSensorProducts(filename)
                    newMapLayers.extend(mapLayers)

    else:
        s = ""

    info = ['Extract map layers from QMimeData']
    info.append('Formats:' + ','.join(mimeData.formats()))
    info.append(f' {len(newMapLayers)} Map Layers: ' + '\n\t'.join([f'{lyr}' for lyr in newMapLayers]))
    debugLog('\n'.join(info))

    return newMapLayers


def extractSpectralLibraries(mimeData: QMimeData) -> list:
    """Reads spectral libraries that may be defined in mimeData"""
    results = []
    slib = SpectralLibrary.readFromMimeData(mimeData)
    if is_spectral_library(slib):
        results.append(slib)

    return results


def textToByteArray(text):
    """
    Converts input into a QByteArray
    :param text: bytes or str
    :return: QByteArray
    """

    if isinstance(text, QDomDocument):
        return textToByteArray(text.toString())
    else:
        data = QByteArray()
        data.append(text)
        return data


def textFromByteArray(data):
    """
    Decodes a QByteArray into a str
    :param data: QByteArray
    :return: str
    """
    assert isinstance(data, QByteArray)
    s = data.data().decode()
    return s
