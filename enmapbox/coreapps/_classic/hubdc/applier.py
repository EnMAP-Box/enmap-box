"""
Basic tools for setting up a function to be applied over a raster processing chain.
The :class:`~_classic.hubdc.applier.Applier` class is the main point of entry in this module.

"""

from __future__ import print_function
from multiprocessing import Pool, cpu_count
from os import walk
from os.path import splitdrive, split, splitext, join
from timeit import default_timer as now
import numpy
from osgeo.gdal_array import NumericTypeCodeToGDALTypeCode
from _classic.hubdc.core import *
import _classic.hubdc.core  # needed for sphinx
from _classic.hubdc.writer import Writer, WriterProcess, QueueMock
from _classic.hubdc.progressbar import CUIProgressBar
import _classic.hubdc.hubdcerrors as errors

class ApplierOptions(object):
    '''Enumeration types.'''

    class AutoExtent(object):
        '''Options for automatic extent calculation.'''
        union = 'union'
        intersection = 'intersection'

    class AutoResolution(object):
        '''Options for automatic resolution calculation.'''
        minimum = 'minimum'
        maximum = 'maximum'
        average = 'average'


class ApplierDefaults(object):
    '''Default values for various settings used inside an applier processing chain.'''

    autoExtent = ApplierOptions.AutoExtent.intersection
    autoResolution = ApplierOptions.AutoResolution.minimum
    nworker = None
    nwriter = None
    blockSize = RasterSize(x=256, y=256)
    writeENVIHeader = True

    class GDALEnv(object):
        cacheMax = 100 * 2 ** 20
        swathSize = 100 * 2 ** 20
        disableReadDirOnOpen = True
        maxDatasetPoolSize = 100

    class GDALWarp(object):
        errorThreshold = 0.
        memoryLimit = 100 * 2 ** 20
        multithread = False


class ApplierIO(object):
    '''
    Base class for io items.
    For internal use only.'''

    def __init__(self, filename):
        self._operator = None
        if not isinstance(filename, str):
            raise TypeError('Expected filename of type str, got: {} instead'.format(type(filename)))
        self._filename = filename

    def setOperator(self, operator):
        '''Pass a handle on the operator object.'''
        assert isinstance(operator, ApplierOperator)
        self._operator = operator

    def operator(self):
        '''Returns the operator object.'''
        assert isinstance(self._operator, ApplierOperator)
        return self._operator

    def filename(self):
        '''Returns the filename.'''
        return self._filename


class ApplierInputRaster(ApplierIO):
    '''Class for handling input raster dataset.'''

    @classmethod
    def fromDataset(cls, dataset):
        '''Create an input raster from an :class:`~_classic.hubdc.model.Dataset`.'''

        assert isinstance(dataset, RasterDataset)
        applierInputRaster = ApplierInputRaster(filename='')
        applierInputRaster._dataset = dataset
        return applierInputRaster

    def __init__(self, filename):
        '''Creates an instance from raster stored at ``filename``.'''

        ApplierIO.__init__(self, filename=filename)
        self._dataset = None

    def __repr__(self):
        return '{cls}(filename={filename})'.format(cls=self.__class__.__name__, filename=str(self.filename()))

    def dataset(self):
        '''Returns the :class:`~hubdc.model.Raster` object.'''
        if self._dataset is None:
            self._dataset = openRasterDataset(filename=self.filename())

        return self._dataset

    def _freeUnpickableResources(self):
        self._dataset = None

    def array(self, indices=None, overlap=0, resampleAlg=gdal.GRA_NearestNeighbour, noDataValue=None,
              errorThreshold=ApplierDefaults.GDALWarp.errorThreshold,
              warpMemoryLimit=ApplierDefaults.GDALWarp.memoryLimit,
              multithread=ApplierDefaults.GDALWarp.multithread,
              grid=None):
        '''
        Returns image data as 3-d numpy array of shape = (zsize, ysize, xsize),
        where zsize is the number of bands.

        :param indices: list of band indices to read (default is all bands)
        :param overlap: the number of pixels to additionally read along each spatial dimension
        :param resampleAlg: GDAL resampling algorithm, e.g. gdal.GRA_NearestNeighbour
        :param noDataValue: explicitely set the noDataValue used for reading; this overwrites the noDataValue defined by the raster itself
        :param errorThreshold: error threshold for approximation transformer (in pixels)
        :param warpMemoryLimit: size of working buffer in bytes
        :param multithread: whether to multithread computation and I/O operations
        :param grid: explicitly set the :class:`~hubdc.model.Grid`, for which image data is returned
        '''

        if grid is None:
            grid = self.operator().subgrid().pixelBuffer(buffer=overlap)

        array = self.dataset().array(indices=indices, grid=grid, resampleAlg=resampleAlg, noDataValue=noDataValue,
                                     errorThreshold=errorThreshold, warpMemoryLimit=warpMemoryLimit,
                                     multithread=multithread,)
        return array

    def fractionArray(self, categories, overlap=0, index=None):
        '''
        Returns a stack of category fractions for the given ``categories`` as a 3-d numpy array of
        shape = (zsize, ysize, xsize), where zsize is the number of categories.

        :param categories: list of categories of interest
        :param overlap: the number of pixels to additionally read along each spatial dimension
        :param index: index to the band holding the categories
        '''

        assert self.dataset().zsize() == 1 or index is not None
        if index is None:
            index = 0
        grid = self.operator().subgrid().pixelBuffer(buffer=overlap)

        # create tmp dataset with binarized categories in original resolution

        extentInSourceProjection = grid.extent().reproject(projection=self.dataset().projection())
        gridInSourceProjection = Grid(extent=extentInSourceProjection, resolution=self.dataset().grid().resolution())
        gridInSourceProjection = gridInSourceProjection.anchor(point=self.dataset().grid().extent().upperLeft())
        gridInSourceProjection = gridInSourceProjection.pixelBuffer(buffer=1)
        tmpDataset = self.dataset().translate(grid=gridInSourceProjection, bandList=[index + 1])
        tmpArray = tmpDataset.readAsArray()

        binarizedArray = list()
        for category in categories:
            if category is None:
                binarizedArray.append(np.full_like(tmpArray[0], fill_value=0.))
                assert 0 # do we need this?
            else:
                binarizedArray.append(numpy.float32(tmpArray[0] == category))
        binarizedDataset = RasterDataset.fromArray(grid=gridInSourceProjection, array=binarizedArray)


        binarizedInputRaster = ApplierInputRaster.fromDataset(dataset=binarizedDataset)
        binarizedInputRaster.setOperator(operator=self.operator())

        array = binarizedInputRaster.array(overlap=overlap, resampleAlg=gdal.GRA_Average)
        return array

    def sample(self, mask, resampleAlg=gdal.GRA_NearestNeighbour, noDataValue=None,
               errorThreshold=ApplierDefaults.GDALWarp.errorThreshold,
               warpMemoryLimit=ApplierDefaults.GDALWarp.memoryLimit,
               multithread=ApplierDefaults.GDALWarp.multithread):
        '''
        Returns all pixel profiles for which ``mask`` is True as a 2-d numpy array of shape = (zsize, samples).
        Note that pixel profiles are individually accessed, which is fast for sparse masks, but slow otherwise.

        :param overlap: the number of pixels to additionally read along each spatial dimension
        :param resampleAlg: GDAL resampling algorithm, e.g. gdal.GRA_NearestNeighbour
        :param noDataValue: explicitely set the noDataValue used for reading; this overwrites the noDataValue defined by the raster itself
        :param errorThreshold: error threshold for approximation transformer (in pixels)
        :param warpMemoryLimit: size of working buffer in bytes
        :param multithread: whether to multithread computation and I/O operations
        '''

        assert isinstance(mask, numpy.ndarray)
        assert mask.dtype == numpy.bool
        assert mask.ndim == 3
        assert mask.shape[0] == 1
        assert mask.shape[1:] == self.operator().subgrid().shape()

        ys, xs = numpy.indices(mask.shape[1:])[:, mask[0]]
        profiles = list()
        for y, x in zip(ys, xs):
            grid = self.operator().subgrid().subset(offset=Pixel(x=x, y=y), size=RasterSize(x=1, y=1))
            profiles.append(self.array(resampleAlg=resampleAlg, noDataValue=noDataValue, errorThreshold=errorThreshold,
                                       warpMemoryLimit=warpMemoryLimit, multithread=multithread, grid=grid))
        if len(profiles) != 0:
            profiles = numpy.hstack(profiles)[:, :, 0]
        else:
            profiles = numpy.empty((self.dataset().zsize(), 0))
        return profiles

    def metadataItem(self, key, domain):
        """Returns a metadata item."""
        return self.dataset().metadataItem(key=key, domain=domain)

    def metadataDict(self):
        """Returns the metadata dictionary."""
        return self.dataset().metadataDict()

    def noDataValue(self, default=None):
        '''Return single image no data value. Only valid to use if all bands have the same no data value.'''
        return self.dataset().noDataValue(default=default)

    def noDataValues(self, default=None):
        """Return band no data values."""
        return self.dataset().noDataValues(default=default)

    def categoryColors(self, index=0):
        """Return category colors for band given by ``index``."""
        return self.dataset().band(index=index).categoryColors()

    def categoryNames(self, index=0):
        """Return category names for band given by ``index``."""
        return self.dataset().band(index=index).categoryNames()

    def descriptions(self):
        """Return band descriptions."""
        return [band.description() for band in self.dataset().bands()]


