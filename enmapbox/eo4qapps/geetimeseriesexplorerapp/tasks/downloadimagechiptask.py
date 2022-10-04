import traceback
from typing import List, Optional

import numpy as np
from osgeo import gdal

from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapbox.utils import importEarthEngine
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from geetimeseriesexplorerapp.imageinfo import ImageInfo
from qgis.core import QgsTask, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsRectangle, QgsMessageLog, Qgis
from typeguard import typechecked


@typechecked
class DownloadImageChipBandTask(QgsTask):

    def __init__(self, filename: str, location: SpatialPoint, eeImage, bandName: str):
        QgsTask.__init__(self, 'Download image chip band task', QgsTask.CanCancel)
        self.filename = filename
        self.location = location
        self.eeImage = eeImage
        self.bandName = bandName
        self.radius = 250  # results in image chips with 500 x 500 pixel
        self.exception: Optional[Exception] = None

    def run(self):
        eeImported, ee = importEarthEngine(False)

        try:
            self.alreadyExists = QgsRasterLayer(self.filename).isValid()
            if self.alreadyExists:
                return True

            eeImage = self.eeImage.select(self.bandName)

            # query image info
            info = ImageInfo(eeImage.getInfo())
            ul = info.upperLefts[0]
            xres = info.xresolutions[0]
            yres = info.yresolutions[0]
            epsg = info.epsgs[0]
            dataTypeMin = info.dataTypeRanges[0][0]

            # calculate sampling region that is aligned with the pixel grid
            p = self.location.toCrs(QgsCoordinateReferenceSystem(epsg))
            xmin = (int((p.x() - ul.x()) / xres) - self.radius) * xres + ul.x()
            xmax = xmin + 2 * self.radius * xres
            ymax = (int((p.y() - ul.y()) / yres) - self.radius) * yres + ul.y()
            ymin = ymax + 2 * self.radius * yres
            eeExtent = ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], epsg, evenOdd=False)

            # query data
            defaultValue = dataTypeMin  # default values will be masked out later!
            sample = eeImage.sampleRectangle(eeExtent, None, defaultValue, defaultValue).getInfo()
            msample = eeImage.mask().sampleRectangle(eeExtent, None, 0, 0).getInfo()

            # prepare data
            array = np.array([sample['properties'].pop(self.bandName)])
            if array.dtype == np.float64:
                array = array.astype(np.float32)
            marray = np.array([msample['properties'].pop(self.bandName)])

            noDataValue = Utils.defaultNoDataValue(array.dtype)
            array[marray == 0] = noDataValue

            # write data
            extent = QgsRectangle(xmin, ymin, xmax, ymax)
            crs = QgsCoordinateReferenceSystem(epsg)
            driver = Driver(self.filename, 'GTiff', ['INTERLEAVE=BAND', 'COMPRESS=LZW', 'PREDICTOR=2'])
            raster = driver.createFromArray(array, extent, crs)
            raster.setNoDataValue(noDataValue)
            raster.setBandName(self.bandName, 1)
            del raster

            assert QgsRasterLayer(self.filename).isValid()  # this will also calculate band statistics

        except Exception as e:
            traceback.print_exc()
            self.exception = e
            return False

        return True

    def finished(self, result):
        if self.isCanceled():
            return
        elif not result:
            raise self.exception

        if self.alreadyExists:
            QgsMessageLog.logMessage(f'already exists: {self.filename}', tag="GEE Time Series Explorer",
                                     level=Qgis.Success)
        else:
            QgsMessageLog.logMessage(f'downloaded: {self.filename}', tag="GEE Time Series Explorer", level=Qgis.Success)


@typechecked
class DownloadImageChipTask(QgsTask):
    """Build image chip VRT."""

    def __init__(self, filename: str, filenames: List[str], location: SpatialPoint):
        QgsTask.__init__(self, 'Create image chip task', QgsTask.CanCancel)
        self.filename = filename
        self.filenames = filenames
        self.location = location
        self.exception: Optional[Exception] = None

    def run(self):
        try:
            self.alreadyExists = QgsRasterLayer(self.filename).isValid()
            if self.alreadyExists:
                return True

            options = gdal.BuildVRTOptions(resolution='highest', separate=True)
            ds = gdal.BuildVRT(self.filename, self.filenames, options=options)
            raster = RasterWriter(ds)
            self.bandNames = list()
            for i, filename in enumerate(self.filenames):
                bandName = RasterReader(filename).bandName(1)
                raster.setBandName(bandName, i + 1)
                self.bandNames.append(bandName)
        except Exception as e:
            traceback.print_exc()
            self.exception = e
            return False

        return True

    def finished(self, result):
        if self.isCanceled():
            return
        elif not result:
            raise self.exception

        if self.alreadyExists:
            QgsMessageLog.logMessage(f'already exists: {self.filename}', tag="GEE Time Series Explorer",
                                     level=Qgis.Success)
        else:
            QgsMessageLog.logMessage(f'downloaded: {self.filename}', tag="GEE Time Series Explorer",
                                     level=Qgis.Success)
