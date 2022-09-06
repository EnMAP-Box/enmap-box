import traceback
from os import DirEntry, scandir
from os.path import join
from typing import List, Optional

from osgeo import gdal

from enmapboxprocessing.rasterwriter import RasterWriter
from qgis.core import QgsTask, QgsMessageLog, Qgis
from typeguard import typechecked


@typechecked
class BuildImageChipVrtsTask(QgsTask):

    def __init__(self, root: str):
        QgsTask.__init__(self, 'Build image chip VRTs task', QgsTask.CanCancel)
        self.root = root  # e.g. C:\Users\Andreas\Downloads\GEETSE
        self.exception: Optional[Exception] = None

    def run(self):
        try:
            folderCollection: DirEntry
            folderLocation: DirEntry
            folderChip: DirEntry
            f: DirEntry
            for folderCollection in scandir(join(self.root, 'chips')):
                # e.g. <root>/chips/LANDSAT_LC09_C02_T1_L2'
                if not folderCollection.is_dir():
                    continue
                for folderLocation in scandir(folderCollection.path):
                    # e.g. <root>/chips/LANDSAT_LC09_C02_T1_L2/X0013.2867979971745_Y0052.5076947733707
                    if not folderLocation.is_dir():
                        continue
                    for folderChip in scandir(folderLocation.path):
                        # e.g. <root>/chips/LANDSAT_LC09_C02_T1_L2/X0013.2867979971745_Y0052.5076947733707/LC09_192023_20211103
                        if not folderChip.is_dir():
                            continue
                        srcDss: List[gdal.Dataset] = [gdal.Open(f.path) for f in scandir(folderChip.path) if
                                                      f.is_file() and f.path.endswith('.tif')]
                        if len(srcDss) == 0:
                            continue
                        filename = join(folderChip.path, folderChip.name + '.vrt')
                        ds = gdal.BuildVRT(filename, srcDss, separate=True)
                        writer = RasterWriter(ds)
                        for bandNo, srcDs in enumerate(srcDss, 1):
                            rb: gdal.Band = srcDs.GetRasterBand(1)
                            writer.setBandName(rb.GetDescription(), bandNo)

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

        QgsMessageLog.logMessage(
            f'All Image Chip VRTs built: {self.root}', tag="GEE Time Series Explorer", level=Qgis.Success
        )
