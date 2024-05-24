from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import QgsRasterLayer, QgsRasterPipe, QgsRasterFileWriter

layer = QgsRasterLayer(
    r'D:\data\sensors\planet\Valencia_NTIF_1B_psscene_basic_analytic_8b_udm2\PSScene\20240507_100329_00_24a8_1B_AnalyticMS_8b_file_format.ntf')
reader = RasterReader(layer)
provider = layer.dataProvider()
pipe = QgsRasterPipe()
pipe.set(provider.clone())
writer = QgsRasterFileWriter(r'C:\Users\Andreas\Downloads\copy.tif')
writer.writeRaster(pipe, reader.width(), reader.height(), reader.extent(), reader.crs())