class ApplierInputVector(ApplierIO):
    '''Class for handling the vector dataset given by it's ``filename`` and ``layerNameOrIndex``.'''

    def __init__(self, filename, layerNameOrIndex=0):
        '''

        :param filename: filename
        :param layerNameOrIndex: layer name or index
        :type layerNameOrIndex: str or int
        '''

        ApplierIO.__init__(self, filename=filename)
        self._layerNameOrIndex = layerNameOrIndex
        self._dataset = None

    def __repr__(self):
        return '{cls}(filename={filename}, layerNameOrIndex={layerNameOrIndex})'.format(
            cls=self.__class__.__name__,
            filename=str(self.filename()),
            layerNameOrIndex=repr(self._layerNameOrIndex))

    def dataset(self):
        '''Return the :class:`~hubdc.model.Vector` object.'''
        if self._dataset is None:
            self._dataset = openVectorDataset(filename=self.filename(), layerNameOrIndex=self._layerNameOrIndex, update=False)
        return self._dataset

    def _rasterize(self, initValue, burnValue, burnAttribute, allTouched, filterSQL, overlap, dtype, resolution):

        grid = self.operator().subgrid().pixelBuffer(buffer=overlap)
        gridOversampled = Grid(extent=grid.extent(), resolution=resolution)

        dataset = self.dataset().rasterize(grid=gridOversampled, gdalType=NumericTypeCodeToGDALTypeCode(dtype),
                                           initValue=initValue, burnValue=burnValue, burnAttribute=burnAttribute,
                                           allTouched=allTouched,
                                           filterSQL=filterSQL)
        raster = ApplierInputRaster.fromDataset(dataset=dataset)
        raster.setOperator(operator=self.operator())
        return raster

    def array(self, initValue=0, burnValue=1, burnAttribute=None, allTouched=False, filterSQL=None, overlap=0,
              dtype=numpy.float32):
        '''Returns the vector rasterization of the current block in form of a 3-d numpy array of shape = (1, ysize, xsize).

        :param initValue: value to pre-initialize the output array
        :param burnValue: value to burn into the output array for all objects; exclusive with ``burnAttribute``
        :param burnAttribute: identifies an attribute field on the features to be used for a burn-in value; exclusive with ``burnValue``
        :param allTouched: whether to enable that all pixels touched by lines or polygons will be updated, not just those on the line render path, or whose center point is within the polygon
        :param filterSQL: set an SQL WHERE clause which will be used to filter vector features
        :param overlap: the number of pixels to additionally read along each spatial dimension
        '''

        raster = self._rasterize(initValue=initValue, burnValue=burnValue, burnAttribute=burnAttribute,
                                 allTouched=allTouched, filterSQL=filterSQL, overlap=overlap, dtype=dtype,
                                 resolution=self.operator().subgrid().resolution())
        return raster.dataset().readAsArray()

    def fractionArray(self, categories, categoryAttribute=None, oversampling=1, overlap=0):
        '''Returns aggregated category fractions of the current block in form of a 3d numpy array of shape = (categories, ysize, xsize).

        :param categories: list of categories (numbers or names)
        :param categoryAttribute: attribute field on the features holding the categories
        :param oversampling: factor defining the relative degree of rasterization detail compared to the target resolution. If for example the target resolution is 30m and the oversampling factor is 10, then the categories are first rasterized at 3m, and finally aggregated to the target resolution.
        :param overlap: the number of pixels to additionally read along each spatial dimension
        '''

        resolution = Resolution(x=self.operator().subgrid().resolution().x() / float(oversampling),
                                y=self.operator().subgrid().resolution().y() / float(oversampling))

        array = list()
        for category in categories:
            filterSQL = str('"' + categoryAttribute + '" = ' + "'" + str(category) + "'")
            oversampledRaster = self._rasterize(initValue=0, burnValue=1, burnAttribute=None, allTouched=False,
                                                filterSQL=filterSQL,
                                                overlap=overlap * oversampling, dtype=numpy.float32,
                                                resolution=resolution)
            array.append(oversampledRaster.array(overlap=overlap, resampleAlg=gdal.GRA_Average))

        return numpy.vstack(array)

    def coverageFractionArray(self, oversampling=1, overlap=0):
        '''Returns aggregated coverage fractions of the current block in form of a 3d numpy array of shape = (1, ysize, xsize).

        :param oversampling: factor defining the relative degree of rasterization detail compared to the target resolution. If for example the target resolution is 30m and the oversampling factor is 10, then the categories are first rasterized at 3m, and finally aggregated to the target resolution.
        :param overlap: the number of pixels to additionally read along each spatial dimension
        '''

        resolution = Resolution(x=self.operator().subgrid().resolution().x() / float(oversampling),
                                y=self.operator().subgrid().resolution().y() / float(oversampling))

        oversampledRaster = self._rasterize(initValue=0, burnValue=1, burnAttribute=None, allTouched=False,
                                            filterSQL=None,
                                            overlap=overlap * oversampling, dtype=numpy.float32,
                                            resolution=resolution)
        array = oversampledRaster.array(overlap=overlap, resampleAlg=gdal.GRA_Average)

        return array



