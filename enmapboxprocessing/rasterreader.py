from math import isnan, ceil
from os.path import exists
from typing import Iterable, List, Union, Optional, Tuple, Iterator

import numpy as np
from osgeo import gdal

import processing
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapbox.typeguard import typechecked
from enmapboxprocessing.gridwalker import GridWalker
from enmapboxprocessing.numpyutils import NumpyUtils
from enmapboxprocessing.rasterblockinfo import RasterBlockInfo
from enmapboxprocessing.typing import RasterSource, Array3d, Metadata, MetadataValue, MetadataDomain, Array2d
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtCore import QSizeF, QDateTime, QDate, QPoint
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsRasterLayer, QgsRasterDataProvider, QgsCoordinateReferenceSystem, QgsRectangle,
                       QgsRasterRange, QgsPoint, QgsRasterBlockFeedback, QgsRasterBlock, QgsPointXY,
                       QgsProcessingFeedback, QgsRasterBandStats, Qgis, QgsGeometry, QgsVectorLayer, QgsWkbTypes,
                       QgsFeature, QgsRasterPipe, QgsRasterProjector)


@typechecked
class RasterReader(object):
    Nanometers = 'Nanometers'
    Micrometers = 'Micrometers'

    def __init__(
            self, source: RasterSource, openWithGdal: bool = True,
            crs: QgsCoordinateReferenceSystem = None
    ):
        self.maskReader: Optional[RasterReader] = None
        if isinstance(source, QgsRasterLayer):
            self.layer = source
            self.provider: QgsRasterDataProvider = self.layer.dataProvider()
        elif isinstance(source, QgsRasterDataProvider):
            self.layer = QgsRasterLayer()  # invalid layer!; all QGIS PAM items will get lost
            self.provider = source
        elif isinstance(source, str):
            self.layer = QgsRasterLayer(source)
            self.provider: QgsRasterDataProvider = self.layer.dataProvider()
        elif isinstance(source, gdal.Dataset):
            self.layer = QgsRasterLayer(source.GetDescription())
            self.provider: QgsRasterDataProvider = self.layer.dataProvider()
        else:
            raise ValueError()

        if isinstance(source, gdal.Dataset):
            gdalDataset = source
        else:
            if openWithGdal:
                gdalDataset: gdal.Dataset = gdal.Open(self.provider.dataSourceUri(), gdal.GA_ReadOnly)
            else:
                gdalDataset = None

        self.gdalDataset = gdalDataset

        self.setRasterPipeCrs(crs)

        # prepare STAC metadata
        if exists(self.layer.source() + '.stac.json'):
            self.stacMetadata = Utils().jsonLoad(self.layer.source() + '.stac.json')
        else:
            self.stacMetadata = {}
        if 'properties' not in self.stacMetadata:
            self.stacMetadata['properties'] = {}
        if 'eo:bands' not in self.stacMetadata['properties']:
            self.stacMetadata['properties']['eo:bands'] = [{} for i in self.bandNumbers()]
        if 'envi:metadata' not in self.stacMetadata['properties']:
            self.stacMetadata['properties']['envi:metadata'] = {}

        # prepare R terra (https://github.com/rspatial/terra) metadata, also see #907
        if exists(self.layer.source() + '.aux.json'):
            self.terraMetadata = Utils().jsonLoad(self.layer.source() + '.aux.json')
        else:
            self.terraMetadata = None

    def setExternalMask(self, layer: QgsRasterLayer):
        self.maskReader = RasterReader(layer)

    def bandCount(self) -> int:
        """Return iterator over all band numbers."""
        return self.provider.bandCount()

    def bandNumbers(self) -> Iterator[int]:
        """Return iterator over all band numbers."""
        for bandNo in range(1, self.provider.bandCount() + 1):
            yield bandNo

    def checksum(self, bandNo: int = None, xoff=0, yoff=0, xsize: int = None, ysize: int = None) -> int:
        """Return band checksum."""
        if bandNo is None:
            checksum = 0
            for bandNo in self.bandNumbers():
                checksum += self.checksum(bandNo, xoff, yoff, xsize, ysize)
        else:
            checksum = self.gdalBand(bandNo).Checksum(xoff, yoff, xsize, ysize)
        return checksum

    def bandName(self, bandNo: int) -> str:
        """Return band name."""

        # check STAC
        bandName = self.stacMetadata['properties']['eo:bands'][bandNo - 1].get('name')
        if bandName is not None:
            return bandName

        bandName = self.stacMetadata['properties']['envi:metadata'].get('band_names')
        if bandName is not None:
            return bandName[bandNo - 1]

        # check QGIS
        return ': '.join(self.layer.bandName(bandNo).split(': ')[1:])  # removes the "Band 042: " prefix

    def bandColor(self, bandNo: int) -> Optional[QColor]:
        """Return band color."""
        return Utils.parseColor(self.metadataItem('color', '', bandNo))

    def bandOffset(self, bandNo: int) -> float:
        """Return band offset."""
        return self.provider.bandOffset(bandNo)

    def bandScale(self, bandNo: int) -> float:
        """Return band scale."""
        return self.provider.bandScale(bandNo)

    def crs(self) -> QgsCoordinateReferenceSystem:
        """Return CRS."""
        return self.provider.crs()

    def dataType(self, bandNo: int = None) -> Qgis.DataType:
        """Return band data type."""
        if bandNo is None:
            bandNo = 1
        return self.provider.dataType(bandNo)

    def dataTypeSize(self, bandNo: int = None) -> int:
        """Return band data type size in bytes."""
        if bandNo is None:
            bandNo = 1
        return self.provider.dataTypeSize(bandNo)

    def extent(self) -> QgsRectangle:
        """Return extent."""
        return self.provider.extent()

    def noDataValue(self, bandNo: int = None) -> Optional[float]:
        """Return no data value."""
        if bandNo is None:
            bandNo = 1

        if not self.sourceHasNoDataValue(bandNo):
            return None

        return self.sourceNoDataValue(bandNo)

    def sourceNoDataValue(self, bandNo: int):
        """Return no data value."""
        return self.provider.sourceNoDataValue(bandNo)

    def sourceHasNoDataValue(self, bandNo: int = None):
        """Read QGIS docs."""
        if bandNo is None:
            bandNo = 1
        return self.provider.sourceHasNoDataValue(bandNo)

    def useSourceNoDataValue(self, bandNo: int = None) -> bool:
        """Read QGIS docs."""
        if bandNo is None:
            bandNo = 1
        return self.provider.useSourceNoDataValue(bandNo)

    def setUseSourceNoDataValue(self, bandNo: int, use: bool):
        """Read QGIS docs."""
        return self.provider.setUseSourceNoDataValue(bandNo, use)

    def setUserNoDataValue(self, bandNo: int, noData: Iterable[QgsRasterRange]):
        """Read QGIS docs."""
        return self.provider.setUserNoDataValue(bandNo, noData)

    def userNoDataValues(self, bandNo: int = None) -> List[QgsRasterRange]:
        """Read QGIS docs."""
        if bandNo is None:
            bandNo = 1
        return self.provider.userNoDataValues(bandNo)

    def offset(self, bandNo: int) -> Optional[float]:
        return self.gdalBand(bandNo).GetOffset()

    def scale(self, bandNo: int) -> Optional[float]:
        return self.gdalBand(bandNo).GetScale()

    def source(self) -> str:
        """Return source URI."""
        return self.provider.dataSourceUri()

    def width(self) -> int:
        """Return width in pixel."""
        return self.provider.xSize()

    def height(self) -> int:
        """Return height in pixel."""
        return self.provider.ySize()

    def rasterUnitsPerPixelX(self) -> float:
        """Return pixel resolution in x."""
        return self.provider.extent().width() / self.provider.xSize()

    def rasterUnitsPerPixelY(self) -> float:
        """Return pixel resolution in y."""
        return self.provider.extent().height() / self.provider.ySize()

    def rasterUnitsPerPixel(self) -> QSizeF:
        """Return pixel resolution."""
        return QSizeF(self.rasterUnitsPerPixelX(), self.rasterUnitsPerPixelY())

    def walkGrid(
            self, blockSizeX: int, blockSizeY: int, feedback: QgsProcessingFeedback = None
    ) -> Iterator[RasterBlockInfo]:
        """Iterate block-wise over the raster."""
        pixelSizeX = self.rasterUnitsPerPixelX()
        pixelSizeY = self.rasterUnitsPerPixelY()
        extent = self.extent()
        for blockExtent in GridWalker(extent, blockSizeX, blockSizeY, pixelSizeX, pixelSizeY, feedback):
            xOffset = int(round((blockExtent.xMinimum() - extent.xMinimum()) / pixelSizeX))
            yOffset = int(round((extent.yMaximum() - blockExtent.yMaximum()) / pixelSizeY))
            width = min(blockSizeX, int(round((blockExtent.xMaximum() - blockExtent.xMinimum()) / pixelSizeX)))
            height = min(blockSizeY, int(round((blockExtent.yMaximum() - blockExtent.yMinimum()) / pixelSizeY)))
            if width == 0 or height == 0:
                continue  # empty blocks may occure, but can just skip over
            yield RasterBlockInfo(blockExtent, xOffset, yOffset, width, height)

    def setRasterPipeCrs(self, crs: QgsCoordinateReferenceSystem = None):
        if crs is None:
            projector = self.provider
            pipe = None
        elif isinstance(crs, QgsCoordinateReferenceSystem):
            pipe = QgsRasterPipe()
            pipe.set(self.provider.clone())
            projector = QgsRasterProjector()
            projector.setCrs(self.provider.crs(), crs)
            pipe.insert(1, projector)
        else:
            raise ValueError()
        self.pipe = pipe
        self.projector = projector

    def arrayFromBlock(
            self, block: RasterBlockInfo, bandList: List[int] = None, overlap: int = None,
            feedback: QgsRasterBlockFeedback = None
    ):
        """Return data for given block."""
        return self.arrayFromBoundingBoxAndSize(
            block.extent, block.width, block.height, bandList, overlap, feedback
        )

    def arrayFromBoundingBoxAndSize(
            self, boundingBox: QgsRectangle, width: int, height: int, bandList: List[int] = None,
            overlap: int = None, feedback: QgsRasterBlockFeedback = None
    ) -> Array3d:
        """Return data for given bounding box and size."""
        if bandList is None:
            bandList = range(1, self.provider.bandCount() + 1)
        if overlap is not None:
            xres = boundingBox.width() / width
            yres = boundingBox.height() / height
            boundingBox = QgsRectangle(
                boundingBox.xMinimum() - overlap * xres,
                boundingBox.yMinimum() - overlap * yres,
                boundingBox.xMaximum() + overlap * xres,
                boundingBox.yMaximum() + overlap * yres
            )
            width = width + 2 * overlap
            height = height + 2 * overlap
        arrays = list()
        for bandNo in bandList:
            assert 0 < bandNo <= self.bandCount(), f'bandNo is {bandNo}'
            block: QgsRasterBlock = self.projector.block(bandNo, boundingBox, width, height, feedback)
            array = Utils.qgsRasterBlockToNumpyArray(block=block)
            arrays.append(array)
        return arrays

    def arrayFromPixelOffsetAndSize(
            self, xOffset: int, yOffset: int, width: int, height: int, bandList: List[int] = None, overlap: int = None,
            feedback: QgsRasterBlockFeedback = None
    ) -> Array3d:
        """Return data for given pixel offset and size."""
        if self.crs().isValid():
            p1 = QgsPoint(xOffset, yOffset)
            p2 = QgsPoint(xOffset + width, yOffset + height)
            p1 = QgsPointXY(self.provider.transformCoordinates(p1, QgsRasterDataProvider.TransformImageToLayer))
            p2 = QgsPointXY(self.provider.transformCoordinates(p2, QgsRasterDataProvider.TransformImageToLayer))
        else:
            assert self.rasterUnitsPerPixel() == QSizeF(1, 1)
            p1 = QgsPointXY(xOffset, - yOffset)
            p2 = QgsPointXY(xOffset + width, -(yOffset + height))
        boundingBox = QgsRectangle(p1, p2)
        return self.arrayFromBoundingBoxAndSize(boundingBox, width, height, bandList, overlap, feedback)

    def array(
            self, xOffset: int = None, yOffset: int = None, width: int = None, height: int = None,
            bandList: List[int] = None, boundingBox: QgsRectangle = None, overlap: int = None,
            feedback: QgsRasterBlockFeedback = None
    ) -> Array3d:
        """Return data."""
        if boundingBox is None:
            if xOffset is None and width is None:
                xOffset = 0
                width = self.provider.xSize()
            if yOffset is None and height is None:
                yOffset = 0
                height = self.provider.ySize()
            array = self.arrayFromPixelOffsetAndSize(xOffset, yOffset, width, height, bandList, overlap, feedback)
        else:
            rasterUnitsPerPixelX = self.provider.extent().width() / self.provider.xSize()
            rasterUnitsPerPixelY = self.provider.extent().height() / self.provider.ySize()
            if width is None:
                width = int(round(boundingBox.width() / rasterUnitsPerPixelX))
            if height is None:
                height = int(round(boundingBox.height() / rasterUnitsPerPixelY))
            array = self.arrayFromBoundingBoxAndSize(boundingBox, width, height, bandList, overlap, feedback)
        return array

    def maskArray(
            self, array: Array3d, bandList: List[int] = None, maskNotFinite=True, defaultNoDataValue: float = None,
            maskNoDataValue=True
    ) -> Array3d:
        """Return mask for given data. No data values evaluate to False, all other to True."""

        if bandList is None:
            bandList = range(1, self.provider.bandCount() + 1)
        assert len(bandList) == len(array)
        maskArray = list()
        for i, a in enumerate(array):
            bandNo = i + 1
            m = np.full_like(a, True, dtype=bool)
            if maskNoDataValue:
                if self.provider.sourceHasNoDataValue(bandNo) and self.provider.useSourceNoDataValue(bandNo):
                    noDataValue = self.provider.sourceNoDataValue(bandNo)
                    if not isnan(noDataValue):
                        m[a == noDataValue] = False
                else:
                    if defaultNoDataValue is not None:
                        m[a == defaultNoDataValue] = False
            rasterRange: QgsRasterRange
            for rasterRange in self.provider.userNoDataValues(bandNo):
                if rasterRange.bounds() == QgsRasterRange.BoundsType.IncludeMinAndMax:
                    contained = np.logical_and(
                        np.greater_equal(a, rasterRange.min()), np.less_equal(a, rasterRange.max())
                    )
                elif rasterRange.bounds() == QgsRasterRange.BoundsType.IncludeMin:
                    contained = np.logical_and(
                        np.greater_equal(a, rasterRange.min()), np.less(a, rasterRange.max())
                    )
                elif rasterRange.bounds() == QgsRasterRange.BoundsType.IncludeMax:
                    contained = np.logical_and(
                        np.greater(a, rasterRange.min()), np.less_equal(a, rasterRange.max())
                    )
                elif rasterRange.bounds() == QgsRasterRange.BoundsType.Exclusive:
                    contained = np.logical_and(
                        np.greater(a, rasterRange.min()), np.less(a, rasterRange.max())
                    )
                else:
                    raise ValueError()

                m[contained] = False

            if maskNotFinite:
                m[np.logical_not(np.isfinite(a))] = False

            maskArray.append(m)
        return maskArray

    def pixelByPoint(self, point: Union[QgsPointXY, SpatialPoint]) -> QPoint:
        if isinstance(point, QgsPointXY):
            point = SpatialPoint(self.crs(), point)
        return point.toPixelPosition(self.layer)

    def pixelExtent(self, pixel: QPoint) -> QgsRectangle:
        xoff = self.extent().xMinimum()
        yoff = self.extent().yMaximum()
        xres = self.rasterUnitsPerPixelX()
        yres = self.rasterUnitsPerPixelY()

        x1 = xoff + pixel.x() * xres
        x2 = x1 + xres
        y1 = yoff - pixel.y() * yres
        y2 = y1 - yres

        extent = QgsRectangle(x1, y2, x2, y1)
        return extent

    def extentByGeometry(self, geometry: QgsGeometry) -> QgsRectangle:

        bb = geometry.boundingBox()
        point1 = SpatialPoint(self.crs(), QgsPointXY(bb.xMinimum(), bb.yMinimum()))
        point2 = SpatialPoint(self.crs(), QgsPointXY(bb.xMaximum(), bb.yMaximum()))
        pixel1 = point1.toPixelPosition(self.layer)
        pixel2 = point2.toPixelPosition(self.layer)
        pixel1Extent = self.pixelExtent(pixel1)
        pixel2Extent = self.pixelExtent(pixel2)

        xvalues = [pixel1Extent.xMinimum(), pixel1Extent.xMaximum(), pixel2Extent.xMinimum(), pixel2Extent.xMaximum()]
        yvalues = [pixel1Extent.yMinimum(), pixel1Extent.yMaximum(), pixel2Extent.yMinimum(), pixel2Extent.yMaximum()]

        extent = QgsRectangle(min(xvalues), min(yvalues), max(xvalues), max(yvalues))
        return extent

    def geometryCoverage(self, geometry: QgsGeometry, fractions=True) -> Tuple[np.ndarray, QgsRectangle]:
        assert geometry.type() == QgsWkbTypes.GeometryType.PolygonGeometry

        # make memory layer from geometry
        layer = QgsVectorLayer(f'Polygon?crs={self.crs().authid()}', 'polygon', 'memory')
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry(geometry))
        layer.dataProvider().addFeatures([feature])
        layer.updateExtents()

        # rasterize polygon
        extent = self.extentByGeometry(geometry)
        xsize = max(1, round(extent.width() / self.rasterUnitsPerPixelX()))
        ysize = max(1, round(extent.height() / self.rasterUnitsPerPixelY()))

        if fractions:
            xsize2 = xsize * 10
            ysize2 = ysize * 10
        else:
            xsize2 = xsize
            ysize2 = ysize

        alg = 'gdal:rasterize'
        parameters = {
            'INPUT': layer,
            'INIT': 0,
            'BURN': 1,
            'UNITS': 0, 'WIDTH': xsize2, 'HEIGHT': ysize2,
            'EXTENT': extent,
            'DATA_TYPE': 5,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }
        result = processing.run(alg, parameters)

        # read mask and calculate fractions
        maskArray = RasterReader(result['OUTPUT']).array()[0]
        fractionArray = NumpyUtils.rebinMean(maskArray, (ysize, xsize))

        return fractionArray, extent

    def sampleWeightedValues(
            self, extent: QgsRectangle, weightsArray: Array2d, bandNo: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        height, width = weightsArray.shape
        array = self.arrayFromBoundingBoxAndSize(extent, width, height, [bandNo])[0]
        maskArray = self.maskArray([array], [bandNo])[0] * (weightsArray != 0)
        values = array[maskArray]
        weights = weightsArray[maskArray]
        return values, weights

    def samplingWidthAndHeight(self, bandNo: int, extent=None, sampleSize: int = 0) -> Tuple[int, int]:
        """Return number of pixel for width and heigth, that approx. match the given sample size."""

        if extent is None:
            extent = self.extent()

        if sampleSize == 0:
            width = ceil((extent.xMaximum() - extent.xMinimum()) / self.rasterUnitsPerPixelX())
            height = ceil((extent.yMaximum() - extent.yMinimum()) / self.rasterUnitsPerPixelY())
        else:
            bandStats: QgsRasterBandStats = self.provider.bandStatistics(bandNo, 0, extent, sampleSize)
            width, height = bandStats.width, bandStats.height

        return width, height

    def sampleValues(
            self, bandNo: int, extent=None, sampleSize: int = 0,
            excludeNoDataValues=True, excludeNotFinite=True, defaultNoDataValue: float = None,
            feedback: QgsRasterBlockFeedback = None
    ) -> np.ndarray:
        """Return sample data."""
        if extent is None:
            extent = self.extent()
        width, height = self.samplingWidthAndHeight(bandNo, extent, sampleSize)
        array = self.arrayFromBoundingBoxAndSize(extent, width, height, [bandNo], None, feedback)
        if excludeNoDataValues:
            maskArray = self.maskArray(array, [bandNo], excludeNotFinite, defaultNoDataValue)
            values = array[0][maskArray[0]]
        else:
            values = array[0].flatten()
        return values

    def uniqueValueCounts(
            self, bandNo: int, extent=None, sampleSize: int = 0, excludeNoDataValues=True, excludeNotFinite=True,
            defaultNoDataValue: float = None, feedback: QgsRasterBlockFeedback = None
    ) -> Tuple[List[float], List[int]]:
        """Return unique value counts."""
        values = self.sampleValues(
            bandNo, extent, sampleSize, excludeNoDataValues, excludeNotFinite, defaultNoDataValue, feedback
        )
        uniqueValues, counts = np.unique(values, return_counts=True)
        return list(map(float, uniqueValues)), list(map(int, counts))

    def metadataItem(
            self, key: str, domain: str = '', bandNo: int = None, checkCustomProperties=True
    ) -> Optional[MetadataValue]:
        """Return metadata item."""

        key2 = key.replace(' ', '_')

        # check STAC
        if domain == 'envi':
            value = self.stacMetadata['properties']['envi:metadata'].get(key)
            if value is not None:
                if bandNo is not None:
                    value = value[bandNo - 1]
        else:
            if bandNo is not None:
                value = self.stacMetadata['properties']['eo:bands'][bandNo - 1].get(key)
            else:
                value = self.stacMetadata['properties'].get(key)
        if value is not None:
            return value

        # check QGISPAM
        if checkCustomProperties:
            if bandNo is None:
                string = self.layer.customProperty(f'QGISPAM/dataset/{domain}/{key}')
                if string is None:
                    string = self.layer.customProperty(f'QGISPAM/dataset/{domain}/{key2}')
            else:
                string = self.layer.customProperty(f'QGISPAM/band/{bandNo}/{domain}/{key}')
                if string is None:
                    string = self.layer.customProperty(f'QGISPAM/band/{bandNo}/{domain}/{key2}')
            if string is not None:
                return Utils.stringToMetadateValue(str(string))

        if self.gdalDataset is None:
            return None

        string = self._gdalObject(bandNo).GetMetadataItem(key, domain)
        if string is None:
            string = self._gdalObject(bandNo).GetMetadataItem(key2, domain)
        if string is None:
            return None
        return Utils.stringToMetadateValue(string)

    def metadataDomain(self, domain: str = '', bandNo: int = None) -> MetadataDomain:
        """Return domain metadata."""
        metadata = {
            key: Utils.stringToMetadateValue(value)
            for key, value in self._gdalObject(bandNo).GetMetadata(domain).items()
        }
        return metadata

    def metadata(self, bandNo: int = None) -> Metadata:
        """Return metadata."""
        domains = self.metadataDomainKeys(bandNo)
        return {domain: self.metadataDomain(domain, bandNo) for domain in domains}

    def metadataDomainKeys(self, bandNo: int = None) -> List[str]:
        """Return metadata domain names."""

        if self.gdalDataset is None:
            return []

        domains: List = self._gdalObject(bandNo).GetMetadataDomainList()
        if domains is None:
            domains = []

        return domains

    def isSpectralRasterLayer(self, quickCheck=True):
        """Return whether a raster has wavelength information."""

        if quickCheck:
            return self.wavelength(1) is not None
        else:
            for bandNo in range(1, self.bandCount() + 1):
                if self.wavelength(bandNo) is None:
                    return False
            return True

    def findBandName(self, bandName: str) -> Optional[int]:
        """Find band number by name."""
        for bandNo in range(1, self.bandCount() + 1):
            if self.bandName(bandNo) == bandName:
                return bandNo
        return None

    def wavelengthUnits(self, bandNo: int, guess=True) -> Optional[str]:
        """Return wavelength units."""

        # check STAC
        if 'center_wavelength' in self.stacMetadata['properties']['eo:bands'][bandNo - 1]:
            return self.Micrometers  # STAC EO Extension always uses Micrometers
        if 'full_width_half_max' in self.stacMetadata['properties']['eo:bands'][bandNo - 1]:
            return self.Micrometers  # STAC EO Extension always uses Micrometers
        if 'wavelength_units' in self.stacMetadata['properties']['envi:metadata']:
            return self.stacMetadata['properties']['envi:metadata']['wavelength_units']

        for key in [
            'wavelength_units',
            'Wavelength_unit',  # support for FORCE BOA files
            'wavelength units'  # support for GDAL Metadata Editor dialog (by @jakimow)
        ]:
            # check band-level domains
            for domain in set(self.metadataDomainKeys(bandNo) + ['']):
                units = self.metadataItem(key, domain, bandNo)
                if units is not None:
                    return Utils.wavelengthUnitsLongName(units)

            # check dataset-level domains
            for domain in set(self.metadataDomainKeys() + ['']):
                units = self.metadataItem(key, domain)
                if units is not None:
                    return Utils.wavelengthUnitsLongName(units)

        # finally, we try to guess the units from the actual value
        if guess:
            wavelength = self.wavelength(bandNo, raw=True)
            if wavelength is not None:
                if wavelength < 100:
                    units = 'Micrometers'
                else:
                    units = 'Nanometers'
                return units

        return None

    def wavelength(self, bandNo: int, units: str = None, raw=False) -> Optional[float]:
        """Return band center wavelength in nanometers. Optionally, specify destination units."""

        # special handling: FORCE TSI raster
        enviDescription = self.metadataItem('description', 'ENVI')
        if enviDescription is not None:
            if enviDescription[0].startswith('FORCE') and enviDescription[0].endswith('Time Series Analysis'):
                return None

        if raw:
            conversionFactor = 1.
        else:
            if units is None:
                units = self.Nanometers

            wavelength_units = self.wavelengthUnits(bandNo)
            if wavelength_units is None:
                return None

            conversionFactor = Utils.wavelengthUnitsConversionFactor(wavelength_units, units)

        # check STAC
        wavelength = self.stacMetadata['properties']['eo:bands'][bandNo - 1].get('center_wavelength')
        if wavelength is not None:
            return conversionFactor * float(wavelength)

        wavelength = self.stacMetadata['properties']['envi:metadata'].get('wavelength')
        if wavelength is not None:
            return conversionFactor * float(wavelength[bandNo - 1])

        for key in [
            'wavelength',
            'Wavelength'  # support for FORCE BOA files
        ]:
            # check band-level domains
            for domain in set(self.metadataDomainKeys(bandNo) + ['']):
                wavelength = self.metadataItem(key, domain, bandNo)
                if wavelength is not None:
                    return conversionFactor * float(wavelength)

            # check dataset-level domains
            for domain in set(self.metadataDomainKeys() + ['']):
                wavelengths = self.metadataItem(key, domain)
                if wavelengths is not None:
                    wavelength = wavelengths[bandNo - 1]
                    return conversionFactor * float(wavelength)

        return None

    def findWavelength(self, wavelength: Optional[float], units: str = None) -> Optional[int]:
        """Find band number by wavelength."""
        if wavelength is None:
            return None
        if units is not None:
            wavelength = wavelength * Utils.wavelengthUnitsConversionFactor(units, 'nm')

        bandNos = list()
        distances = list()
        for bandNo in range(1, self.bandCount() + 1):
            wavelength_ = self.wavelength(bandNo)
            if wavelength_ is None:
                continue
            bandNos.append(bandNo)
            distances.append(abs(wavelength_ - wavelength))
        if len(bandNos) == 0:
            return None

        return bandNos[np.argmin(distances)]

    def fwhm(self, bandNo: int, units: str = None) -> Optional[float]:
        """Return band FWHM in nanometers. Optionally, specify destination units."""

        if units is None:
            units = self.Nanometers

        wavelength_units = self.wavelengthUnits(bandNo)
        if wavelength_units is None:
            return None

        conversionFactor = Utils.wavelengthUnitsConversionFactor(wavelength_units, units)

        # check STAC
        fwhm = self.stacMetadata['properties']['eo:bands'][bandNo - 1].get('full_width_half_max')
        if fwhm is not None:
            return conversionFactor * float(fwhm)

        fwhm = self.stacMetadata['properties']['envi:metadata'].get('fwhm')
        if fwhm is not None:
            return conversionFactor * float(fwhm[bandNo - 1])

        # check band-level domains
        for domain in set(self.metadataDomainKeys(bandNo) + ['']):
            fwhm = self.metadataItem('fwhm', domain, bandNo)
            if fwhm is not None:
                return conversionFactor * float(fwhm)

        # check dataset-level domains
        for domain in set(self.metadataDomainKeys() + ['']):
            fwhm = self.metadataItem('fwhm', domain)
            if fwhm is not None:
                fwhm = fwhm[bandNo - 1]
                return conversionFactor * float(fwhm)

        return None

    def badBandMultiplier(self, bandNo: int) -> int:
        """Return bad band multiplier, 0 for bad band and 1 for good band."""

        if self.gdalDataset is None:
            return 1

        # check STAC
        badBandMultiplier = self.stacMetadata['properties']['eo:bands'][bandNo - 1].get('enmapbox:bad_band_multiplier')
        if badBandMultiplier is not None:
            return int(badBandMultiplier)

        badBandMultiplier = self.stacMetadata['properties']['envi:metadata'].get('bbl')
        if badBandMultiplier is not None:
            return int(badBandMultiplier[bandNo - 1])

        # check band-level domains
        for domain in set(self.metadataDomainKeys(bandNo) + ['']):
            badBandMultiplier = self.metadataItem('bbl', domain, bandNo)
            if badBandMultiplier is not None:
                return int(badBandMultiplier)

        # check dataset-level domains
        for domain in set(self.metadataDomainKeys() + ['']):
            bbl = self.metadataItem('bbl', domain)
            if bbl is not None:
                badBandMultiplier = bbl[bandNo - 1]
                return int(badBandMultiplier)

        return 1

    def startTime(self, bandNo: int = None) -> Optional[QDateTime]:
        """Return raster / band start time."""

        if bandNo is not None:

            # special handling: FORCE TSI raster
            enviDescription = self.metadataItem('description', 'ENVI')
            if enviDescription is not None:
                if enviDescription[0].startswith('FORCE') and enviDescription[0].endswith('Time Series Analysis'):
                    decimalYear = float(self.metadataItem('wavelength', '', bandNo))
                    return Utils.decimalYearToDateTime(decimalYear)

            # check STAC
            dateTime = self.stacMetadata['properties']['envi:metadata'].get('eo:start_datetime')
            if dateTime is not None:
                return Utils.parseDateTime(dateTime[bandNo - 1])

            dateTime = self.stacMetadata['properties']['envi:metadata'].get('eo:datetime')
            if dateTime is not None:
                return Utils.parseDateTime(dateTime[bandNo - 1])

            dateTime = self.stacMetadata['properties']['eo:bands'][bandNo - 1].get('start_datetime')
            if dateTime is not None:
                return Utils.parseDateTime(dateTime)

            dateTime = self.stacMetadata['properties']['eo:bands'][bandNo - 1].get('datetime')
            if dateTime is not None:
                return Utils.parseDateTime(dateTime)

            # check band-level default-domain
            dateTime = self.metadataItem('start_time', '', bandNo)

            if dateTime is not None:
                return Utils.parseDateTime(dateTime)

            # check band-level FORCE-domain (see #9)
            dateTime = self.metadataItem('Date', 'FORCE', bandNo)

            if dateTime is not None:
                return Utils.parseDateTime(dateTime)

            # check band-level default-domain for NETCDF_DIM_time (see #251)
            dateTime = self.metadataItem('NETCDF_DIM_time', '', bandNo)

            if dateTime is not None:
                dateTimeUnit = self.metadataItem('time#units')  # e.g. 'days since 1970-01-01 00:00:00'
                unit, _, datestamp, *tmp = dateTimeUnit.split(' ')
                if len(tmp) == 0:
                    tmp = ['00:00:00']
                hours, minutes, seconds = tmp[0].split(':')
                years, months, days = datestamp.split('-')
                dateTime0 = QDateTime(int(years), int(months), int(days), int(hours), int(minutes), int(seconds))
                if unit == 'seconds':
                    return dateTime0.addSecs(int(dateTime))
                elif unit == 'minutes':
                    return dateTime0.addSecs(int(dateTime) * 60)
                elif unit == 'hours':
                    return dateTime0.addSecs(int(dateTime) * 60 * 60)
                elif unit == 'days':
                    return dateTime0.addDays(int(dateTime))
                elif unit == 'months':
                    return dateTime0.addMonths(int(dateTime))
                elif unit == 'years':
                    return dateTime0.addYears(int(dateTime))
                else:
                    raise NotImplementedError(dateTimeUnit)

            # check R terra (see #907)
            if self.terraMetadata is not None:
                if 'time' in self.terraMetadata and 'timestep' in self.terraMetadata:
                    if self.terraMetadata['timestep'] == 'days':
                        year, month, day = self.terraMetadata['time'][bandNo - 1].split('-')
                        return QDateTime(QDate(int(year), int(month), int(day)))
                    elif self.terraMetadata['timestep'] == 'seconds':
                        tmp1, tmp2 = self.terraMetadata['time'][bandNo - 1].split(' ')
                        year, month, day = tmp1.split('-')
                        hour, minute, second = tmp2.split(':')
                        return QDateTime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                    else:
                        raise NotImplementedError(self.terraMetadata['timestep'])

        # check STAC
        dateTime = self.stacMetadata['properties']['envi:metadata'].get('acquisition_time')
        if dateTime is not None:
            return Utils.parseDateTime(dateTime)

        # check dataset-level default-domain
        dateTime = self.metadataItem('start_time')
        if dateTime is not None:
            return Utils.parseDateTime(dateTime)

        # check dataset-level IMAGERY-domain
        dateTime = self.metadataItem('ACQUISITIONDATETIME', 'IMAGERY')
        if dateTime is not None:
            return Utils.parseDateTime(dateTime)

        # check dataset-level ENVI-domain
        dateTime = self.metadataItem('acquisition_time', 'ENVI')
        if dateTime is not None:
            return Utils.parseDateTime(dateTime)

        return None

    def endTime(self, bandNo: int = None) -> Optional[QDateTime]:
        """Return raster / band end time."""

        # check STAC
        if bandNo is not None:
            dateTime = self.stacMetadata['properties']['envi:metadata'].get('eo:end_datetime')
            if dateTime is not None:
                return Utils.parseDateTime(dateTime[bandNo - 1])

            dateTime = self.stacMetadata['properties']['eo:bands'][bandNo - 1].get('end_datetime')
            if dateTime is not None:
                return Utils.parseDateTime(dateTime)

        # check band-level domain
        if bandNo is not None:
            dateTime = self.metadataItem('end_time', '', bandNo)

            if dateTime is not None:
                return Utils.parseDateTime(dateTime)

        # check dataset-level default-domain
        dateTime = self.metadataItem('end_time')
        if dateTime is not None:
            return Utils.parseDateTime(dateTime)

        return None

    def centerTime(self, bandNo: int = None) -> Optional[QDateTime]:
        """Return raster / band center time."""

        startTime = self.startTime(bandNo)
        if startTime is None:
            return None

        endTime = self.endTime(bandNo)
        if endTime is None:
            return startTime

        msecs = startTime.msecsTo(endTime)
        return startTime.addMSecs(int(msecs / 2))

    def findTime(self, centerTime: Optional[QDateTime]) -> Optional[int]:
        """Find band number by center time."""
        if centerTime is None:
            return None

        bandNos = list()
        distances = list()
        for bandNo in range(1, self.bandCount() + 1):
            centerTime_ = self.centerTime(bandNo)
            if centerTime_ is None:
                continue
            bandNos.append(bandNo)
            distances.append(abs(centerTime_.msecsTo(centerTime)))
        if len(bandNos) == 0:
            return None

        return bandNos[np.argmin(distances)]

    def lineMemoryUsage(self, nBands: int = None, dataTypeSize: int = None) -> int:
        """Returns the memory (in bytes) used to store a single raster line."""
        if nBands is None:
            nBands = self.bandCount()
        if dataTypeSize is None:
            dataTypeSize = self.dataTypeSize()
        return self.width() * nBands * dataTypeSize

    def _gdalObject(self, bandNo: int = None) -> Union[gdal.Band, gdal.Dataset]:
        if bandNo is None:
            gdalObject = self.gdalDataset
        else:
            gdalObject = self.gdalDataset.GetRasterBand(bandNo)
        return gdalObject

    def gdalBand(self, bandNo: int = None) -> gdal.Band:
        return self._gdalObject(bandNo)
