from qgis.core import QgsRasterDataProvider, Qgis, QgsCoordinateReferenceSystem, QgsProviderRegistry

from qgis.testing import start_app

providers = QgsProviderRegistry.instance().providerList()
print('Providers: {}'.format(', '.join(providers)))
start_app()
# def create(self, providerKey, uri, format, nBands, type, width, height, crs,
# createOptions, p_str=None, *args, **kwargs):  # real signature unknown; NOTE: unreliably restored from __doc__


crs = QgsCoordinateReferenceSystem('EPSG:4326')
assert crs.isValid()
createOptions = []
DP, v = QgsRasterDataProvider.create('gdal',
                                     'empty',
                                     'MEM',
                                     3,
                                     Qgis.DataType.Int16,
                                     20,
                                     50,
                                     crs,
                                     createOptions)

s = ""