class ApplierOutputRaster(ApplierIO):
    '''Class for creating and handling an output raster dataset.'''

    def __init__(self, filename, driver=None, creationOptions=None):
        '''
        :param filename: destination filename for output raster
        :param driver:
        :type driver: hubdc.core.RasterDriver
        :param creationOptions: raster creation options
        :type creationOptions: list
        '''

        if driver is None:
            driver = RasterDriver.fromFilename(filename)
        filename = driver.prepareCreation(filename=filename)
        self.driver = driver

        ApplierIO.__init__(self, filename=filename)

        assert isinstance(driver, RasterDriver)
        if creationOptions is None:
            creationOptions = driver.options()
        self.creationOptions = creationOptions
        assert isinstance(self.creationOptions, list)
        self._writerQueue = None
        self._zsize = None

    def __repr__(self):
        return '{cls}(filename={filename}, driver={driver}, creationOptions={creationOptions})'.format(
            cls=self.__class__.__name__,
            filename=str(self.filename()),
            driver=repr(self.driver),
            creationOptions=repr(self.creationOptions))

    def setZsize(self, zsize):
        """Specify the number of output bands. This is only required if the output is written band-wise."""
        self._zsize = zsize

    def zsize(self):
        if self._zsize is None:
            raise errors.ApplierOutputRasterNotInitializedError
        return int(self._zsize)

    def flatList(self):
        '''Returns itself inside a list, i.e. ``[self]``.'''
        return [self]

    def band(self, index):
        '''Returns the :class:`~hubdc.applier.ApplierOutputRasterBand` for the given ``index``.'''

        assert self.zsize() is not None
        return ApplierOutputRasterBand(parent=self, index=index)

    def bands(self):
        '''Returns an iterator over all :class:`~hubdc.applier.ApplierOutputRasterBand`'s.'''

        for index in range(self.zsize()):
            yield self.band(index=index)

    def setArray(self, array, overlap=0):
        """
        Write data to the output raster.

        :param array: 3-d numpy array of shape = (zsize, ysize, xsize) or 2-d numpy array of shape = (ysize, xsize)
        :param overlap: the amount of margin (number of pixels) to be removed from the image data block in each direction;
                        this is useful when the overlap keyword was also used during data reading.
        """

        if not isinstance(array, numpy.ndarray):
            array = numpy.array(array)

        if array.ndim == 2:
            array = array[None]

        if overlap > 0:
            array = array[:, overlap:-overlap, overlap:-overlap]

        self._writerQueue.put(
            (Writer.WRITE_ARRAY, self.filename(), array, self.operator().subgrid(), self.operator().grid(),
             self.driver, self.creationOptions))

        self.setZsize(zsize=len(array))

        return self

    def setMetadataItem(self, key, value, domain):
        '''Set image metadata item.'''

        self._callImageMethod(method=RasterDataset.setMetadataItem, key=key, value=value, domain=domain)

    def setMetadataDict(self, metadataDict):
        '''
        Set metadata dictionary.

        :param metadataDict: dictionary of dictionaries for different metadata domains, e.g. ``{'ENVI': {'wavelength' : [482, 561, 655, 865, 1609, 2201], 'wavelength_units' : 'nanometers', 'band_names' : ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2']}}``
        '''

        assert isinstance(metadataDict, dict)
        for domain in metadataDict:
            assert isinstance(metadataDict[domain], dict)
            for key, value in metadataDict[domain].items():
                self.setMetadataItem(key=key, value=value, domain=domain)

    def setNoDataValue(self, value):
        """Set no data value to all bands."""

        self._callImageMethod(method=RasterDataset.setNoDataValue, value=value)

    def setNoDataValues(self, values):
        """Set no data values."""

        self._callImageMethod(method=RasterDataset.setNoDataValues, values=values)

    def setCategoryColors(self, colors):
        """Set category colors."""

        self.band(index=0)._callMethod(method=RasterBandDataset.setCategoryColors, colors=colors)

    def setCategoryNames(self, names):
        """Set category names."""

        self.band(index=0)._callMethod(method=RasterBandDataset.setCategoryNames, names=names)

    def _callImageMethod(self, method, **kwargs):
        if self.operator().isFirstBlock():
            method = (RasterDataset, method.__name__)
            self._writerQueue.put((Writer.CALL_RASTERMETHOD, self.filename(), method, kwargs))


class ApplierOutputRasterBand(ApplierIO):
    '''Class for handling an output raster band dataset.'''

    def __init__(self, parent, index):
        '''For internal use only.'''
        assert isinstance(parent, ApplierOutputRaster)
        self.parent = parent
        self._index = index

    def setArray(self, array, overlap=0):
        '''
        Write data to the output raster band.

        :param array: 3-d numpy array of shape = (1, ysize, xsize) or 2-d numpy array of shape = (ysize, xsize)
        :param overlap: the amount of margin (number of pixels) to be removed from the image data block in each direction;
                        this is useful when the overlap keyword was also used during data reading.
        '''
        if not isinstance(array, numpy.ndarray):
            array = numpy.array(array)

        if array.ndim == 2:
            array = array[None]

        assert array.shape[0] == 1

        if overlap > 0:
            array = array[:, overlap:-overlap, overlap:-overlap]

        self.parent._writerQueue.put((Writer.WRITE_BANDARRAY, self.parent.filename(), array, self._index,
                                      self.parent.zsize(), self.parent.operator().subgrid(),
                                      self.parent.operator().grid(),
                                      self.parent.driver, self.parent.creationOptions))
        return self

    def _callMethod(self, method, **kwargs):
        if self.parent.operator().isFirstBlock():
            method = (RasterBandDataset, method.__name__)
            self.parent._writerQueue.put(
                (Writer.CALL_BANDMETHOD, self.parent.filename(), self._index, method, kwargs))

    def setDescription(self, value):
        '''Set band description.'''
        self._callMethod(method=RasterBandDataset.setDescription, value=value)

    def setMetadataItem(self, key, value, domain=''):
        """Set metadata item."""
        self._callMethod(method=RasterBandDataset.setMetadataItem, key=key, value=value, domain=domain)

    def setNoDataValue(self, value):
        """Set no data value."""
        self._callMethod(method=RasterBandDataset.setNoDataValue, value=value)

    def setCategoryNames(self, names):
        '''Set band category names.'''
        self._callMethod(method=RasterBandDataset.setCategoryNames, names=names)

    def setCategoryColors(self, colors):
        '''Set band category colors from list of rgba tuples.'''
        self._callMethod(method=RasterBandDataset.setCategoryColors, colors=colors)


