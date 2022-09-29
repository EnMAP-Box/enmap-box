from typing import List, Union, Optional, Iterator

from osgeo import gdal

from enmapboxprocessing.typing import Array3d, Array2d, MetadataValue, MetadataDomain, Metadata, Number
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtCore import QDateTime
from qgis.PyQt.QtGui import QColor
from qgis.core import Qgis
from typeguard import typechecked


@typechecked
class RasterWriter(object):

    def __init__(self, gdalDataset: gdal.Dataset):
        self.gdalDataset = gdalDataset
        self._source: str = self.gdalDataset.GetDescription()

    def writeArray(self, array: Array3d, xOffset=0, yOffset=0, bandList: List[int] = None, overlap: int = None):
        if bandList is None:
            assert len(array) == self.bandCount()
            bandList = range(1, self.bandCount() + 1)
        for bandNo, array2d in zip(bandList, array):
            self.writeArray2d(array2d, bandNo, xOffset, yOffset, overlap)

    def writeArray2d(self, array: Array2d, bandNo: int, xOffset=0, yOffset=0, overlap: int = None):
        if overlap is not None:
            height, width = array.shape
            array = array[overlap:height - overlap, overlap:width - overlap]
        self.gdalBand(bandNo).WriteArray(array, xOffset, yOffset)

    def fill(self, value: float, bandNo: int):
        self.gdalBand(bandNo).Fill(value)

    def setNoDataValue(self, noDataValue: Optional[float], bandNo: int = None):
        if noDataValue is None:
            return
        if bandNo is None:
            for bandNo in range(1, self.bandCount() + 1):
                self.gdalBand(bandNo).SetNoDataValue(noDataValue)
        else:
            self.gdalBand(bandNo).SetNoDataValue(noDataValue)

    def deleteNoDataValue(self, bandNo: int):
        self.gdalBand(bandNo).DeleteNoDataValue()

    def setOffset(self, offset: Optional[float], bandNo: int):
        if offset is None:
            return
        self.gdalBand(bandNo).SetOffset(offset)

    def setScale(self, scale: Optional[float], bandNo: int):
        if scale is None:
            return
        self.gdalBand(bandNo).SetScale(scale)

    def setMetadataItem(self, key: str, value: MetadataValue, domain: str = '', bandNo: int = None):
        if value is None:
            return
        if bandNo is not None:
            if key in ['offset', 'scale']:
                return  # skip user offset and scale; will be set via gdal.Band.SetOffset/SetScale
        self._gdalObject(bandNo).SetMetadataItem(key, Utils.metadateValueToString(value), domain)

    def setMetadataDomain(self, metadata: MetadataDomain, domain: str = '', bandNo: int = None):
        self._gdalObject(bandNo).SetMetadata({}, domain)  # clear existing domain first

        deleteDomain = len(metadata) == 0
        if deleteDomain:
            self._gdalObject(bandNo).SetMetadata({}, domain)
        else:
            for key, value in metadata.items():
                if key.replace(' ', '_') == 'file_compression':
                    continue
                self.setMetadataItem(key, value, domain, bandNo)

    def setMetadata(self, metadata: Metadata, bandNo: int = None):
        for domain, metadata_ in metadata.items():
            self.setMetadataDomain(metadata_, domain, bandNo)

    def setBandName(self, bandName: Optional[str], bandNo: int):
        if bandName is not None:
            self.gdalBand(bandNo).SetDescription(bandName)

    def setBandColor(self, color: Optional[QColor], bandNo: int):
        if color is not None:
            self.setMetadataItem('color', color.name(), '', bandNo)

    def setCategoryNames(self, names: List[str] = None, bandNo: int = None):
        if bandNo is None:
            bandNo = 1
        gdalBand = self.gdalBand(bandNo)
        gdalBand.SetCategoryNames(names)

    def setCategoryColors(self, colors: List[QColor] = None, bandNo: int = None):
        if bandNo is None:
            bandNo = 1
        gdalBand = self.gdalBand(bandNo)

        colorTable = gdal.ColorTable()
        for i, color in enumerate(colors):
            colorTable.SetColorEntry(i, (color.red(), color.green(), color.blue()))
        gdalBand.SetColorTable(colorTable)

    def setWavelength(self, wavelength: Optional[Number], bandNo: int, units: str = None):
        if wavelength is None:
            return
        if units is None:
            units = 'Nanometers'
        self.setMetadataItem('wavelength', round(wavelength, 5), '', bandNo)
        self.setMetadataItem('wavelength_units', units, '', bandNo)

    def setFwhm(self, fwhm: Optional[Number], bandNo: int, units: str = None):
        if fwhm is None:
            return
        if units is None:
            units = 'Nanometers'
        self.setMetadataItem('fwhm', round(fwhm, 5), '', bandNo)
        self.setMetadataItem('wavelength_units', units, '', bandNo)

    def setBadBandMultiplier(self, badBandMultiplier: Optional[int], bandNo: int):
        if badBandMultiplier is None:
            return
        self.setMetadataItem('bbl', badBandMultiplier, '', bandNo)

    def setStartTime(self, startTime: Optional[QDateTime], bandNo: int = None):
        if startTime is None:
            return
        if startTime.isValid():
            self.setMetadataItem('start_time', startTime.toString('yyyy-MM-ddTHH:mm:ss'), '', bandNo)
        else:
            self.setMetadataItem('start_time', 'None', '', bandNo)

    def setEndTime(self, endTime: Optional[QDateTime], bandNo: int = None):
        if endTime is None:
            return
        self.setMetadataItem('end_time', endTime.toString('yyyy-MM-ddTHH:mm:ss'), '', bandNo)

    def bandCount(self) -> int:
        return self.gdalDataset.RasterCount

    def bandNumbers(self) -> Iterator[int]:
        """Return iterator over all band numbers."""
        for bandNo in range(1, self.bandCount() + 1):
            yield bandNo

    def source(self) -> str:
        return self._source

    def dataType(self, bandNo: int = None) -> Qgis.DataType:
        if bandNo is None:
            bandNo = 1
        gdalDataType = self.gdalDataset.GetRasterBand(bandNo).DataType
        return Utils.gdalDataTypeToQgisDataType(gdalDataType)

    def dataTypeSize(self, bandNo: int = None) -> int:
        if bandNo is None:
            bandNo = 1
        qgisDataType = self.dataType(bandNo)
        dtype = Utils.qgisDataTypeToNumpyDataType(qgisDataType)
        return dtype().itemsize

    def width(self) -> int:
        return self.gdalDataset.RasterXSize

    def height(self) -> int:
        return self.gdalDataset.RasterYSize

    def _gdalObject(self, bandNo: int = None) -> Union[gdal.Dataset, gdal.Band]:
        if bandNo is None:
            return self.gdalDataset
        else:
            gdalBand: gdal.Band = self.gdalDataset.GetRasterBand(bandNo)
            assert gdalBand is not None
            return gdalBand

    def gdalBand(self, bandNo: int = None) -> gdal.Band:
        return self._gdalObject(bandNo)

    def close(self):
        self.gdalDataset.FlushCache()
        self.gdalDataset = None
