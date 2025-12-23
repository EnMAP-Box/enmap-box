from osgeo import gdal, gdal_array
from multiprocessing import Process, Queue
from time import sleep
import numpy as np
from _classic.hubdc.core import RasterDataset, RasterBandDataset, RasterDriver

class Writer():
    WRITE_ARRAY, WRITE_BANDARRAY, CALL_RASTERMETHOD, CALL_BANDMETHOD, CLOSE_RASTERS, CLOSE_WRITER = range(6)

    @classmethod
    def getRaster(cls, outputRaster, filename):
        raster = outputRaster[filename]
        assert isinstance(raster, RasterDataset)
        return raster

    @classmethod
    def handleTask(cls, task, args, outputRasters):
        if task is cls.WRITE_ARRAY:
            cls.writeArray(outputRasters, *args)
        elif task is cls.WRITE_BANDARRAY:
            cls.writeBandArray(outputRasters, *args)
        elif task is cls.CALL_RASTERMETHOD:
            cls.callImageMethode(outputRasters, *args)
        elif task is cls.CALL_BANDMETHOD:
            cls.callBandMethode(outputRasters, *args)
        elif task is cls.CLOSE_RASTERS:
            cls.closeRasters(outputRasters, *args)
        elif task is cls.CLOSE_WRITER:
            pass
        else:
            raise ValueError(str(task))

    @staticmethod
    def createRaster(outputRasters, filename, bands, dtype, grid, driver, creationOptions):
        assert isinstance(driver, RasterDriver)
        if dtype == bool:
            dtype = np.uint8
        outputRasters[filename] = driver.create(grid=grid, bands=bands,
                                                gdalType=gdal_array.NumericTypeCodeToGDALTypeCode(dtype),
                                                filename=filename, options=creationOptions)

    @staticmethod
    def closeRasters(outputRasters, createEnviHeader):
        for filename, ds in list(outputRasters.items()):
            outputRaster = outputRasters.pop(filename)
            outputRaster.flushCache()
            if createEnviHeader:
                outputRaster.writeENVIHeader()
            outputRaster.close()

    @classmethod
    def writeArray(cls, outputRasters, filename, array, subgrid, maingrid, driver, creationOptions):

        if filename not in outputRasters:
            Writer.createRaster(outputRasters=outputRasters, filename=filename, bands=len(array), dtype=array.dtype, grid=maingrid, driver=driver, creationOptions=creationOptions)
        cls.getRaster(outputRasters, filename).writeArray(array=array, grid=subgrid)

    @classmethod
    def writeBandArray(cls, outputRasters, filename, array, index, bands, subgrid, maingrid, driver, creationOptions):

        if filename not in outputRasters:
            Writer.createRaster(outputRasters=outputRasters, filename=filename, bands=bands, dtype=array.dtype, grid=maingrid, driver=driver, creationOptions=creationOptions)
        cls.getRaster(outputRasters, filename).band(index=index).writeArray(array=array, grid=subgrid)

    @classmethod
    def callImageMethode(cls, outputRasters, filename, method, kwargs):
        getattr(*method)(cls.getRaster(outputRasters, filename), **kwargs)

    @classmethod
    def callBandMethode(cls, outputRasters, filename, index, method, kwargs):
        getattr(*method)(cls.getRaster(outputRasters, filename).band(index=index), **kwargs)

class WriterProcess(Process):

    def __init__(self):
        Process.__init__(self)
        self.outputRasters = dict()
        self.queue = Queue()

    def run(self):

        try:
            gdal.SetCacheMax(1)
            while True:

                sleep(0.01) # this should prevent high CPU load during idle time (not sure if this is really needed)
                if self.queue.qsize() == 0:
                    continue
                value = self.queue.get()
                task, args = value[0], value[1:]
                Writer.handleTask(task=task, args=args, outputRasters=self.outputRasters)
                if task is Writer.CLOSE_WRITER:
                    break

        except:

            import traceback
            tb = traceback.format_exc()
            print(tb)

class QueueMock():

    def __init__(self):
        self.outputRasters = dict()

    def put(self, value):
        task, args = value[0], value[1:]
        Writer.handleTask(task=task, args=args, outputRasters=self.outputRasters)