class ApplierIOGroup(object):
    def __init__(self):
        self.items = dict()
        self._operator = None

    def __repr__(self, key='ApplierIOGroup()', indent=0):
        space = 2
        result = '{indent}{key}\n'.format(indent=' ' * indent, key=key)
        for k, v in self.items.items():
            if isinstance(v, ApplierIOGroup):
                result += v.__repr__(key=k, indent=indent + space)
            else:
                result += '{indent}{k} : '.format(indent=' ' * (indent + space), k=k)
                result += repr(v) + '\n'
        return result

    def operator(self):
        assert isinstance(self._operator, ApplierOperator)
        return self._operator

    def setOperator(self, operator):
        assert isinstance(operator, ApplierOperator)
        self._operator = operator
        for item in self.items.values():
            item.setOperator(operator=self._operator)

    def _freeUnpickableResources(self):
        for item in self.items.values():
            item._freeUnpickableResources()

    def _flatValues(self):
        result = list()
        for value in self.items.values():
            if isinstance(value, self.__class__):
                result.extend(value._flatValues())
            else:
                result.append(value)
        return result

    def _flatKeys(self):
        result = list()
        for key, value in self.items.items():
            if isinstance(value, self.__class__):
                result.extend(['{}/{}'.format(key, key2) for key2 in value._flatKeys()])
            else:
                result.append(key)
        return result

    def setGroup(self, key, value):
        assert isinstance(value, self.__class__)

        keys = key.split('/')
        subgroup = self
        for k in keys[:-1]:
            subgroup.items[k] = subgroup.items.get(k, self.__class__())
            subgroup = subgroup.items[k]
        k = keys[-1]
        subgroup.items[k] = value
        return subgroup.items[k]

    def group(self, key):
        groupkeys = key.split('/')
        group = self
        for groupkey in groupkeys:
            group = group.items[groupkey]
        assert isinstance(group, self.__class__)
        return group

    def _setItem(self, key, value):
        subkeys = key.split('/')
        groupkeys, iokey = subkeys[:-1], subkeys[-1]
        group = self
        for groupkey in groupkeys:
            group.items[groupkey] = group.items.get(groupkey, self.__class__())
            group = group.items[groupkey]
        group.items[iokey] = value
        return group.items[iokey]

    def _item(self, key):
        subkeys = key.split('/')
        groupkeys, iokey = subkeys[:-1], subkeys[-1]
        group = self
        for groupkey in groupkeys:
            group = group.items[groupkey]
        value = group.items[iokey]
        return value


class ApplierInputRasterGroup(ApplierIOGroup):
    '''Container for :class:`~hubdc.applier.ApplierInputRaster` and :class:`~hubdc.applier.ApplierInputRasterGroup` objects.'''

    @classmethod
    def fromFolder(cls, folder, extensions, ufunc=None):
        '''
        Returns an input raster group containing all input rasters that are located relativ to the given ``folder``,
        matches one of the file ``extensions``, and (optionally) matches the user defined filter ``ufunc(dirname, basename, extension)``.
        In the result, the file system folder structure is preserved.

        :param folder: root folder
        :param extensions: only rasters that matches one of the given extensions are included, e.g. ['', '.bsq', '.tif', '.vrt'].
        :param ufunc: function of form ``ufunc(dirname, basename, extension)``; only files that pass the filter function (i.e. return True) are included
        '''
        assert isinstance(extensions, list)

        def abspath_split(path):

            drive, path_and_file = splitdrive(path)
            folders = []
            while 1:
                path, folder = split(path)

                if folder != "":
                    folders.append(folder)
                else:
                    break
            return list(reversed(folders))

        # off = len(os.path._abspath_split(folder)[2]) # Python 2
        off = len(abspath_split(folder)) # Python 3

        group = ApplierInputRasterGroup()
        for root, dirs, files in walk(folder):
            # key = '/'.join(os.path._abspath_split(root)[2][off:]) # Python 2
            key = '/'.join(abspath_split(root)[off:]) # Python 3

            if key == '':
                subgroup = group
            else:
                subgroup = group.group(key=key)
            for dir in dirs:
                subgroup.setGroup(key=dir, value=ApplierInputRasterGroup())
            for file in files:
                fileBasenameWithoutExtension, fileExtension = splitext(file)
                for extension in extensions:
                    if extension != '': assert extension[0] == '.'
                    if fileExtension.lower() != extension.lower():
                        continue
                    if ufunc is not None:
                        if not ufunc(dirname=root, basename=fileBasenameWithoutExtension, extension=fileExtension):
                            continue
                    subgroup.setRaster(key=fileBasenameWithoutExtension,
                                       value=ApplierInputRaster(filename=join(root, file)))
        return group

    #@staticmethod
    #def fromIndex(index):
    #    '''Returns an input raster group containing all input rasters contained in the :class:`~hubdc.applier.ApplierInputRasterIndex` given by ``index``.'''
    #
    #    assert isinstance(index, ApplierInputRasterIndex)
    #    group = ApplierInputRasterGroup()
    #    for key, filename, extent in zip(index._keys, index._filenames, index._extents):
    #        group.setRaster(key=key, value=ApplierInputRaster(filename=filename))
    #    return group

    def setRaster(self, key, value):
        '''Add an :class:`~hubdc.applier.ApplierInputRaster` given by ``value`` and named ``key``.'''

        assert isinstance(value, ApplierInputRaster)
        return ApplierIOGroup._setItem(self, key=key, value=value)

    def raster(self, key):
        '''Returns the :class:`~hubdc.applier.ApplierInputRaster` named ``key``.'''

        value = ApplierIOGroup._item(self, key=key)
        assert isinstance(value, ApplierInputRaster), value
        return value

    def flatRasters(self):
        '''Returns an iterator over all contained :class:`~hubdc.applier.ApplierInputRaster`'s. Traverses the group structure recursively.'''
        for input in ApplierIOGroup._flatValues(self):
            assert isinstance(input, ApplierInputRaster)
            yield input

    def flatRasterKeys(self):
        '''Returns an iterator over the keys of all contained :class:`~hubdc.applier.ApplierInputRaster`'s. Traverses the group structure recursively.'''
        for key in ApplierIOGroup._flatKeys(self):
            yield key

    def groups(self):
        '''Returns an iterator over all directly contained :class:`~hubdc.applier.ApplierInputRasterGroups`'s. No recursion.'''

        for v in self.items.values():
            if isinstance(v, ApplierInputRasterGroup):
                yield v

    def groupKeys(self):
        '''Returns an iterator over the keys of all directly contained :class:`~hubdc.applier.ApplierInputRasterGroups`'s. No recursion.'''

        for k, v in self.items.items():
            if isinstance(v, ApplierInputRasterGroup):
                yield k

    def rasters(self):
        '''Returns an iterator over all directly contained :class:`~hubdc.applier.ApplierInputRaster`'s. No recursion.'''

        for v in self.items.values():
            if isinstance(v, ApplierInputRaster):
                yield v

    def rasterKeys(self):
        '''Returns an iterator over the keys of all directly contained :class:`~hubdc.applier.ApplierInputRaster`'s. No recursion.'''

        for k, v in self.items.items():
            if isinstance(v, ApplierInputRaster):
                assert isinstance(k, str)
                yield k

    def findRaster(self, ufunc=lambda key, raster: False):
        '''Returns the first :class:`~hubdc.applier.ApplierInputRaster` for that the user defined function ``ufunc(key, raster)`` matches.
        Returns None in case of no match.'''

        for key in self.rasterKeys():
            raster = self.raster(key=key)
            if ufunc(key=key, raster=raster):
                return raster
        return None

    def findRasterKey(self, ufunc=lambda key, raster: False):
        '''Returns the first key for that the user defined function ``ufunc(key, raster)`` matches.
        Returns None in case of no match.'''

        for key in self.rasterKeys():
            raster = self.raster(key=key)
            if ufunc(key=key, raster=raster):
                return key
        return None

