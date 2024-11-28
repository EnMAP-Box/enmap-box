import os
import warnings
from os import makedirs
from os.path import splitext, exists, dirname
from typing import List

from osgeo import gdal

from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.typing import Array3d, CreationOptions
from enmapboxprocessing.utils import Utils
from qgis.core import QgsRectangle, QgsCoordinateReferenceSystem, QgsProcessingFeedback, Qgis
from enmapbox.typeguard import typechecked


@typechecked
class Driver(object):
    VrtFormat = 'VRT'
    DefaultVrtCreationOptions = ''.split()
    GTiffFormat = 'GTiff'
    DefaultGTiffCreationOptions = 'INTERLEAVE=BAND COMPRESS=LZW TILED=YES BIGTIFF=YES'.split()
    EnviFormat = 'ENVI'
    MemFormat = 'MEM'
    DefaultEnviBsqCreationOptions = 'INTERLEAVE=BSQ'.split()
    DefaultEnviBilCreationOptions = 'INTERLEAVE=BIL'.split()
    DefaultEnviBipCreationOptions = 'INTERLEAVE=BIP'.split()

    def __init__(
            self, filename: str, format: str = None, options: CreationOptions = None,
            feedback: QgsProcessingFeedback = None
    ):
        assert filename is not None
        if format is None:
            format = self.defaultFormat(filename)
        if options is None:
            extension = splitext(filename)[1].lower()
            options = self.defaultCreationOptions(format, extension)
        self.filename = filename
        self.format = format
        self.options = options
        self.feedback = feedback

    def create(
            self, dataType: Qgis.DataType, width: int, height: int, nBands: int, extent: QgsRectangle = None,
            crs: QgsCoordinateReferenceSystem = None
    ) -> RasterWriter:

        gdalDataType = Utils.qgisDataTypeToGdalDataType(dataType)
        if extent is not None:
            xResolution = extent.width() / width
            yResolution = extent.height() / height
            gdalGeoTransform = extent.xMinimum(), xResolution, -0., extent.yMaximum(), -0., -yResolution

        info = f'Create Raster [{width}x{height}x{nBands}]({Utils.qgisDataTypeName(dataType)})' \
               f' -co {" ".join(self.options)}' \
               f' {self.filename}'
        if self.feedback is not None:
            self.feedback.pushInfo(info)

        if self.format != self.MemFormat:
            if not exists(dirname(self.filename)):
                makedirs(dirname(self.filename))

            if exists(self.filename + 'stac.json'):
                try:
                    os.remove(self.filename + 'stac.json')
                except Exception:
                    pass

        gdalDriver: gdal.Driver = gdal.GetDriverByName(self.format)
        try:
            gdalDataset: gdal.Dataset = gdalDriver.Create(self.filename, width, height, nBands, gdalDataType,
                                                          self.options)
        except RuntimeError as error:
            warnings.warn(f'Unable to create file: {self.filename}')
            raise error

        assert gdalDataset is not None
        if crs is not None:
            gdalDataset.SetProjection(crs.toWkt())
        if extent is not None:
            gdalDataset.SetGeoTransform(gdalGeoTransform)

        # remove default color interpretation (issue #544)
        for bandNo in range(1, gdalDataset.RasterCount + 1):
            rb: gdal.Band = gdalDataset.GetRasterBand(bandNo)
            rb.SetColorInterpretation((gdal.GCI_Undefined))

        return RasterWriter(gdalDataset)

    def createFromArray(
            self, array: Array3d, extent: QgsRectangle = None, crs: QgsCoordinateReferenceSystem = None,
            overlap: int = None
    ) -> RasterWriter:
        nBands = len(array)
        height, width = array[0].shape
        if overlap is not None:
            height -= 2 * overlap
            width -= 2 * overlap
        dataType = Utils.numpyDataTypeToQgisDataType(array[0].dtype)
        raster = self.create(dataType=dataType, width=width, height=height, nBands=nBands, extent=extent, crs=crs)
        raster.writeArray(array, overlap=overlap)
        return raster

    def createLike(
            self, raster: RasterReader, dataType: Qgis.DataType = None, nBands: int = None
    ) -> RasterWriter:

        provider = raster.provider
        if nBands is None:
            nBands = provider.bandCount()
        if dataType is None:
            dataType = raster.provider.dataType(bandNo=1)
        raster2 = self.create(dataType, provider.xSize(), provider.ySize(), nBands, provider.extent(), provider.crs())
        return raster2

    @classmethod
    def defaultFormat(cls, filename: str) -> str:
        extension = splitext(filename)[1]
        format = cls.formatFromExtension(extention=extension)
        return format

    @staticmethod
    def formatFromExtension(extention: str) -> str:
        extention = extention.lower()
        if extention in ['.tif', '.tiff']:
            format = 'GTiff'
        elif extention == '.vrt':
            format = 'VRT'
        else:
            format = 'ENVI'
        return format

    @classmethod
    def defaultCreationOptions(cls, format: str, extension: str) -> List[str]:
        if format == cls.EnviFormat:
            if extension == '.bil':
                options = cls.DefaultEnviBilCreationOptions
            elif extension == '.bip':
                options = cls.DefaultEnviBipCreationOptions
            else:
                options = cls.DefaultEnviBsqCreationOptions
        elif format == cls.GTiffFormat:
            options = cls.DefaultGTiffCreationOptions
        elif format == cls.VrtFormat:
            options = cls.DefaultVrtCreationOptions
        else:
            options = []
        return options