'''
class ApplierInputRasterIndex(object):
    WGS84 = Projection.wgs84()

    def __init__(self):
        self._keys = list()
        self._filenames = list()
        self._extents = list()

    def __repr__(self):

        result = 'ApplierInputRasterIndex\n'
        for key, filename, extent in zip(self._keys, self._filenames, self._extents):
            result += '  {} : {} {}\n'.format(key, filename, extent)
        return result

    @staticmethod
    def fromFolder(folder, extensions, ufunc=None):
        group = ApplierInputRasterGroup.fromFolder(folder=folder, extensions=extensions, ufunc=ufunc)
        index = ApplierInputRasterIndex()
        for key in group.flatRasterKeys():
            index.insertRaster(key=key, raster=group.raster(key=key))
        return index

    @staticmethod
    def unpickle(filename):
        with open(filename, 'rb') as f:
            index = pickle.load(file=f)
        assert isinstance(index, ApplierInputRasterIndex)
        return index

    def pickle(self, filename):
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'wb') as f:
            pickle.dump(obj=self, file=f, protocol=1)

    def insertRaster(self, key, raster):
        assert isinstance(raster, ApplierInputRaster)
        extent = raster.dataset().grid().spatialExtent().reproject(projection=self.WGS84)
        self.insertFilename(key=key, filename=raster.filename(), extent=extent)

    def insertFilename(self, key, filename, extent):
        self._keys.append(key)
        self._filenames.append(filename)
        self._extents.append(extent)

    def intersection(self, grid):
        assert isinstance(grid, Grid)

        gridExtent = grid.spatialExtent().reproject(projection=self.WGS84)

        index = ApplierInputRasterIndex()

        for key, filename, extent in zip(self._keys, self._filenames, self._extents):
            if extent.intersects(gridExtent):
                index.insertFilename(key=key, filename=filename, extent=extent)

        return index
'''

class ApplierInputVectorGroup(ApplierIOGroup):
    '''Container for :class:`~hubdc.applier.ApplierInputVector` and :class:`~hubdc.applier.ApplierInputVectorGroup` objects.'''

    def setVector(self, key, value):
        '''Add an :class:`~hubdc.applier.ApplierInputVector` given by ``value`` and named ``key``.'''

        assert isinstance(value, ApplierInputVector)
        return ApplierIOGroup._setItem(self, key=key, value=value)

    def vector(self, key):
        '''Returns the :class:`~hubdc.applier.ApplierInputVector` named ``key``.'''

        value = ApplierIOGroup._item(self, key=key)
        assert isinstance(value, ApplierInputVector)
        return value

    def flatVectors(self):
        '''Returns an iterator over all contained :class:`~hubdc.applier.ApplierInputVector`'s. Traverses the group structure recursively.'''
        for input in ApplierIOGroup._flatValues(self):
            assert isinstance(input, ApplierInputVector)
            yield input

    def flatVectorKeys(self):
        '''Returns an iterator over the keys of all contained :class:`~hubdc.applier.ApplierInputVectors`'s. Traverses the group structure recursively.'''
        for input in ApplierIOGroup._flatKeys(self):
            assert isinstance(input, str)
            yield input

    def groups(self):
        '''Returns an iterator over all directly contained :class:`~hubdc.applier.ApplierInputVectorGroups`'s. No recursion.'''

        for v in self.items.values():
            if isinstance(v, ApplierInputVectorGroup):
                yield v

    def groupKeys(self):
        '''Returns an iterator over the keys of all directly contained :class:`~hubdc.applier.ApplierInputVectorGroups`'s. No recursion.'''

        for k, v in self.items.items():
            if isinstance(v, ApplierInputVectorGroup):
                yield k


class ApplierOutputRasterGroup(ApplierIOGroup):
    '''Container for :class:`~hubdc.applier.ApplierOutputRaster` and :class:`~hubdc.applier.ApplierOutputRasterGroup` objects.'''

    def setRaster(self, key, value):
        '''Add an :class:`~hubdc.applier.ApplierOutputRaster` given by ``value`` and named ``key``.'''

        assert isinstance(value, ApplierOutputRaster)
        return ApplierIOGroup._setItem(self, key=key, value=value)

    def raster(self, key):
        '''Returns the :class:`~hubdc.applier.ApplierOutputRaster` named ``key``.'''

        value = ApplierIOGroup._item(self, key=key)
        assert isinstance(value, ApplierOutputRaster)
        return value

    def flatRasters(self):
        '''Returns an iterator over all contained :class:`~hubdc.applier.ApplierOutputRaster`'s. Traverses the group structure recursively.'''

        for v in self._flatValues():
            assert isinstance(v, ApplierOutputRaster)
            yield v

    def flatRasterKeys(self):
        '''Returns an iterator over the keys of all contained :class:`~hubdc.applier.ApplierOutputRaster`'s. Traverses the group structure recursively.'''

        for key in ApplierIOGroup._flatKeys(self):
            assert isinstance(key, str)
            yield key


class Applier(object):
    '''
    This class is the main point of entry in this module.

    Attributes and properties are:
        * **inputRaster**          :class:`~hubdc.applier.ApplierInputRasterGroup` object containing all input rasters
        * **inputRasterArchive**   :class:`~hubdc.applier.ApplierInputRasterArchiveGroup` object containing all input raster archieves
        * **inputVector**          :class:`~hubdc.applier.ApplierInputVectorGroup` object containing all input vectors
        * **outputRaster**         :class:`~hubdc.applier.ApplierOutputRasterGroup` object containing all output rasters
        * **controls**             :class:`~hubdc.applier.ApplierControls` object containing all input rasters
        * **mainGrid**             :class:`~hubdc.model.Grid` object
    '''

    def __init__(self, controls=None):
        '''
        :param controls: an :class:`~hubdc.applier.ApplierControls` object
        '''

        self.inputRaster = ApplierInputRasterGroup()
        self.inputVector = ApplierInputVectorGroup()
        self.outputRaster = ApplierOutputRasterGroup()
        self.controls = controls if controls is not None else ApplierControls()
        self._grid = None

    def grid(self):
        '''Returns the output :class:`~hubdc.model.Grid` object.'''

        assert isinstance(self._grid, Grid)
        return self._grid

    def apply(self, operatorType=None, operatorFunction=None, description=None, overwrite=True, *ufuncArgs,
              **ufuncKwargs):
        """
        Applies the ``operator`` blockwise over a raster processing chain and returns a list of results, one for each block.

        The ``operator`` must be a subclass of :class:`~hubdc.applier.ApplierOperator` and needs to implement the
        :meth:`~hubdc.applier.ApplierOperator.ufunc` method to specify the image processing.

        For example::

            class MyOperator(ApplierOperator):
                def ufunc(self):
                    # process the data

            applier.apply(operator=MyOperator)


        :param description: short description that is displayed on the progress bar
        :param ufuncArgs: additional arguments that will be passed to the operators ufunc() method.
        :param ufuncKwargs: additional keyword arguments that will be passed to the operators ufunc() method.
        :return: list of results, one for each processed block
        """

        if isinstance(operatorType, type):
            self.operatorType = operatorType
            self.operatorUFunc = None
        elif callable(operatorFunction):
            self.operatorType = ApplierOperator
            self.operatorUFunc = operatorFunction
        else:
            raise errors.ApplierOperatorTypeError()

        if description is None:
            description = self.operatorType.__name__

        if not overwrite:
            allExists = all([exists(raster.filename()) for raster in self.outputRaster.flatRasters()])
            if allExists:
                self.controls.progressBar.setText('skip {} (all outputs exist and OVERWRITE=FALSE)'.format(description))
                return

        self.ufuncArgs = ufuncArgs
        self.ufuncKwargs = ufuncKwargs

        runT0 = now()
        self._grid = self.controls.deriveGrid(inputRasterGroup=self.inputRaster)

        self.controls.progressBar.setText(
            'start {}, {}'.format(description.lstrip('_'), self.grid().size()))


        self._runInitWriters()
        self._runInitPool()
        results = self._runProcessSubgrids()
        self._runClose()
        self.controls.progressBar.setPercentage(percentage=100)
        if self.controls.progressCallback is not None:
            self.controls.progressCallback(100)

        s = (now() - runT0)
        m = s / 60
        h = m / 60

        self.controls.progressBar.setText(
            'done {description} in {s} sec | {m}  min | {h} hours'.format(description=description.lstrip('_'),
                                                                          s=int(s), m=round(m, 2), h=round(h, 2)))
        return results

    def _runInitWriters(self):
        self.writers = list()
        self.queues = list()
        self.queueMock = QueueMock()
        if self.controls._multiwriting:

            for w in range(self.controls.nwriter if self.controls.nwriter is not None else 1):
                w = WriterProcess()
                w.start()
                self.writers.append(w)
                self.queues.append(w.queue)
        self._assignQueues()

    def _runInitPool(self):
        if self.controls._multiprocessing:
            # exclude non-pickable members
            # - writers arn't pickable, need to detache them before passing self to Pool initializer
            writers, self.writers = self.writers, None
            # - free cached gdal datasets
            self.inputRaster._freeUnpickableResources()
            self.pool = Pool(processes=self.controls.nworker, initializer=_pickableWorkerInitialize, initargs=(self,))
            self.writers = writers  # put writers back
        else:
            _Worker.initialize(applier=self)

    def _runProcessSubgrids(self):

        n = ny = nx = 0
        subgrids = self.grid().subgrids(size=self.controls.blockSize)
        _, n, ny, nx = subgrids[-1]

        self.nsubgrids = n
        if self.controls._multiprocessing:
            applyResults = list()
        else:
            blockResults = list()

        for subgrid, i, iy, ix in subgrids:
            kwargs = {'i': i,
                      'n': len(subgrids),
                      'iy': iy,
                      'ix': ix,
                      'ny': ny,
                      'nx': nx,
                      'workingGrid': subgrid}

            if self.controls._multiprocessing:
                applyResults.append(self.pool.apply_async(func=_pickableWorkerProcessSubgrid, kwds=kwargs))
            else:
                blockResults.append(_Worker.processSubgrid(**kwargs))

        if self.controls._multiprocessing:
            blockResults = [applyResult.get() for applyResult in applyResults]

        result = self.operatorType.aggregate(blockResults=blockResults, grid=self.grid(), *self.ufuncArgs, **self.ufuncKwargs)
        return result

    def _assignQueues(self):

        def lessFilledQueue():
            lfq = self.queues[0]
            for q in self.queues:
                if lfq.qsize() > q.qsize():
                    lfq = q
            return lfq

        for output in self.outputRaster.flatRasters():
            assert isinstance(output, ApplierOutputRaster)
            if self.controls._multiwriting:
                output._writerQueue = lessFilledQueue()
            else:
                output._writerQueue = self.queueMock

    def _runClose(self):
        if self.controls._multiprocessing:
            self.pool.close()
            self.pool.join()

        if self.controls._multiwriting:
            for writer in self.writers:
                writer.queue.put([Writer.CLOSE_RASTERS, self.controls.createEnviHeader])
                writer.queue.put([Writer.CLOSE_WRITER, None])
                writer.join()
        else:
            self.queueMock.put([Writer.CLOSE_RASTERS, self.controls.createEnviHeader])


class _Worker(object):
    """
    For internal use only.
    """

    # queues = list()
    inputRaster = None
    inputVector = None
    outputRaster = None
    applier = None
    operator = None

    def __init__(self):
        raise Exception('singleton class')

    @classmethod
    def initialize(cls, applier):
        gdal.SetCacheMax(applier.controls.cacheMax)
        gdal.SetConfigOption('GDAL_SWATH_SIZE', str(applier.controls.swathSize))
        gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', str(applier.controls.disableReadDirOnOpen))
        gdal.SetConfigOption('GDAL_MAX_DATASET_POOL_SIZE', str(applier.controls.maxDatasetPoolSize))

        assert isinstance(applier, Applier)
        cls.applier = applier
        cls.inputRaster = applier.inputRaster
        cls.inputVector = applier.inputVector
        cls.outputRaster = applier.outputRaster

        # create operator
        cls.operator = applier.operatorType(mainGrid=applier.grid(),
                                            inputRaster=cls.inputRaster,
                                            inputVector=cls.inputVector,
                                            outputRaster=cls.outputRaster,
                                            controls=applier.controls,
                                            operatorUFunc=applier.operatorUFunc, ufuncArgs=applier.ufuncArgs,
                                            ufuncKwargs=applier.ufuncKwargs)

    @classmethod
    def processSubgrid(cls, i, n, iy, ix, ny, nx, workingGrid):
        percent = float(i) / n * 100
        cls.operator.progressBar.setPercentage(percent)
        if cls.operator._controls.progressCallback is not None:
            cls.operator._controls.progressCallback(percent)

        return cls.operator._apply(workingGrid=workingGrid, iblock=i, nblock=n, yblock=iy, xblock=ix, nyblock=ny,
                                   nxblock=nx)


def _pickableWorkerProcessSubgrid(**kwargs):
    return _Worker.processSubgrid(**kwargs)


def _pickableWorkerInitialize(*args):
    return _Worker.initialize(*args)


class ApplierOperator(object):
    """
    This is the baseclass for an user defined applier operator.
    For details on user defined operators see :meth:`hubdc.applier.Applier.apply`
    """

    def __init__(self, mainGrid, inputRaster, inputVector, outputRaster,
                 controls, ufuncArgs, ufuncKwargs, operatorUFunc=None):
        assert isinstance(mainGrid, Grid)
        assert isinstance(inputRaster, ApplierInputRasterGroup)
        assert isinstance(inputVector, ApplierInputVectorGroup)
        assert isinstance(outputRaster, ApplierOutputRasterGroup)
        assert isinstance(controls, ApplierControls)

        self._subgrid = None
        self._grid = mainGrid

        self.inputRaster = inputRaster
        self.inputVector = inputVector
        self.outputRaster = outputRaster

        self.inputRaster.setOperator(operator=self)
        self.inputVector.setOperator(operator=self)
        self.outputRaster.setOperator(operator=self)

        self._controls = controls
        self._ufuncArgs = ufuncArgs
        self._ufuncKwargs = ufuncKwargs
        self._ufuncFunction = operatorUFunc
        self._iblock = 0
        self._nblock = 0

    def subgrid(self):
        """
        Returns the current block :class:`~hubdc.applier.Grid`.
        """
        assert isinstance(self._subgrid, Grid)
        return self._subgrid

    def grid(self):
        """
        Returns the :class:`~hubdc.applier.Grid`.
        """
        assert isinstance(self._grid, Grid)
        return self._grid

    def _setWorkingGrid(self, grid):
        assert isinstance(grid, Grid)
        self._subgrid = grid

    @property
    def progressBar(self):
        """
        Returns the :class:`~hubdc.progressbar.ProgressBar`.
        """
        return self._controls.progressBar

    def isFirstBlock(self):
        """
        Returns wether or not the current block is the first one.
        """
        return self._iblock == 0

    def isLastBlock(self):
        """
        Returns wether or not the current block is the last one.
        """
        return self._iblock == self.nblock() - 1

    def isLastYBlock(self):
        """
        Returns wether or not the current block is the last block in y direction.
        """
        return self._yblock == self.nyblock() - 1

    def isLastXBlock(self):
        """
        Returns wether or not the current block is the last block in x direction.
        """
        return self._xblock == self.nxblock() - 1

    def iblock(self):
        return self._iblock

    def nblock(self):
        return self._nblock

    def yblock(self):
        return self._yblock

    def xblock(self):
        return self._xblock

    def nyblock(self):
        return self._nyblock

    def nxblock(self):
        return self._nxblock

    def yblockSize(self):
        return self.subgrid().shape()[0]

    def xblockSize(self):
        return self.subgrid().shape()[1]

    def yblockOffset(self):
        return self.yblock() * self.yblockSize()

    def xblockOffset(self):
        return self.xblock() * self.xblockSize()

    def full(self, value, bands=1, dtype=None, overlap=0):
        '''Returns a 3-d numpy array of shape = (zsize, ysize+2*overlap, xsize+2*overlap) filled with constant ``value``
        or list of values, one for each band.'''
        if isinstance(value, list):
            array = [numpy.full(shape=(self.subgrid().size().y() + 2 * overlap,
                                       self.subgrid().size().x() + 2 * overlap),
                                fill_value=v, dtype=dtype) for v in value]
            array = np.array(array)
        else:
            array = numpy.full(shape=(bands,
                                      self.subgrid().size().y() + 2 * overlap,
                                      self.subgrid().size().x() + 2 * overlap),
                               fill_value=value, dtype=dtype)
        return array

    def _apply(self, workingGrid, iblock, nblock, yblock, xblock, nyblock, nxblock):
        self._iblock = iblock
        self._nblock = nblock
        self._yblock = yblock
        self._xblock = xblock
        self._nyblock = nyblock
        self._nxblock = nxblock

        self._setWorkingGrid(workingGrid)
        blockResult = self.ufunc(*self._ufuncArgs, **self._ufuncKwargs)
        return blockResult

    def ufunc(self, *args, **kwargs):
        '''Overwrite this method to specify the image processing.'''

        blockResults = self._ufuncFunction(self, *args, **kwargs)
        result = self.aggregate(blockResults=blockResults, grid=self.grid())
        return result

    @staticmethod
    def aggregate(blockResults, grid, *args, **kwargs):
        '''
        Overwrite this method to specify how to aggregate the list of block-wise return values.
        '''
        return blockResults


class ApplierControls(object):
    '''Class for controlling various details of the applier processing.'''

    def __init__(self):

        self.setBlockSize()
        self.setNumThreads()
        self.setNumWriter()
        self.setWriteENVIHeader(createEnviHeader=False)
        self.setAutoExtent()
        self.setAutoResolution()
        self.setResolution()
        self.setExtent()
        self.setProjection()
        self.setGrid()
        self.setGDALCacheMax()
        self.setGDALSwathSize()
        self.setGDALDisableReadDirOnOpen()
        self.setGDALMaxDatasetPoolSize()
        self.setProgressBar()
        self.setProgressCallback()

    def setProgressBar(self, progressBar=None):
        """
        Set the progress display object. Default is an :class:`~hubdc.progressbar.CUIProgress` object.
        For suppressing outputs use an :class:`~hubdc.progressbar.SilentProgress` object
        """
        if progressBar is None:
            progressBar = CUIProgressBar()

        self.progressBar = progressBar
        return self

    def setProgressCallback(self, progressCallback=None):
        """
        Set the progress callback function, a function with one argument named ``percent``, that is called each time the applier finishes a block.
        """
        self.progressCallback = None
        return self

    def setBlockSize(self, blockSize=ApplierDefaults.blockSize):
        '''
        Set the processing block x and y size. Pass an int defining x and y size to be the same,
        or a tuple (int, int) defining x and y size separately,
        or a :class:`~hubdc.model.Size` object.
        '''

        if isinstance(blockSize, int):
            blockSize = RasterSize(*[blockSize] * 2)
        elif isinstance(blockSize, (tuple, list)) and len(blockSize) == 2:
            blockSize = RasterSize(*blockSize)
        elif isinstance(blockSize, RasterSize):
            pass
        else:
            raise ValueError('not a valid block size')
        self.blockSize = blockSize
        return self

    def setBlockFullSize(self):
        """
        Set the block size to full extent.
        """

        veryLargeNumber = 10 ** 20
        self.setBlockSize(veryLargeNumber)
        return self

    def setNumThreads(self, nworker=ApplierDefaults.nworker):
        """
        Set the number of pool worker for multiprocessing. Set to None to disable multiprocessing (recommended for debugging).
        Set to -1 to use all CPUs.
        """
        if nworker == -1:
            nworker = cpu_count()

        self.nworker = nworker
        return self

    def setNumWriter(self, nwriter=ApplierDefaults.nwriter):
        """
        Set the number of writer processes. Set to None to disable multiwriting (recommended for debugging).
        """

        self.nwriter = nwriter
        return self

    def setWriteENVIHeader(self, createEnviHeader=ApplierDefaults.writeENVIHeader):
        """
        Set to True to create additional ENVI header files for all output rasters.
        The header files store all metadata items from the ENVI domain,
        so that the images can be correctly interpreted by the ENVI software.
        Currently only the native ENVI format and the GTiff format is supported.
        """

        self.createEnviHeader = createEnviHeader
        return self

    def setAutoExtent(self, autoExtent=ApplierDefaults.autoExtent):
        """
        Define how the grid extent is derived from the input rasters.
        Possible options are listed in :class:`~hubdc.applier.Options.AutoExtent`.
        """

        if autoExtent not in ApplierOptions.AutoExtent.__dict__.values():
            raise errors.UnknownApplierAutoExtentOption
        self.autoExtent = autoExtent

        return self

    def setAutoResolution(self, autoResolution=ApplierDefaults.autoResolution):
        """
        Define how the grid resolution is derived from the input rasters.
        Possible options are listed in :class:`~hubdc.applier.Options.AutoResolution`.
        """

        if autoResolution not in ApplierOptions.AutoResolution.__dict__.values():
            raise errors.UnknownApplierAutoResolutionOption
        self.autoResolution = autoResolution
        return self

    def setResolution(self, resolution=None):
        '''
        Set the applier resolution.
        Pass a float defining x and y resolution to be the same,
        or a (float, float) tuple defining x and y resolution separately,
        or a :class:`~hubdc.model.Resolution` object,
        or None (default) to derive the resolution from the input rasters.
        '''

        if resolution is None:
            pass
        elif isinstance(resolution, Resolution):
            pass
        elif isinstance(resolution, (int, float)):
            resolution = Resolution(*[resolution] * 2)
        elif (isinstance(resolution, (tuple, list)) and len(resolution) == 2 and
                  isinstance(resolution[0], (int, float)) and isinstance(resolution[1], (int, float))):
            resolution = Resolution(*resolution)
        else:
            raise ValueError('not a valid resolution')
        self.resolution = resolution
        return self

    def setExtent(self, extent=None):
        """
        Set the applier extent.
        Pass a (float, float, float, float) tuple defining the extent as (xMin, xMax, yMin, yMax),
        or an :class:`~hubdc.model.Extent` object,
        or None (default) to derive the extent from the input rasters.
        """

        if not isinstance(extent, (Extent, type(None))):
            raise errors.TypeError(extent)
        self.extent = extent
        return self

    def setProjection(self, projection=None):
        '''Set the applier projection (default is projection shared by all input rasters.'''

        if not isinstance(projection, (Projection, type(None))):
            raise errors.TypeError(projection)
        self.projection = projection
        return self

    def setGrid(self, grid=None):
        '''Set the applier grid (default is grid derived from the input rasters.'''

        if grid is None:
            self.setExtent()
            self.setResolution()
            self.setProjection()
        elif isinstance(grid, Grid):
            self.setExtent(extent=grid.extent())
            self.setResolution(resolution=grid.resolution())
            self.setProjection(projection=grid.projection())
        else:
            raise errors.TypeError(grid)
        return self

    def setGDALCacheMax(self, bytes=ApplierDefaults.GDALEnv.cacheMax):
        self.cacheMax = bytes
        return self

    def setGDALSwathSize(self, bytes=ApplierDefaults.GDALEnv.swathSize):
        self.swathSize = bytes
        return self

    def setGDALDisableReadDirOnOpen(self, disable=ApplierDefaults.GDALEnv.disableReadDirOnOpen):
        self.disableReadDirOnOpen = disable
        return self

    def setGDALMaxDatasetPoolSize(self, nfiles=ApplierDefaults.GDALEnv.maxDatasetPoolSize):
        self.maxDatasetPoolSize = nfiles
        return self

    @property
    def _multiprocessing(self):
        return self.nworker is not None

    @property
    def _multiwriting(self):
        return self._multiprocessing or (self.nwriter is not None)

    def deriveGrid(self, inputRasterGroup):
        '''Derives the grid from the given :class:`~hubdc.applier.ApplierInputRasterGroup`'s.'''
        assert isinstance(inputRasterGroup, ApplierInputRasterGroup)
        grids = [inputRaster.dataset().grid() for inputRaster in inputRasterGroup.flatRasters()]
        projection = self.deriveProjection(grids)
        return Grid(extent=self.deriveExtent(grids, projection),
                    resolution=self.deriveResolution(grids))

    def deriveProjection(self, grids):
        '''Derives the projection from the given grids.'''

        if self.projection is None:
            if len(grids) == 0:
                raise errors.MissingApplierProjectionError()
            projection = grids[0].projection()
            for grid in grids:
                if not grid.projection().equal(other=projection):
                    raise errors.MissingApplierProjectionError()
        else:
            projection = self.projection
        return projection

    def deriveExtent(self, grids, projection):
        '''Derives the extent from the given grids in the given projection.'''

        if self.extent is None:

            if len(grids) == 0:
                raise errors.MissingApplierExtentError()

            extent = grids[0].extent().reproject(projection=projection)

            for grid in grids:
                extent_ = grid.extent().reproject(projection=projection)
                if self.autoExtent == ApplierOptions.AutoExtent.union:
                    extent = extent.union(other=extent_)
                elif self.autoExtent == ApplierOptions.AutoExtent.intersection:
                    extent = extent.intersection(other=extent_)
                else:
                    raise errors.UnknownApplierAutoExtentOption()

        else:
            extent = self.extent

        return extent

    def deriveResolution(self, grids):
        '''Derives the resolution from the given :class:`~hubdc.model.Grid`.'''

        if self.resolution is None:

            if len(grids) == 0:
                raise errors.MissingApplierResolutionError()


            if self.autoResolution == ApplierOptions.AutoResolution.minimum:
                f = numpy.min
            elif self.autoResolution == ApplierOptions.AutoResolution.maximum:
                f = numpy.max
            elif self.autoResolution == ApplierOptions.AutoResolution.average:
                f = numpy.mean
            else:
                raise errors.UnknownApplierAutoResolutionOption()
            resolution = Resolution(x=f([grid.resolution().x() for grid in grids]),
                                    y=f([grid.resolution().y() for grid in grids]))

        else:
            resolution = self.resolution

        return resolution
