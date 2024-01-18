from collections import OrderedDict, namedtuple
from os import makedirs, remove, listdir
from os.path import dirname, exists, join, basename, splitext
import copy
from shutil import copyfile, rmtree
import datetime
from random import randint
import tempfile
from osgeo import gdal, gdal_array, ogr, osr
import numpy as np
from sklearn.base import ClassifierMixin
import _classic.hubdc.hubdcerrors as errors
import _classic.hubflow.core as hfc

gdal.UseExceptions()

CACHE = dict()


class Projection(object):
    '''Class for managing projections.'''

    def __init__(self, wkt):
        '''Create by given well known text string.'''
        self._wkt = str(wkt)

    def __repr__(self):
        wkt = self.wkt().replace(' ', '').replace('\n', ' ')
        return '{cls}(wkt={wkt})'.format(cls=self.__class__.__name__, wkt=wkt)

    def wkt(self):
        '''Returns the well known text string.'''
        return self._wkt

    @staticmethod
    def fromEPSG(epsg):
        '''Create by given ``epsg`` authority ID.'''
        projection = osr.SpatialReference()
        projection.ImportFromEPSG(int(epsg))
        return Projection(wkt=projection)

    @staticmethod
    def WGS84WebMercator():
        '''Create WGS84 Web Mercator projection (epsg=3857)'''
        return Projection.fromEPSG(epsg=3857)

    @staticmethod
    def WGS84():
        '''Create WGS84 projection (epsg=4326)'''
        return Projection.fromEPSG(epsg=4326)

    @classmethod
    def UTM(cls, zone, north=True):
        '''Create UTM projection of given ``zone``.'''
        assert zone >= 1 and zone <= 60
        if north:
            return cls.fromEPSG(epsg=32600 + zone)
        else:
            return cls.fromEPSG(epsg=32700 + zone)

    def osrSpatialReference(self):
        '''Returns osr.SpatialReference object.'''
        srs = osr.SpatialReference()
        srs.ImportFromWkt(self.wkt())
        return srs

    def equal(self, other):
        '''Returns whether self is equal to other.'''

        assert isinstance(other, Projection)
        return bool(self.osrSpatialReference().IsSame(other.osrSpatialReference()))


class Resolution(object):
    '''Class for managing pixel resolutions.'''

    def __init__(self, x, y=None):
        '''
        :param x: resolution in x dimension
        :type x: float > 0
        :param y: resolution in y dimension
        :type y: float > 0
        '''

        if y is None:
            if isinstance(x, (int, float)):
                y = x
            elif isinstance(x, (list, tuple)):
                assert len(x) == 2
                x, y = x[0], x[1]
            else:
                assert 0

        self._x = float(x)
        self._y = float(y)
        assert self._x > 0
        assert self._y > 0

    def __repr__(self):
        return '{cls}(x={x}, y={y})'.format(cls=self.__class__.__name__, x=repr(self.x()), y=repr(self.y()))

    def __truediv__(self, other):

        if isinstance(other, (int, float)):
            fx = fy = other
        elif len(other) == 2:
            fx, fy = other
        else:
            assert 0

        return Resolution(x=self.x()/fx, y=self.y()/fy)

    def __mul__(self, other):

        if isinstance(other, (int, float)):
            fx = fy = other
        elif len(other) == 2:
            fx, fy = other
        else:
            assert 0

        return Resolution(x=self.x()*fx, y=self.y()*fy)


    @staticmethod
    def parse(obj):
        if isinstance(obj, Resolution):
            resolution = obj
        elif isinstance(obj, (float, int)):
            resolution = Resolution(x=obj, y=obj)
        elif isinstance(obj, (list, tuple)):
            assert len(obj) == 2
            resolution = Resolution(x=obj[0], y=obj[1])
        else:
            assert 0
        return resolution

    def x(self):
        '''Returns x resolution.'''
        return self._x

    def y(self):
        '''Returns y resolution.'''
        return self._y

    def equal(self, other, tol=0.):
        '''Returns whether self is equal to other.'''
        assert isinstance(other, Resolution)
        equal = abs(self.x() - other.x()) <= tol
        equal &= abs(self.y() - other.y()) <= tol
        return equal

    def zoom(self, factor):
        '''
        Returns a new instance, where the resolution of self is divided by the given ``factor``.

        :param factor: zoom factor by which the current resolution is devided by; can be a single number for both x and y
                       resolution or a tuple of size 2 for individual x and y factors
        :type factor: number or (number, number)
        :return:
        :rtype: hubdc.core.Resolution
        '''
        if isinstance(factor, (int, float)):
            factor = factor, factor
        assert len(factor) == 2
        return Resolution(x=self.x() / float(factor[0]), y=self.y() / float(factor[1]))


class Geometry(object):
    '''Class for managing geometries.'''

    def __init__(self, wkt, projection):
        '''Create by given well known text string.'''
        assert isinstance(wkt, str)
        assert isinstance(projection, Projection)
        self._wkt = wkt
        self._projection = projection

    def __repr__(self):
        return '{cls}(wkt={wkt}, projection={projection})'.format(cls=self.__class__.__name__, wkt=repr(self.wkt()),
                                                                  projection=repr(self.projection()))

    def wkt(self):
        '''Return wkt string.'''
        return self._wkt

    def projection(self):
        '''Return projection.'''
        return self._projection

    def ogrGeometry(self):
        '''Returns ogr.Geometry.'''
        ogrGeometry = ogr.CreateGeometryFromWkt(self._wkt)
        return ogrGeometry

    def isPoint(self):
        return ogr.GeometryTypeToName(self.ogrGeometry().GetGeometryType()) == 'Point'

    def boundingBox(self):
        BoundingBox = namedtuple('BoundingBox', ['xmin', 'xmax', 'ymin', 'ymax'])
        return BoundingBox(*self.ogrGeometry().GetEnvelope())

    def x(self):
        return self.ogrGeometry().GetX()

    def y(self):
        return self.ogrGeometry().GetY()

    def reproject(self, projection):
        '''
        Reproject itself into given projection.

        :param projection: target projection
        :type projection: Projection
        :return:
        :rtype: Geometry
        '''
        assert isinstance(projection, Projection)
        transformation = osr.CoordinateTransformation(self.projection().osrSpatialReference(),
                                                      projection.osrSpatialReference())
        ogrGeometry = self.ogrGeometry()
        ogrGeometry.Transform(transformation)
        return Geometry(wkt=ogrGeometry.ExportToWkt(), projection=projection)

    def intersection(self, other):
        '''Returns the intersection of self and other.'''
        assert isinstance(other, Geometry)
        assert self.projection().equal(other.projection())
        ogrGeometry = self.ogrGeometry().Intersection(other.ogrGeometry())
        assert ogrGeometry is not None
        return Geometry(wkt=ogrGeometry.ExportToWkt(), projection=self.projection())

    def union(self, other):
        '''Returns the union of self and other.'''
        assert isinstance(other, Geometry)
        assert self.projection().equal(other.projection())
        ogrGeometry = self.ogrGeometry().Union(other.ogrGeometry())
        assert ogrGeometry is not None
        return Geometry(wkt=ogrGeometry.ExportToWkt(), projection=self.projection())

    def intersects(self, other):
        '''Returns whether self and other intersect.'''
        assert isinstance(other, Geometry)
        other = other.reproject(projection=self.projection())
        assert self.projection().equal(other.projection())
        return self.ogrGeometry().Intersects(other.ogrGeometry())

    def within(self, other):
        '''Returns whether self is within other.'''
        assert isinstance(other, Geometry)
        assert self.projection().equal(other.projection())
        return self.ogrGeometry().Within(other.ogrGeometry())

    def centroid(self):
        '''Return centroid.'''
        return Geometry(wkt=self.ogrGeometry().Centroid().ExportToWkt(), projection=self.projection())


class Extent(Geometry):
    '''Class for managing extents (i.e. bounding boxes).'''

    def __init__(self, xmin, xmax, ymin, ymax, projection):
        '''
        :param xmin:
        :type xmin: float
        :param xmax:
        :type xmax: float
        :param ymin:
        :type ymin: float
        :param ymax:
        :type ymax: float
        :param projection
        :type projection: Projection
        '''
        assert isinstance(projection, Projection)
        try:
            assert xmax > xmin, (xmin, xmax)
        except:
            a=1
        assert ymax > ymin

        ring = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in zip([xmin, xmax, xmax, xmin, xmin],
                        [ymax, ymax, ymin, ymin, ymax]):
            ring.AddPoint(x, y)
        geometry = ogr.Geometry(ogr.wkbPolygon)
        geometry.AddGeometry(ring)
        Geometry.__init__(self, wkt=geometry.ExportToWkt(), projection=projection)

    def equal(self, other, tol=0.):
        assert isinstance(other, Extent)
        for a, b in zip(self.boundingBox, other.BoundingBox):
            if abs(a - b) > tol:
                return False
        return True

    def shape(self, resolution):
        '''Return grid shape (i.e. y, x sizes) for given resolution.'''
        assert isinstance(resolution, Resolution)
        bb = self.boundingBox()
        x = int(round(float(bb.xmax - bb.xmin) / resolution.x()))
        y = int(round(float(bb.ymax - bb.ymin) / resolution.y()))
        return y, x


class Grid(object):
    '''Class for managing raster grids in terms of extent, resolution and projection.'''

    def __init__(self, extent, resolution):
        '''
        Create instance.

        :param extent:
        :type extent: Extent
        :param resolution:
        :type resolution: Union[object, Resolution]
        '''
        assert isinstance(extent, Extent)
        resolution = Resolution.parse(resolution)
        assert isinstance(resolution, Resolution)
        self._resolution = resolution

        ysize, xsize = extent.shape(resolution=resolution)
        bb = extent.boundingBox()

        self._extent = Extent(xmin=bb.xmin,
                              xmax=bb.xmin + xsize * resolution.x(), # trim to multiple of resolution
                              ymin=bb.ymin,
                              ymax=bb.ymin + ysize * resolution.y(), # trim to multiple of resolution
                              projection=extent.projection())

    def __repr__(self):
        return '{cls}(extent={extent}, resolution={resolution}'.format(
            cls=self.__class__.__name__,
            extent=repr(self.extent()),
            resolution=repr(self.resolution()))

    def extent(self):
        '''Return extent.'''
        return self._extent

    def resolution(self):
        '''Return resolution`.'''
        return self._resolution

    def shape(self):
        '''Return (ysize, xsize) tuple.'''
        return self.extent().shape(resolution=self.resolution())

    def xsize(self):
        return self.shape()[1]

    def ysize(self):
        return self.shape()[0]

    def atResolution(self, resolution):
        resolution = Resolution.parse(resolution)
        return Grid(extent=self.extent(), resolution=resolution)

    def xMapCoordinates(self):
        '''Returns the list of map coordinates in x dimension.'''
        bb = self.extent().boundingBox()
        return [bb.xmin + (x + 0.5) * self.resolution().x() for x in range(self.shape()[1])]

    def yMapCoordinates(self):
        '''Returns the list of map coordinates in y dimension.'''
        bb = self.extent().boundingBox()
        return [bb.ymax - (y + 0.5) * self.resolution().y() for y in range(self.shape()[0])]

    def xMapCoordinatesArray(self):
        '''Returns the 2d array of map x coordinates.'''
        return np.asarray(self.xMapCoordinates()).reshape(1, -1) * np.ones(shape=self.shape())

    def yMapCoordinatesArray(self):
        '''Returns the 2d array of map y coordinates.'''
        return np.asarray(self.yMapCoordinates()).reshape(-1, 1) * np.ones(shape=self.shape())

    def xPixelCoordinates(self, offset=0):
        '''Returns the list of pixel coordinates in x dimension with optional ``offset``.'''
        return [x + offset for x in range(self.shape()[1])]

    def yPixelCoordinates(self, offset=0):
        '''Returns the list of pixel coordinates in y dimension with optional ``offset``.'''
        return [y + offset for y in range(self.shape()[0])]

    def xPixelCoordinatesArray(self, offset=0):
        '''Returns the 2d array of pixel x coordinates with optional ``offset``.'''
        return np.int32(np.asarray(self.xPixelCoordinates(offset=offset)).reshape(1, -1) * np.ones(shape=self.shape()))

    def yPixelCoordinatesArray(self, offset=0):
        '''Returns the 2d array of pixel y coordinates with optional ``offset``.'''
        return np.int32(np.asarray(self.yPixelCoordinates(offset=offset)).reshape(-1, 1) * np.ones(shape=self.shape()))

    def geoTransform(self):
        '''Returns a GDAL  georeferencing transform tuple ``(xmin, xres, 0, ymax, 0, -yres)`` from bounds and resolution,
         without any rotation or shearing.'''
        bb = self.extent().boundingBox()
        geotransform = (bb.xmin, self.resolution().x(), 0.0, bb.ymax, 0.0, -self.resolution().y())
        return geotransform

    def equal(self, other, tol=0.):
        '''Return whether self is equal to other.'''
        assert isinstance(other, Grid)
        bool = self.extent().equal(other=other.extent(), tol=tol)
        bool &= self.resolution().equal(other=other.resolution(), tol=tol)
        return bool

    def reproject(self, other):
        '''
        Returns a new instance with:
        a) extent reprojected into the projection of other,
        b) resolution of other, and
        c) anchored to other.
        '''
        assert isinstance(other, Grid)
        extent = self.extent().reproject(projection=other.projection())
        grid = Grid(extent=extent, resolution=other.resolution())
        bb = other.extent().boundingBox()
        grid = grid.anchor(point=createPoint(x=bb.xmin, y=bb.ymin))
        return grid

    def pixelBuffer(self, buffer, left=True, right=True, up=True, down=True):
        '''Returns a new instance with a pixel buffer applied in different directions.

        :param buffer: number of pixels to be buffered (can also be negativ)
        :type buffer: int
        :param left: whether to buffer to the left/west
        :type left: bool
        :param right: whether to buffer to the right/east
        :type right: bool
        :param up: whether to buffer upwards/north
        :type up: bool
        :param down: whether to buffer downwards/south
        :type down: bool
        :return:
        :rtype: hubdc.core.Grid
        '''
        assert isinstance(buffer, int)
        bb = self.extent().boundingBox()
        extent = Extent(xmin=bb.xmin - buffer * self.resolution().x() if left else 0,
                        xmax=bb.xmax + buffer * self.resolution().x() if right else 0,
                        ymin=bb.ymin - buffer * self.resolution().y() if down else 0,
                        ymax=bb.ymax + buffer * self.resolution().y() if up else 0,
                        projection=self.extent().projection())
        return Grid(extent=extent, resolution=self.resolution())

    def anchor(self, point):
        '''
        Returns a new instance that is anchored to a :class:`~hubdc.model.Point`.
        Anchoring will result in a subpixel shift.
        See the source code for implementation details.'''
        assert isinstance(point, Geometry)
        assert point.isPoint()
        assert self.extent().projection().equal(other=point.projection())
        bb = self.extent().boundingBox()
        xoff = (bb.xmin - point.x()) % self.resolution().x()
        yoff = (bb.ymin - point.y()) % self.resolution().y()

        # round snapping offset
        if xoff > self.resolution().x() / 2.:
            xoff -= self.resolution().x()
        if yoff > self.resolution().y() / 2.:
            yoff -= self.resolution().y()

        # return new instance
        extent = Extent(xmin=bb.xmin - xoff,
                        ymin=bb.ymin - yoff,
                        xmax=bb.xmax - xoff,
                        ymax=bb.ymax - yoff,
                        projection=self.extent().projection())
        return Grid(extent=extent, resolution=self.resolution())

    def subset(self, offset, size, trim=False):
        '''
        Returns a new instance that is a subset given by a location (i.e. (x, y) offset)
        and a raster size (i.e. (x, y) size).
        Optionally set ``trim=True`` to restrain the grid extent to the extent of self.
        '''
        xsize, ysize = size
        xoffset, yoffset = offset
        if trim:
            offset = max(xoffset, 0), max(yoffset, 0)
            size = min(xsize, self.xsize() - xoffset), min(ysize, self.ysize() - yoffset)

        bb = self.extent().boundingBox()
        xmin = bb.xmin + xoffset * self.resolution().x()
        xmax = xmin + xsize * self.resolution().x()
        ymax = bb.ymax - yoffset * self.resolution().y()
        ymin = ymax - ysize * self.resolution().y()

        return Grid(extent=Extent(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, projection=self.extent().projection()), resolution=self.resolution())


class PseudoGrid(Grid):
    def __init__(self, size):
        xsize, ysize = size
        res = 1 / 3600. # 1 millisecond of arc
        Grid.__init__(self, extent=Extent(xmin=0, xmax=xsize*res, ymin=0, ymax=ysize*res,
                                          projection=Projection.WGS84()),
                      resolution=Resolution(x=res, y=res))

    @staticmethod
    def fromArray(array):
        isinstance(array, np.ndarray)
        return PseudoGrid(size=(array.shape[-1], array.shape[-2]))


class Date(object):

    def __init__(self, date):
        assert isinstance(date, datetime.date)
        self._date = date

    def __repr__(self):
        return '{}{}{}'.format(self._date.year, str(self._date.month).zfill(2), str(self._date.day).zfill(2))

    def __ge__(self, other):
        assert isinstance(other, Date)
        return self._date >= other._date

    @staticmethod
    def parse(obj):

        if isinstance(obj, Date):
            date = obj._date
        elif isinstance(obj, datetime.date):
            date = obj
        elif isinstance(obj, Date):
            date = obj._date
        elif isinstance(obj, str):
            obj = obj.replace('-', '')
            if len(obj) == 8:
                y, m, d = obj[0:4], obj[4:6], obj[6:8]
            elif len(obj) == 6:
                y, m, d = obj[0:4], obj[4:6], 1
            elif len(obj) == 4:
                y, m, d = obj[0:4], 1, 1
            else:
                assert 0

            date = datetime.date(int(y), int(m), int(d))
        elif isinstance(obj, (list, tuple)):
            date = datetime.date(*obj)
        else:
            assert 0, 'unknown date format'
        return Date(date=date)


class List(object):

    def __init__(self, items):
        self._items = list(items)

    def map(self, function, **kwargs):
        collection = Collection()
        for item in self._items:
            collection._addRaster(raster=function(item, **kwargs))
        return collection


class Band(object):

    def __init__(self, filename, index, mask, name, date, wavelength, geometry, tilingScheme):
        self._filename = filename
        self._index = index
        self.setMask(mask)
        self._name = name
        self._date = date
        self._wavelength = wavelength
        self._geometry = geometry
        self.setTilingScheme(tilingScheme)

    def __str__(self):
        return self._name

    def filename(self, tile=None):
        if tile is None:
            return self._filename
        elif isinstance(tile, Tile):
            return join(dirname(self._filename), tile.name(), basename(self._filename))
        else:
            assert 0

    def index(self):
        return self._index

    def mask(self):
        return self._mask

    def name(self):
        return self._name

    def date(self):
        isinstance(self._date, Date)
        return self._date

    def wavelength(self):
        return self._wavelength

    def geometry(self):
        assert isinstance(self._geometry, Geometry)
        return self._geometry

    def setGeometry(self, geometry):
        assert isinstance(geometry, Geometry)
        self._geometry = geometry
        return self

    def tilingScheme(self):
        assert isinstance(self._tilingScheme, TilingScheme)
        return self._tilingScheme

    def setTilingScheme(self, tilingScheme):
        assert isinstance(tilingScheme, TilingScheme)
        self._tilingScheme = tilingScheme

    def setMask(self, mask):
        assert isinstance(mask, (type(None), Operand))
        self._mask = mask

    def updateMask(self, mask):
        assert isinstance(mask, Operand)
        band = copy.deepcopy(self)
        if self._mask is None:
            band.setMask(mask=mask)
        else:
            band.setMask(mask=self._mask.multiply(raster2=mask))
        return band

    def rename(self, name):
        band = copy.deepcopy(self)
        band._name = name
        return band

    def side(self, function):
        function(self)
        return self

    def dataset(self, grid):
        assert isinstance(grid, Grid)
        # find all source tiles for given target grid
        filenames = list()
        for tile in self.tilingScheme().tiles():
            extent = tile.extent()
            if extent.intersects(other=grid.extent()):
                filename = self.filename(tile=tile)
                if not filename.startswith('/vsimem/'):
                    if not exists(filename):
                        continue # in some cases a tile extent is only touched at the edge

                filenames.append(filename)

        vrtSource = createVRTDataset(rasterDatasetsOrFilenames=filenames, bandList=[self.index()+1])
        vrtTarget = vrtSource.warp(grid=grid)
        return vrtTarget.band(index=0)

    def arrays(self, grid):
        array = self.dataset(grid=grid).readAsArray()
        mask = self.mask()
        if mask is None:
            maskArray = np.full(shape=grid.shape(), fill_value=True)
        elif isinstance(mask, Raster):
            maskArray, _ = mask.arrays(grid=grid) # note: the array is used as the mask!
            maskArray = maskArray[0]
        elif isinstance(mask, Pipeline):
            maskArray, _ = mask.arrays(grid=grid) # note: the array is used as the mask!
            maskArray = maskArray[0]
        else:
            assert 0
        return array, maskArray.view(dtype=bool)


class Operand(object):

    def _connect(self, operator):
        assert isinstance(operator, Operator)
        if isinstance(self, (Raster, Collection)):
            pipeline = Pipeline(self)
        elif isinstance(self, Pipeline):
            pipeline = copy.deepcopy(self)
        else:
            assert 0
        pipeline.connect(operator=operator)
        return pipeline

    def _computeOperatorOnTile(self, operator, tile, extent, filename, resolution=None, noDataValues=None, driver=None,
                               options=None, categoryNames=None):

        assert isinstance(operator, Operator)
        assert isinstance(tile, Tile)

        if resolution is None:
            if isinstance(self, Raster):  # use resolution of first band
                resolution = openRasterDataset(filename=self.band(index=0).filename(tile=tile)).grid().resolution()
            elif isinstance(self, Collection):  # use resolution of first raster
                resolution = openRasterDataset(filename=self.first().band(index=0).filename(tile=tile)).grid().resolution()
            else:
                assert 0

        resolution = Resolution.parse(resolution)

        grid = Grid(extent=extent, resolution=resolution)
        if driver is None:
            driver = RasterDriver.fromFilename(filename=filename)
        maskFilename = join(dirname(filename), '.mask.{}'.format(basename(filename)))

        if isinstance(operator, MapOperator):
            array, maskArray = operator.calculate(raster=self, grid=grid)
        elif isinstance(operator, ReduceOperator):
            array, maskArray = operator.calculate(collection=self, grid=grid)
        else:
            assert 0


        msg = 'wrong array or mask array format, check operator: {}'.format(operator)
        if isinstance(array, list):
            assert isinstance(array[0], np.ndarray), msg
            assert array[0].ndim == 2, msg
        elif isinstance(array, np.ndarray):
            assert array.ndim == 3, msg
        else:
            assert 0, msg

        if isinstance(maskArray, list):
            assert isinstance(maskArray[0], np.ndarray), msg
            assert maskArray[0].ndim == 2, msg
            assert maskArray[0].dtype == bool, 'wrong mask array data type, expected bool, check operator: {}'.format(operator)
        elif isinstance(maskArray, np.ndarray):
            assert maskArray.ndim == 3, msg
        else:
            raise Exception('wrong mask array format, check operator: {}'.format(operator))

        if len(array) != len(maskArray):
            raise Exception('number of bands in array and mask array must match, check operator: {}'.format(operator))

        if noDataValues is not None:
            assert len(noDataValues) == len(array)
            for a, m, noDataValue in zip(array, maskArray, noDataValues):
                a[np.logical_not(m)] = noDataValue

        if categoryNames is not None:
            assert len(categoryNames) == len(array)

        arrayTileFilename = join(dirname(filename), tile.name(), basename(filename))
        arrayRasterDataset = RasterDataset.fromArray(array=array, grid=grid,
                                                     filename=arrayTileFilename,
                                                     driver=driver, options=options)
        arrayRasterDataset.setNoDataValues(values=noDataValues)
        maskTileFilename = join(dirname(filename), tile.name(), '.mask.{}'.format(basename(filename)))
        maskRasterDataset = RasterDataset.fromArray(array=maskArray, grid=grid,
                                                    filename=maskTileFilename,
                                                    driver=driver, options=options)

        for i, rasterBandDataset in enumerate(arrayRasterDataset.bands()):
            rasterBandDataset.setDescription(value=operator.bandName(i, self))
            if categoryNames is not None:
                rasterBandDataset.setCategoryNames(names=categoryNames[i])
                # classDefinition = hfc.ClassDefinition(names=categoryNames[i])
                #rasterBandDataset.setCategoryColors(colors=[(c.red(), c.green(), c.blue()) for c in classDefinition.colors()])

        raster = Raster(name=operator.rasterName(self),
                        date=operator.rasterDate(self))

        tilingScheme = TilingScheme().addTile(Tile(name=tile.name(), extent=extent)) # should be omitted in the future!!!
        for i in range(len(array)):

            mask = Raster(name='Mask', date=None).addBand(band=Band(filename=maskFilename, index=i, mask=None,
                                                                    name='Mask', date=None, wavelength=None,
                                                                    geometry=grid.extent(), tilingScheme=tilingScheme))
            raster.addBand(band=Band(filename=filename, index=i,
                                     mask=mask,
                                     name=operator.bandName(i, self),
                                     date=operator.bandDate(i, self),
                                     wavelength=operator.wavelength(i, self),
                                     geometry=grid.extent(),
                                     tilingScheme=tilingScheme))

        return raster, arrayRasterDataset, maskRasterDataset

    def arrays(self, grid):
        assert 0 # overload me!

    def identity(self):
        return self._connect(operator=MapIdentity())

    def multiply(self, raster2):
        return self._connect(operator=MapBinaryElementWise(raster2=raster2, method=np.multiply))

    def divide(self, raster2):
        return self._connect(operator=MapBinaryElementWise(raster2=raster2, method=np.divide))

    def add(self, raster2):
        return self._connect(operator=MapBinaryElementWise(raster2=raster2, method=np.add))

    def subtract(self, raster2):
        return self._connect(operator=MapBinaryElementWise(raster2=raster2, method=np.subtract))

    def equal(self, raster2):
        return self._connect(operator=MapBinaryElementWise(raster2=raster2, method=np.equal))

    def not_equal(self, raster2):
        return self._connect(operator=MapBinaryElementWise(raster2=raster2, method=np.not_equal))

    def where(self, condition, raster2):
        return self._connect(operator=MapWhere(condition=condition, raster2=raster2))

    def select(self, bandNames):
        return self._connect(operator=MapSelect(bandNames=bandNames))

    def rename(self, bandNames):
        return self._connect(operator=MapRename(bandNames=bandNames))

    def addRaster(self, raster):
        return self._connect(operator=MapAddRaster(raster=raster))

    def normalizedDifference(self, bandNames=None):
        return self._connect(operator=MapNormalizedDifference(bandNames=bandNames))

    def predict(self, estimator):
        if isinstance(estimator, Classifier):
            return self._connect(operator=MapPredictClassification(classifier=estimator))
        else:
            assert 0

    def inflate(self, bandName, offsets, nbits):
        return self._connect(operator=MapInflate(bandName=bandName, offsets=offsets, nbits=nbits))

    def sampleRegions(self, vectorDataset, idProperty, tilingScheme, resolution):
        assert isinstance(vectorDataset, VectorDataset)
        assert isinstance(tilingScheme, TilingScheme)
        resolution = Resolution.parse(resolution)

        isPointGeometry = vectorDataset.ogrLayer().GetGeomType() == ogr.CreateGeometryFromWkt('Point(0 0)').GetGeometryType()
        assert isPointGeometry

        resultIds = list()
        resultValues = list()

        for tile in tilingScheme.tiles():
            print(tile.name())
            extent = tile.extent()
            grid = Grid(extent, resolution=resolution)
            if isinstance(self, Pipeline):
                array, maskArray, raster = self.arrays(grid, returnRaster=True)
            else:
                array, maskArray = self.arrays(grid)

            initValue = -np.inf
            idArray = vectorDataset.rasterize(grid=grid, gdalType=gdal.GDT_Float64,
                                                  initValue=initValue, burnAttribute=idProperty,
                                                  allTouched=False, filterSQL=None).readAsArray()

            ids, indices = np.unique(idArray, return_index=True)
            ids = ids[1:]         # skip init value
            indices = indices[1:] # skip init value

            values = np.array([a.ravel()[indices] for a in array])
            valid = np.all([m.ravel()[indices] for m in maskArray], axis=0)

            ids = ids[valid]
            values = values[:, valid]

            resultIds.append(ids)
            resultValues.append(values)

        resultIds = np.concatenate(resultIds, axis=0)

        geometry = tilingScheme.geometry().reproject(projection=vectorDataset.projection())

        layer = vectorDataset.ogrLayer()
        layer.SetSpatialFilter(geometry.ogrGeometry())

        attributes = OrderedDict()
        for id in resultIds:
            attributes[id] = None
        fieldNames = vectorDataset.fieldNames()
        for feature in layer:
            id = feature.GetField(idProperty)
            if id in resultIds:
                attributes[id] = [feature.GetField(name) for name in fieldNames]

        for v in attributes.values():
            assert v is not None

        if isinstance(self, Pipeline):
            bandNames = raster.bandNames()
        else:
            bandNames = self.bandNames()
        names = bandNames + fieldNames
        data = np.concatenate((np.concatenate(resultValues, axis=1).T, np.array(list(attributes.values()))), axis=1)


        return Table(data=data, names=names)


class CollectionOperand(Operand):

    def median(self, bandNames=None):
        return self._connect(operator=ReduceMedian(bandNames=bandNames))

    def toBands(self):
        return self._connect(operator=ReduceToBands())

class Pipeline(Operand):
    def __init__(self, operand):
        assert isinstance(operand, (Raster, Collection))
        self._operand = operand
        self._steps = list()
        self._cache = False

    def connect(self, operator):
        assert isinstance(operator, Operator)
        self._steps.append(operator)
        return self

    def compute(self, filename, tilingScheme=None, resolution=None, noDataValues=None, driver=None, options=None,
                categoryNames=None):

        # derive tiling scheme from inputs if not specified
        if tilingScheme is None:
            if isinstance(self._operand, Raster): # use tiling scheme of first band
                tilingScheme = self._operand.band(index=0).tilingScheme()
            elif isinstance(self._operand, Collection):  # use tiling scheme of first raster
                tilingScheme = self._operand.first().band(index=0).tilingScheme()
            elif isinstance(self._operand, Pipeline): # use tiling scheme of first band
                tilingScheme = self._operand.band(index=0).tilingScheme()
            else:
                assert 0

        assert isinstance(tilingScheme, TilingScheme)
        assert isinstance(filename, str)

        geometry = None
        for tile in tilingScheme.tiles():
            print(tile.name())
            extent = tile.extent()
            operand = self._operand
            last = len(self._steps) - 1
            tmpfilenames = ['', '']
            for i, operator in enumerate(self._steps):
                print('  {}'.format(operator))
                if i != last: # write all intermediate results into mem
                    kwds = {'filename': '/vsimem/step{}/{}'.format(i, filename), 'driver': driver, 'options': None}
                else:
                    kwds = {'filename': filename, 'driver': driver, 'options': options, 'noDataValues': noDataValues}

                operand, rasterDataset, maskRasterDataset = operand._computeOperatorOnTile(operator=operator,
                                                                                           tile=tile,
                                                                                           extent=extent,
                                                                                           resolution=resolution,
                                                                                           categoryNames=categoryNames,
                                                                                           **kwds)

                for tmpfilename in tmpfilenames: # free memory of step i-1
                    gdal.Unlink(tmpfilename)
                tmpfilenames = [rasterDataset.filename(), maskRasterDataset.filename()]

                assert isinstance(operand, Raster)

            if geometry is None:
                geometry = extent
            else:
                geometry = geometry.union(other=extent)

        assert isinstance(operand, Raster) # just take the raster from the last tile and modify it (should be ok!?)

        for band in operand.bands():
            band.setGeometry(geometry=geometry)
            band.setTilingScheme(tilingScheme=tilingScheme)
            if band.mask() is not None:
                band.mask().setGeometry(geometry)
                band.mask().setTilingScheme(tilingScheme)

        return operand

    def cache(self):
        self._cache = True
        return self


    def arrays(self, grid, returnRaster=False):
        assert isinstance(grid, Grid)

        tilingScheme = SingleTileTilingScheme(extent=grid.extent())
        filename = '/vsimem/pipeline/raster.bsq'
        arrayFilename = '/vsimem/pipeline/./raster.bsq'
        maskArrayFilename = '/vsimem/pipeline/./.mask.raster.bsq'

        if self._cache:
            filename = filename.replace('pipeline', 'cache/{}'.format(id(self)))
            arrayFilename = arrayFilename.replace('pipeline', 'cache/{}'.format(id(self)))
            maskArrayFilename = maskArrayFilename.replace('pipeline', 'cache/{}'.format(id(self)))


        key = '{}_{}'.format(id(self), id(grid))
        if key in CACHE:
            raster, array, maskArray = CACHE[key]
        else:
            raster = self.compute(tilingScheme=tilingScheme, resolution=grid.resolution(),
                                  filename=filename, driver=RasterDriver('ENVI'), options=None)
            array = openRasterDataset(filename=arrayFilename).readAsArray()
            maskArray = openRasterDataset(filename=maskArrayFilename).readAsArray()

        if self._cache:
            CACHE[key] = raster, array, maskArray
        else:
            gdal.Unlink(arrayFilename)
            gdal.Unlink(maskArrayFilename)

        if returnRaster:
            return array, maskArray, raster
        else:
            return array, maskArray


class Operator(object):
    pass

class MapOperator(Operator):

    def __repr__(self):
        return '{}(...)'.format(self.__class__.__name__)

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)
        array, maskArray = raster.arrays(grid=grid)

        assert 0  # overload me!

    def rasterName(self, raster):
        return raster.name()

    def bandName(self, index, raster):
        assert 0  # overload me!

    def rasterDate(self, raster):
        return raster.date()

    def bandDate(self, index, raster):
        return None

    def wavelength(self, index, raster):
        return None


class ReduceOperator(Operator):
    def calculate(self, collection, grid):
        assert isinstance(collection, Collection)
        assert isinstance(grid, Grid)
        assert 0  # overload me!

    def rasterName(self, collection):
        return ''

    def bandName(self, index, collection):
        assert 0  # overload me!

    def rasterDate(self, collection):
        return None

    def bandDate(self, index, collection):
        return None

    def wavelength(self, index, collection):
        return None


class ReduceMedian(ReduceOperator):

    def __init__(self, bandNames):
        self._bandNames = bandNames

    def bandNames(self, collection):
        assert isinstance(collection, Collection)
        if self._bandNames is None: # use all bands from the first raster
            return collection.first().bandNames()
        return self._bandNames

    def calculate(self, collection, grid):
        assert isinstance(collection, Collection)
        assert isinstance(grid, Grid)

        array = list()
        for raster in collection.rasters():
            raster = raster.select(bandNames=self.bandNames(collection=collection))
            a, m = np.float32(raster.arrays(grid=grid))
            a[np.logical_not(m)] = np.nan
            array.append(a)
        array = np.nanmedian(array, axis=0)
        maskArray = np.isfinite(array)
        return array, maskArray

    def bandName(self, index, collection):
        return 'Median_{}'.format(self.bandNames(collection=collection)[index])


class ReduceToBands(ReduceOperator):

    def __init__(self):
        self._bandNames = None

    def calculate(self, collection, grid):
        assert isinstance(collection, Collection)
        assert isinstance(grid, Grid)

        array = list()
        maskArray = list()
        for raster in collection.rasters():
            a, m = raster.arrays(grid=grid)
            array.extend(a)
            maskArray.extend(np.ndarray.view(m, dtype=bool))
        return array, maskArray

    def bandName(self, index, collection):
        return 'band {}'.format(index)


class MapIdentity(MapOperator):

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)

        array, maskArray = raster.arrays(grid=grid)
        return array, maskArray

    def bandName(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index).name()

    def rasterName(self, raster):
        assert isinstance(raster, Raster)
        return raster.name()

    def rasterDate(self, raster):
        assert isinstance(raster, Raster)
        return raster.date()

    def bandDate(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).date()

    def wavelength(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).wavelength()


class MapNormalizedDifference(MapOperator):
    def __init__(self, bandNames=None):
        if bandNames is None:
            bandNames = (0, 1)
        self._bandNames = bandNames

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)
        (a, b), (ma, mb) = raster.select(bandNames=self._bandNames).arrays(grid=grid)
        array = np.divide(np.float32(a - b), np.float32(a + b))
        np.clip(array, -1, 1, out=array)
        maskArray = np.logical_and(ma, mb)
        return array[None], maskArray[None]

    def bandName(self, index, raster):
        return 'NormalizedDifference'


class MapPredictClassification(MapOperator):
    def __init__(self, classifier):
        assert isinstance(classifier, Classifier)
        self._classifier = classifier

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)

        array, maskArray = raster.select(bandNames=self._classifier._inputProperties).arrays(grid=grid)
        classification = np.zeros(shape=grid.shape())

        valid = np.all(maskArray, axis=0) # skip every pixel that has a missing band value
        if np.any(valid):
            X = np.float64(array)[:, valid].T
            y = self._classifier._sklClassifier.predict(X=X)
            classification[valid] = y

        return classification[None], valid[None]

    def bandName(self, index, raster):
        return 'Classification'


class MapBinaryElementWise(MapOperator):
    def __init__(self, raster2, method):
        self._raster2 = raster2
        self._method = method

    def __repr__(self):
        return 'MapBinaryElementWise(raster2={}, method={})'.format(self._raster2, self._method.__name__)

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)
        aArray, aMaskArray = raster.arrays(grid=grid)

        if isinstance(self._raster2, Operand):
            bArray, bMaskArray = self._raster2.arrays(grid=grid)
        else:
            bArray = self._raster2
            bMaskArray = True
        array = self._method(aArray, bArray)
        maskArray = np.logical_and(aMaskArray, bMaskArray)
        return array, maskArray

    def bandName(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).name()


class MapInflate(MapOperator):
    def __init__(self, bandName, offsets, nbits):
        self._bandName = bandName
        self._offsets = offsets
        self._nbits = nbits
        assert len(self._offsets) == len(self._nbits)

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)
        array, maskArray = raster.select(bandNames=self._bandName).arrays(grid=grid)

        inflated = list()
        for offset, nbit in zip(self._offsets, self._nbits):
            inflated.append(np.bitwise_and(np.right_shift(array, offset), (2**nbit - 1))[0])

        return np.uint8(inflated), [maskArray[0]]*len(self._offsets)

    def bandName(self, index, raster):
        return 'Inflated {}'.format(index+1)


class MapWhere(MapOperator):
    def __init__(self, condition, raster2):
        assert isinstance(condition, Operand)
        self._condition = condition
        self._raster2 = raster2

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)

        y = raster.array(grid=grid)
        condition = self._condition.array(grid)
        if isinstance(self._raster2, (Raster, Pipeline)):
            x = self._raster2.array(grid=grid)
        else:
            x = self._raster2

        result = np.where(condition, x, y)
        return result

    def bandName(self, index, raster):
        return raster.band(index=index).name()

    def noDataValue(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).noDataValue()

    def rasterName(self, raster):
        assert isinstance(raster, Raster)
        return raster.name()

    def rasterDate(self, raster):
        assert isinstance(raster, Raster)
        return raster.date()

    def bandDate(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).date()

    def wavelength(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).wavelength()


class MapSelect(MapOperator):
    def __init__(self, bandNames):
        self._bandNames = bandNames

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)
        return raster.select(bandNames=self._bandNames).arrays(grid=grid)

    def bandName(self, index, raster):
        return raster.select(self._bandNames).bandNames()[index]

    def noDataValue(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).noDataValue()

    def rasterName(self, raster):
        assert isinstance(raster, Raster)
        return raster.name()

    def rasterDate(self, raster):
        assert isinstance(raster, Raster)
        return raster.date()

    def bandDate(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).date()

    def wavelength(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).wavelength()


class MapRename(MapOperator):
    def __init__(self, bandNames):
        self._bandNames = bandNames

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)
        return raster.arrays(grid=grid)

    def bandName(self, index, raster):
        return self._bandNames[index]

    def noDataValue(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).noDataValue()

    def rasterName(self, raster):
        assert isinstance(raster, Raster)
        return raster.name()

    def rasterDate(self, raster):
        assert isinstance(raster, Raster)
        return raster.date()

    def bandDate(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).date()

    def wavelength(self, index, raster):
        assert isinstance(raster, Raster)
        return raster.band(index=index).wavelength()


class MapAddRaster(MapOperator):
    def __init__(self, raster):
        assert isinstance(raster, Pipeline)
        self._raster = raster
        self.stack = None

    def calculate(self, raster, grid):
        assert isinstance(raster, Raster)
        assert isinstance(grid, Grid)
        raster2 = self._raster.raster(grid=grid)
        array = list(raster.array(grid=grid))
        array.extend(raster2.array(grid=grid))
        self.buildStack(raster=raster, raster2=raster2)
        return array

    def buildStack(self, raster, raster2):
        self.stack = raster.addRaster(raster2)

    def bandName(self, index, raster):
        return self.stack.band(index).name()

    def noDataValue(self, index, raster):
        return self.stack.band(index).noDataValue()

    def bandDate(self, index, raster):
        return self.stack.band(index).date()

    def wavelength(self, index, raster):
        return self.stack.band(index).wavelength()


class Raster(Operand):

    def __init__(self, name, date):
        assert isinstance(name, str)
        assert isinstance(date, (type(None), Date))
        self._name = name
        self._date = date
        self._bands = list()
        self._cache = False

    def __str__(self):
        return self._name

    def __len__(self):
        return len(self._bands)

    def name(self):
        return self._name

    def date(self):
        return self._date

    def bands(self):
        for band in self._bands:
            assert isinstance(band, Band)
            yield band

    def bandNames(self):
        return [band.name() for band in self.bands()]

    def wavelengths(self):
        return [band.wavelength() for band in self.bands()]

    def addBand(self, band):
        self._bands.append(band)
        return self

    def band(self, index=None, name=None, wavelength=None):
        if index is not None:
            band = self._bands[index]
        elif name is not None:
            index = [band.name() for band in self.bands()].index(name)
            band = self._bands[index]
        elif wavelength is not None:
            if all([v is None for v in self.wavelengths()]):
                raise Exception('no wavebands available')
            index = int(np.argmin([abs(v - wavelength) if v is not None else np.inf for v in self.wavelengths()]))
            band = self._bands[index]
        else:
            assert 0

        assert isinstance(band, Band)
        return band

    def setGeometry(self, geometry):
        for band in self.bands():
            band.setGeometry(geometry=geometry)

    def setTilingScheme(self, tilingScheme):
        for band in self.bands():
            band.setTilingScheme(tilingScheme=tilingScheme)

    def compute(self, filename, tilingScheme=None, resolution=None, noDataValues=None, categoryNames=None, driver=None,
                options=None):
        return (Pipeline(operand=self)
                    .identity()
                    .compute(filename=filename, tilingScheme=tilingScheme, resolution=resolution,
                             noDataValues=noDataValues, categoryNames=categoryNames, driver=driver, options=options))

    def cache(self):
        self._cache = True
        return self

    def select(self, bandNames):

        if isinstance(bandNames, (str, int, float)):
            bandNames = [bandNames]
        assert isinstance(bandNames, (list, tuple))
        for name in bandNames:
            assert isinstance(name, (str, int, float))

        raster = Raster(name=self.name(), date=self.date())

        for name in bandNames:
            if isinstance(name, int):
                band = copy.deepcopy(self.band(index=name))
            elif isinstance(name, float):
                band = copy.deepcopy(self.band(wavelength=name))
            else:
                band = copy.deepcopy(self.band(name=name))

            raster.addBand(band=band)
        return raster

    def rename(self, bandNames):
        raster = Raster(name=self.name(), date=self.date())
        for band, name in zip(self.bands(), bandNames):
            raster.addBand(band=band.rename(name=name))
        return raster

    def addRaster(self, raster):
        result = copy.deepcopy(self)

        if isinstance(raster, Raster):
            for band in raster.bands():
                result.addBand(band=band)
        else:
            assert 0
        return result

    def side(self, function):
        function(self)
        return self

    def map(self, function):
        raster = Raster(name=self.name(), date=self.date())
        for band in self.bands():
            raster.addBand(band=function(band))
        return raster

    def updateMask(self, mask):
        return self.map(lambda band: band.updateMask(mask=mask))

    def arrays(self, grid):
        assert isinstance(grid, Grid)

        # read array
        array = list()
        maskArray = list()
        for band in self.bands():
            a, m = band.arrays(grid=grid)
            array.append(a)
            maskArray.append(m)
        return array, maskArray

    def maskArray(self, grid):
        marray = list()
        for band in self.bands():
            if band.mask() is None:
                m = np.full(shape=grid.shape(), fill_value=True, dtype=bool)
            else:
                m = band.mask().array(grid=grid)
                assert len(m) == 1
                m = m[0]
            marray.append(m)
        return marray


class Collection(CollectionOperand):

    def __init__(self):
        self._rasters = list()

    def __len__(self):
        return len(self._rasters)

    def rasters(self):
        for raster in self._rasters:
            assert isinstance(raster, (Raster, Pipeline))
            yield raster

    def _addRaster(self, raster):
        assert isinstance(raster, Operand)
        self._rasters.append(raster)

    def side(self, function):
        function(self)
        return self

    def first(self):
        return self._rasters[0]

    def slice(self, start, stop, step=None):
        collection = Collection()
        collection._rasters = copy.deepcopy(self._rasters[slice(start, stop, step)])
        return collection

    def filterDate(self, start, end):
        return self.filter(filter=DateFilter(start=Date.parse(start), end=Date.parse(end)))

    def filterBounds(self, geometry):

        if isinstance(geometry, Geometry):
            pass
        else:
            assert 0, 'unknown geometry'

        return self.filter(filter=BoundsFilter(geometry=geometry))

    def filter(self, filter):
        assert isinstance(filter, Filter)
        collection = Collection()
        for raster in self.rasters():
            if filter.matches(raster=raster):
                collection.addRaster(copy.deepcopy(raster))
        return collection

    def map(self, function):
        collection = Collection()
        for raster in self.rasters():
            collection.addRaster(raster=function(raster))
        return collection

    def merge(self, *args):
        rasters = list()
        for collection in [self] + list(args):
            assert isinstance(collection, Collection)
            rasters.extend(collection._rasters)
        merged = Collection()
        merged._rasters = rasters
        return merged


class Tile(object):

    def __init__(self, name, extent):
        assert isinstance(extent, Extent)
        self._name = name
        self._extent = extent

    def name(self):
        assert isinstance(self._name, str)
        return self._name

    def extent(self):
        assert isinstance(self._extent, Extent)
        return self._extent


class TilingScheme(object):

    def __init__(self):
        self._tiles = OrderedDict()

    def tiles(self):
        for tilename in self._tiles:
            tile = self._tiles[tilename]
            assert isinstance(tile, Tile)
            yield tile

    def tile(self, name):
        tile = self._tiles[name]
        assert isinstance(tile, Tile)
        return tile

    def addTile(self, tile):
        assert isinstance(tile, Tile)
        self._tiles[tile.name()] = tile
        return self

    def geometry(self):
        geometry = None
        for tile in self.tiles():
            if isinstance(geometry, Geometry):
                geometry = geometry.union(other=tile.extent())
            else:
                geometry = tile.extent()
        assert isinstance(geometry, Geometry)
        return geometry


class SingleTileTilingScheme(TilingScheme):

    def __init__(self, extent):
        assert isinstance(extent, Extent)
        TilingScheme.__init__(self)
        self.addTile(tile=Tile(name='.', extent=extent))


class Filter(object):
    def matches(self, raster):
        return True


#class ProductFilter(Filter):
#    def __init__(self, pattern):
#        self.pattern = pattern

#    def matches(self, filename):
#        return fnmatch.fnmatch(basename(filename), self.pattern)

class DateFilter(Filter):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def matches(self, raster):
        assert isinstance(raster, Raster)
        return raster.date() >= self.start and raster.date() <= self.end


class BoundsFilter(Filter):
    def __init__(self, geometry):
        assert isinstance(geometry, Geometry)
        self.geometry = geometry

    def matches(self, raster):
        for band in raster.bands():
            if self.geometry.intersects(other=band.geometry()):
                return True
        return False


class RasterDataset(object):
    '''Class for managing raster datasets files.'''

    def __init__(self, gdalDataset):
        '''Create an instance by a given gdal.Dataset.'''
        assert isinstance(gdalDataset, gdal.Dataset)
        self._gdalDataset = gdalDataset

        projection = Projection(wkt=self._gdalDataset.GetProjection())
        geotransform = self._gdalDataset.GetGeoTransform()
        resolution = Resolution(x=geotransform[1], y=abs(geotransform[5]))
        extent = Extent(xmin=geotransform[0],
                        xmax=geotransform[0] + self._gdalDataset.RasterXSize * resolution.x(),
                        ymin=geotransform[3] - self._gdalDataset.RasterYSize * resolution.y(),
                        ymax=geotransform[3],
                        projection=projection)

        self._grid = Grid(extent=extent, resolution=resolution)

    def __repr__(self):
        return '{cls}(gdalDataset={gdalDataset})'.format(cls=self.__class__.__name__,
                                                         gdalDataset=repr(self.gdalDataset()))

    @staticmethod
    def fromSpecification(grid, bands, gdalType=gdal.GDT_Float32, filename='', driver=None, options=None):
            '''
            Creates a new raster file with extent, resolution and projection given by ``grid``.

            :param grid:
            :type grid: Grid
            :param bands: number of raster bands
            :type bands: int
            :param gdalType: one of the ``gdal.GDT_*`` data types, or use gdal_array.NumericTypeCodeToGDALTypeCode
            :type gdalType: int
            :param filename: output filename
            :type filename: str
            :param options: creation options
            :type options:
            :return:
            :rtype: RasterDataset
            '''

            assert isinstance(grid, Grid)
            if driver is None:
                driver = RasterDriver(name='MEM')

            if options is None:
                options = []

            assert isinstance(filename, str)
            if (not driver.equal(RasterDriver('MEM'))
                and not filename.startswith('/vsimem/')
                and not exists(dirname(filename))):
                makedirs(dirname(filename))

            ysize, xsize = grid.shape()
            gdalDataset = driver.gdalDriver().Create(filename, xsize, ysize, bands, gdalType, options)
            gdalDataset.SetProjection(grid.extent().projection().wkt())
            gdalDataset.SetGeoTransform(grid.geoTransform())
            return RasterDataset(gdalDataset=gdalDataset)

    @staticmethod
    def fromArray(array, grid=None, filename='', driver=None, options=None):

        if isinstance(array, list):
            for a in array:
                assert isinstance(a, np.ndarray)
                assert a.ndim == 2
            array = np.array(array)

        if grid is None:
            grid = PseudoGrid.fromArray(array)

        if isinstance(array, np.ndarray):
            if array.ndim == 2:
                array = array[None]
            assert array.ndim == 3
        elif isinstance(array, list):
            assert all([subarray.ndim == 2 for subarray in array])
        else:
            raise TypeError()

        bands = len(array)
        dtype = array[0].dtype
        if dtype == bool:
            dtype = np.uint8

        gdalType = gdal_array.NumericTypeCodeToGDALTypeCode(dtype)
        rasterDataset = RasterDataset.fromSpecification(grid=grid, bands=bands, gdalType=gdalType, filename=filename, driver=driver, options=options)
        rasterDataset.writeArray(array=array, grid=grid)
        rasterDataset.flushCache()
        return rasterDataset


    def gdalDataset(self):
        '''Return the gdal.Dataset.'''
        return self._gdalDataset

    def filenames(self):
        '''Return gdal dataset file list`` '''
        return self._gdalDataset.GetFileList()

    def filename(self):
        '''Return filename.'''
        filenames = self.filenames()
        if filenames is None:
            filename = None
        else:
            filename = filenames[0]
        return filename

    def grid(self):
        '''Return the :class:`~hubdc.model.Grid`.'''
        return self._grid

    def band(self, index):
        '''Return the :class:`~hubdc.model.RasterBandDataset` given by ``index``.'''
        return RasterBandDataset(raster=self, index=index)

    def bands(self):
        '''Returns an iterator over each :class:`~hubdc.model.RasterBandDataset`.'''
        for i in range(self.zsize()):
            yield self.band(i)

    def driver(self):
        '''Return the :class:`~hubdc.model.Driver`.'''
        return RasterDriver(name=self._gdalDataset.GetDriver().ShortName)

    def readAsArray(self, grid=None, resampleAlg=gdal.GRA_NearestNeighbour):
        '''
        Returns raster data as 3d array.

        :param grid: if provided, only data inside the grid extent is returned
        :type grid: hubdc.core.Grid
        :param resampleAlg: one of the GDAL resampling algorithms (i.e. gdal.GRA_*)
        :type resampleAlg: int
        :return:
        :rtype: numpy.ndarray
        '''

        if grid is None:
            array = self._gdalDataset.ReadAsArray()
        else:
            assert isinstance(grid, Grid)
            xoff = int(round((grid.extent().xmin() - self.grid().extent().xmin()) / self.grid().resolution().x(), 0))
            yoff = int(round((self.grid().extent().ymax() - grid.extent().ymax()) / self.grid().resolution().y(), 0))
            xsize = int(round((grid.extent().xmax() - grid.extent().xmin()) / self.grid().resolution().x(), 0))
            ysize = int(round((grid.extent().ymax() - grid.extent().ymin()) / self.grid().resolution().y(), 0))

            buf_ysize, buf_xsize = grid.shape()
            array = self._gdalDataset.ReadAsArray(xoff=xoff, yoff=yoff, xsize=xsize, ysize=ysize,
                                                  buf_xsize=buf_xsize, buf_ysize=buf_ysize,
                                                  resample_alg=resampleAlg)

        if array.ndim == 2:
            array = array[None]

        return array

    def writeArray(self, array, grid=None):
        '''
        Writes raster data.

        :param array:
        :type array: 3d array | list of 2d arrays
        :param grid: if provided, data is written to the location given by the grid extent
        :type grid: hubdc.core.Grid
        '''

        assert len(array) == self.zsize()
        for band, bandArray in zip(self.bands(), array):
            band.writeArray(bandArray, grid=grid)

    def flushCache(self):
        '''Flush the cache.'''
        self._gdalDataset.FlushCache()
        return self

    def close(self):
        '''Close the gdal.Dataset.'''
        self._gdalDataset = None

    def setNoDataValues(self, values):
        '''Set band no data values.'''
        if values is not None:
            for i, band in enumerate(self.bands()):
                band.setNoDataValue(values[i])
        self.flushCache()

    def noDataValues(self, default=None, required=False):
        '''Returns band no data values. For bands without a no data value, ``default`` is returned.'''
        return [band.noDataValue(default=default, required=required) for band in self.bands()]

    def setNoDataValue(self, value):
        '''Set a single no data value to all bands.'''
        if value is not None:
            self.setNoDataValues(values=[value] * self.zsize())
            if self.driver().equal(other=RasterDriver(name='ENVI')):
                self.setMetadataItem(key='data ignore value', value=value)
            self.flushCache()
        return self

    def noDataValue(self, default=None):
        '''
        Returns a single no data value. Raises an exception if not all bands share the same no data value.
        If all bands are without a no data value, ``default`` is returned.
        '''
        noDataValues = self.noDataValues()
        if len(set(noDataValues)) != 1:
            raise Exception('there are multiple no data values, use getNoDataValues() instead')
        noDataValue = noDataValues[0]
        if noDataValue is None:
            noDataValue = default
        return noDataValue

    def setDescription(self, value):
        '''Set the description.'''
        self._gdalDataset.SetDescription(value)

    def description(self):
        '''Returns the description.'''
        return self._gdalDataset.GetDescription()

    def metadataDomainList(self):
        '''Returns the list of metadata domain names.'''
        domains = self._gdalDataset.GetMetadataDomainList()
        return domains if domains is not None else []

    def metadataItem(self, key, domain='', dtype=str, required=False, default=None):
        '''Returns the value (casted to a specific ``dtype``) of a metadata item.'''
        key = key.replace(' ', '_')
        gdalString = self._gdalDataset.GetMetadataItem(key, domain)
        if gdalString is None:
            if required:
                raise Exception('missing metadata item: key={}, domain={}'.format(key, domain))
            return default
        return MetadataFormatter.stringToValue(gdalString, dtype=dtype)

    def metadataDomain(self, domain=''):
        '''Returns the metadata dictionary for the given ``domain``.'''
        metadataDomain = dict()
        for key in self._gdalDataset.GetMetadata(domain):
            key = key.replace('_', ' ')
            metadataDomain[key] = self.metadataItem(key=key, domain=domain)
        return metadataDomain

    def metadataDict(self):
        '''Returns the metadata dictionary for all domains.'''
        metadataDict = dict()
        for domain in self.metadataDomainList():
            metadataDict[domain] = self.metadataDomain(domain=domain)
        return metadataDict

    def setMetadataItem(self, key, value, domain=''):
        '''Set a metadata item. ``value`` can be a string, a number or a list of strings or numbers.'''
        if value is None:
            return
        key = key.replace(' ', '_').strip()
        if domain.upper() == 'ENVI' and key.lower() == 'file_compression':
            return
        gdalString = MetadataFormatter.valueToString(value)
        self._gdalDataset.SetMetadataItem(key, gdalString, domain)

    def setMetadataDomain(self, metadataDomain, domain):
        '''Set the metadata domain'''
        assert isinstance(metadataDomain, dict)
        for key, value in metadataDomain.items():
            self.setMetadataItem(key=key, value=value, domain=domain)

    def setMetadataDict(self, metadataDict):
        '''Set the metadata dictionary'''
        assert isinstance(metadataDict, dict)
        for domain, metadataDomain in metadataDict.items():
            self.setMetadataDomain(metadataDomain=metadataDomain, domain=domain)
            # for key, value in metadataDict[domain].items():
            #    self.setMetadataItem(key=key, value=value, domain=domain)

    def copyMetadata(self, other):
        '''Copy raster and raster band metadata from other to self.'''

        assert isinstance(other, RasterDataset)

        for domain in other.metadataDomainList():
            self.gdalDataset().SetMetadata(other.gdalDataset().GetMetadata(domain), domain)

        for band, otherBand in zip(self.bands(), other.bands()):
            for domain in otherBand.metadataDomainList():
                band.gdalBand().SetMetadata(otherBand.gdalBand().GetMetadata(domain), domain)

    def setAcquisitionTime(self, acquisitionTime):
        '''Set the acquisition time. Store it as 'acquisition time' metadata item inside the 'ENVI' domain.

        :param acquisitionTime:
        :type acquisitionTime:  datetime.datetime
        '''

        assert isinstance(acquisitionTime, datetime.datetime)
        self.setMetadataItem(key='acquisition time', value=str(acquisitionTime), domain='ENVI')

    def acquisitionTime(self):
        '''Returns the acquisition time. Restore it from 'acquisition time' metadata item inside the 'ENVI' domain.

        :return:
        :rtype: datetime.datetime
        '''

        value = self.metadataItem(key='acquisition time', domain='ENVI')
        year, month, day = value[0:10].split('-')
        hour, minute, second = value[11:19].split(':')
        acquisitionTime = datetime.datetime(year=int(year), month=int(month), day=int(day), hour=int(hour),
                                            minute=int(minute), second=int(second))
        return acquisitionTime

    '''def writeENVIHeader(self): # this won't work for files written to /vsimem/

        Creates an ENVI header file containing all metadata of the 'ENVI' metadata domain.
        This ensures the correct interpretation of all metadata items by the ENVI software.
        Currently only ENVI and GTiff formats are supported.

        filename = self._gdalDataset.GetFileList()[0]
        driver = self.driver()
        if driver.equal(other=ENVIBSQDriver()):
            fileType = self.metadataItem(key='file type', domain='ENVI')
            filenameHeader = self._gdalDataset.GetFileList()[-1]
        elif driver.equal(other=GTiffDriver()):
            fileType = 'TIFF'
            filenameHeader = filename + '.hdr'
        else:
            return

        metadata = self.gdalDataset().GetMetadata('ENVI')
        metadata['file type'] = fileType
        metadata['samples'] = self._gdalDataset.RasterXSize
        metadata['lines'] = self._gdalDataset.RasterYSize
        metadata['bands'] = self._gdalDataset.RasterCount
        self._gdalDataset = None

        # copy map info and coordinate system string written by GDAL
        if driver.equal(other=ENVIBSQDriver()):
            metadataOnDisk = ENVI.readHeader(filenameHeader=filenameHeader)
            for key in ['map info', 'coordinate system string']:
                metadata[key] = metadataOnDisk[key]

        # create ENVI header
        ENVI.writeHeader(filenameHeader=filenameHeader, metadata=metadata)'''

    def warp(self, grid, filename='', driver=None, options=None, **kwargs):
        '''Returns a new instance of self warped into the given grid.

        :param grid:
        :type grid: Grid
        :param filename: output filename
        :type filename: str
        :param driver:
        :type driver: RasterDriver
        :param options: creation options
        :type options:
        :param kwargs: passed to gdal.WarpOptions
        :type kwargs:
        :return:
        :rtype: hubdc.core.RasterDataset
        '''

        assert isinstance(grid, Grid)
        if driver is None:
            driver = RasterDriver(name='MEM')
        if not driver.equal(other=RasterDriver(name='MEM')) and not exists(dirname(filename)):
            makedirs(dirname(filename))

        bb = grid.extent().boundingBox()
        outputBounds = (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
        warpOptions = gdal.WarpOptions(format=driver.name(), outputBounds=outputBounds, xRes=grid.resolution().x(),
                                       yRes=grid.resolution().y(), dstSRS=grid.extent().projection().wkt(),
                                       creationOptions=options, **kwargs)
        gdalDataset = gdal.Warp(destNameOrDestDS=filename, srcDSOrSrcDSTab=self._gdalDataset, options=warpOptions)

        return RasterDataset(gdalDataset=gdalDataset)

    def translate(self, grid=None, filename='', driver=None, options=None, **kwargs):
        '''Returns a new instance of self translated into the given ``grid`` (default is self.grid()).

        :param grid:
        :type grid: hubdc.core.Grid
        :param filename:
        :type filename: str
        :param driver:
        :type driver: hubdc.core.RasterDriver
        :param options:
        :type options: hubdc.core.RasterCreationOptions
        :param kwargs: passed to gdal.TranslateOptions
        :type kwargs:
        :return:
        :rtype: hubdc.core.RasterDataset
        '''

        if grid is None:
            grid = self.grid()

        assert isinstance(grid, Grid)
        assert self.grid().extent().projection().equal(other=grid.extent().projection())
        assert isinstance(driver, RasterDriver)

        if not driver.equal(other=RasterDriver(name='MEM')) and not exists(dirname(filename)):
            makedirs(dirname(filename))

        ul = grid.extent().upperLeft()
        lr = grid.extent().lowerRight()
        xRes, yRes = grid.resolution().x(), grid.resolution().y()

        # Note that given a projWin, it is not garantied that gdal.Translate will produce a dataset
        # with the same extent as gdal.Warp!
        # The problem seams to only appear if the target resolution is smaller than the source resolution.

        isOversamplingCase = self.grid().resolution().x() > xRes or self.grid().resolution().y() > yRes
        if isOversamplingCase:
            if not driver.equal(other=RasterDriver(name='MEM')):
                raise Exception('spatial resolution oversampling is only supported for MEM format')

            # read one extra source column and line
            translateOptions = gdal.TranslateOptions(format=driver.name(), creationOptions=options.optionsList(),
                                                     projWin=[ul.x(), ul.y(), lr.x() + self.grid().resolution().x(),
                                                              lr.y() - self.grid().resolution().y()],
                                                     xRes=xRes, yRes=yRes, **kwargs)
            tmpGdalDataset = gdal.Translate(destName='', srcDS=self._gdalDataset, options=translateOptions)

            # subset to the exact target grid
            ysize, xsize = grid.shape()
            translateOptions = gdal.TranslateOptions(format=driver.name(), creationOptions=options.optionsList(),
                                                     srcWin=[0, 0, xsize, ysize])
            gdalDataset = gdal.Translate(destName='', srcDS=tmpGdalDataset, options=translateOptions)

        else:

            translateOptions = gdal.TranslateOptions(format=driver.name(), creationOptions=options.optionsList(),
                                                     projWin=[ul.x(), ul.y(), lr.x(), lr.y()],
                                                     # projWin=[ul.x(), min(ul.y(), lr.y()),
                                                     #         lr.x(), max(ul.y(), lr.y())],

                                                     xRes=xRes, yRes=yRes, **kwargs)
            gdalDataset = gdal.Translate(destName=filename, srcDS=self._gdalDataset, options=translateOptions)

        return RasterDataset(gdalDataset=gdalDataset)

    def xsize(self):
        '''Returns raster x size in pixels.'''
        return self._gdalDataset.RasterXSize

    def ysize(self):
        '''Returns raster y size in pixels.'''
        return self._gdalDataset.RasterYSize

    def zsize(self):
        '''Returns raster z size in terms of number of raster bands.'''
        return self._gdalDataset.RasterCount

    def shape(self):
        '''Returns the ``(zsize, ysize, xsize)`` tuple.'''
        return self.zsize(), self.ysize(), self.xsize()

    def dtype(self):
        '''Returns the raster data type.'''
        return self._gdalDataset.GetRasterBand(1).ReadAsArray(win_xsize=1, win_ysize=1).dtype.type

class MetadataFormatter(object):
    '''Class for managing GDAL metadata value formatting.'''

    @classmethod
    def valueToString(cls, value):
        '''Returns a string representation of value.'''

        if isinstance(value, (list, tuple)):
            return cls._listToString(value)
        else:
            return str(value)

    @classmethod
    def stringToValue(cls, string, dtype):
        '''
        Returns a representation of ``string`` as value of given ``dtype``.
        If ``string`` represents a list of values in curly brackets (e.g. ``{1, 2, 3}``),
        a list of values is returned.
        '''

        string.strip()
        if string.startswith('{') and string.endswith('}'):
            value = cls._stringToList(string, dtype)
        else:
            value = dtype(string)
        return value

    @classmethod
    def _listToString(cls, values):
        return '{' + ', '.join([str(v) for v in values]) + '}'

    @classmethod
    def _stringToList(cls, string, type):
        values = [type(v.strip()) for v in string[1:-1].split(',')]
        return values


class RasterBandDataset():
    '''Class for managing raster band datasets.'''

    def __init__(self, raster, index):
        '''Creating a new instance given a :class:`~hubdc.model.Raster` and a raster band ``index``.'''
        assert isinstance(raster, RasterDataset)
        if index < 0 or index > raster.zsize() - 1:
            raise IndexError()

        self._raster = raster
        self._index = index
        self._gdalBand = raster._gdalDataset.GetRasterBand(index + 1)

    def __repr__(self):
        return '{cls}(raster={raster}, index={index})'.format(
            cls=self.__class__.__name__,
            raster=repr(self.raster()),
            index=repr(self.index()))

    def raster(self):
        '''Returns the :class:`~hubdc.core.RasterDataset`.'''
        assert isinstance(self._raster, RasterDataset)
        return self._raster

    def index(self):
        '''Returns the raster band index.'''
        return self._index

    def gdalBand(self):
        '''Return the gdal.Band.'''
        return self._gdalBand

    def readAsArray(self, grid=None, resample_alg=gdal.GRA_NearestNeighbour):
        '''Returns raster band data as 2d array.

        :param grid: if provided, only data inside the grid extent is returned.
        :type grid: hubdc.core.Grid
        :param resampleAlg: one of the GDAL resampling algorithms (i.e. gdal.GRA_*)
        :type resampleAlg: int
        :return:
        :rtype: numpy.ndarray
        '''

        if grid is None:
            array = self._gdalBand.ReadAsArray(resample_alg=resample_alg)
        else:
            assert isinstance(grid, Grid)
            resolution = self._raster.grid().resolution()
            extent = self._raster.grid().extent()
            xoff = round((grid.extent().xmin() - extent.xmin()) / resolution.x(), 0)
            yoff = round((extent.ymax() - grid.extent().ymax()) / resolution.y(), 0)
            xsize = round((grid.extent().xmax() - grid.extent().xmin()) / resolution.x(), 0)
            ysize = round((grid.extent().ymax() - grid.extent().ymin()) / resolution.y(), 0)
            buf_ysize, buf_xsize = grid.shape()
            array = self._gdalBand.ReadAsArray(xoff=xoff, yoff=yoff, win_xsize=xsize, win_ysize=ysize,
                                               buf_xsize=buf_xsize, buf_ysize=buf_ysize,
                                               resample_alg=resample_alg)
            if array is None or xoff < 0 or yoff < 0:  # ReadAsArray seams to accept xy offets of -1, which makes no sense, so we manually raise an error
                raise errors.AccessGridOutOfRangeError()

        assert isinstance(array, np.ndarray)
        assert array.ndim == 2
        return array

    def writeArray(self, array, grid=None):
        '''Writes raster data.

        :param array:
        :type array: 3d array | list of 2d arrays
        :param grid: if provided, data is written to the location given by the grid extent
        :type grid: hubdc.core.Grid
        '''

        assert isinstance(array, np.ndarray)
        if array.ndim == 3:
            assert len(array) == 1
            array = array[0]

        if grid is None:
            grid = self._raster.grid()

        assert isinstance(grid, Grid)
        if array.shape != grid.shape():
            raise errors.ArrayShapeMismatchError()

        assert self._raster.grid().extent().projection().equal(other=grid.extent().projection())

        gridbb = grid.extent().boundingBox()
        rasterbb = self._raster.grid().extent().boundingBox()
        xoff = int(round((gridbb.xmin - rasterbb.xmin) /
                         self._raster.grid().resolution().x(), 0))
        yoff = int(round((rasterbb.ymax - gridbb.ymax) /
                         self._raster.grid().resolution().y(), 0))
        try:
            self._gdalBand.WriteArray(array, xoff=xoff, yoff=yoff)
        except ValueError:
            raise errors.AccessGridOutOfRangeError

    def fill(self, value):
        '''Write constant ``value`` to the whole raster band.'''
        self._gdalBand.Fill(value)

    def setMetadataItem(self, key, value, domain=''):
        '''Set a metadata item. ``value`` can be a string, a number or a list of strings or numbers.'''

        if value is None:
            return
        key = key.replace(' ', '_')
        gdalString = MetadataFormatter.valueToString(value)
        self._gdalBand.SetMetadataItem(key, gdalString, domain)

    def metadataItem(self, key, domain='', dtype=str):
        key = key.replace(' ', '_')
        gdalString = self._gdalBand.GetMetadataItem(key, domain)
        if gdalString is None:
            return None
        return MetadataFormatter.stringToValue(gdalString, dtype=dtype)

    def copyMetadata(self, other):
        '''Copy raster and raster band metadata from self to other '''

        assert isinstance(other, RasterBandDataset)

        for domain in other.metadataDomainList():
            self._gdalBand.SetMetadata(other._gdalBand.GetMetadata(domain), domain)

    def setNoDataValue(self, value):
        '''Set no data value.'''
        if value is not None:
            self._gdalBand.SetNoDataValue(float(value))

    def noDataValue(self, default=None, required=False):
        '''Returns band no data value, or ``default`` if no data value is unfefined.'''
        noDataValue = self._gdalBand.GetNoDataValue()
        if noDataValue is None:
            noDataValue = default
        if noDataValue is None and required:
            raise Exception('required no data value is missing')
        return noDataValue

    def setDescription(self, value):
        '''Set band description.'''
        self._gdalBand.SetDescription(value)

    def description(self):
        '''Returns band description.'''
        return self._gdalBand.GetDescription()

    def setCategoryNames(self, names):
        '''Set band category names.'''
        if names is not None:
            self._gdalBand.SetCategoryNames(names)

    def categoryNames(self):
        '''Returns band category names.'''
        names = self._gdalBand.GetCategoryNames()
        return names

    def setCategoryColors(self, colors):
        '''Set band category colors from list of rgba tuples.'''
        if colors is not None:
            colorTable = gdal.ColorTable()
            for i, color in enumerate(colors):
                assert isinstance(color, tuple)
                if len(color) == 3:
                    color = color + (255,)
                assert len(color) == 4
                colorTable.SetColorEntry(i, color)
            self._gdalBand.SetColorTable(colorTable)

    def categoryColors(self):
        '''Returns band category colors as list of rgba tuples.'''
        colorTable = self._gdalBand.GetColorTable()
        if colorTable is not None:
            colors = list()
            for i in range(colorTable.GetCount()):
                rgba = colorTable.GetColorEntry(i)
                colors.append(rgba)
        else:
            colors = None
        return colors

    def metadataDomainList(self):
        '''Returns the list of metadata domain names.'''
        domains = self._gdalBand.GetMetadataDomainList()
        return domains if domains is not None else []


class VectorDataset(object):

    def __init__(self, ogrDataSource, layerNameOrIndex=0):
        '''Creates new instance from given ogr.DataSource and layer name or index given by ``nameOrIndex``.'''

        assert isinstance(ogrDataSource, ogr.DataSource), str(ogrDataSource)
        self._ogrDataSource = ogrDataSource
        self._ogrLayer = ogrDataSource.GetLayer(iLayer=layerNameOrIndex)
        self._filename = self._ogrDataSource.GetDescription()
        self._layerNameOrIndex = layerNameOrIndex
        self._reprojectionCache = dict()

    def __repr__(self):

        return '{cls}(ogrDataSource={ogrDataSource}, layerNameOrIndex={layerNameOrIndex})'.format(
            cls=self.__class__.__name__,
            ogrDataSource=repr(self.ogrDataSource()),
            layerNameOrIndex=repr(self.layerNameOrIndex()))

    def filename(self):
        '''Returns the filename.'''
        return self._filename

    def layerNameOrIndex(self):
        '''Returns the layer name/index.'''
        return self._layerNameOrIndex

    def ogrDataSource(self):
        '''Returns the ogr.DataSource.'''
        return self._ogrDataSource

    def ogrLayer(self):
        '''Retrurns the ogr.Layer.'''
        assert isinstance(self._ogrLayer, ogr.Layer)
        return self._ogrLayer

    def close(self):
        '''Closes the ogr.DataSourse and ogr.Layer'''
        self._ogrLayer = None
        self._ogrDataSource = None

    def projection(self):
        '''Returns the :class:`~hubdc.model.Projection`.'''
        return Projection(wkt=self._ogrLayer.GetSpatialRef())

    def rasterize(self, grid, gdalType=gdal.GDT_Float32,
                  initValue=0, burnValue=1, burnAttribute=None, allTouched=False,
                  filterSQL=None, noDataValue=None,
                  filename='', driver=None, options=None):
        '''Returns a :class:`~hubdc.model.Raster` that is the rasterization of self into the given ``grid`` as.

        :param grid:
        :type grid: hubdc.core.Grid
        :param gdalType: one of the GDAL data types gdal.GDT_*
        :type gdalType: int
        :param initValue: value to pre-initialize the output array
        :type initValue: int
        :param burnValue: value to burn into the output array for all objects; exclusive with ``burnAttribute``
        :type burnValue: int
        :param burnAttribute: identifies an attribute field on the features to be used for a burn-in value; exclusive with ``burnValue``
        :type burnAttribute: str
        :param allTouched: whether to enable that all pixels touched by lines or polygons will be updated, not just those on the line render path, or whose center point is within the polygon
        :type allTouched: bool
        :param filterSQL: set an SQL WHERE clause which will be used to filter vector features
        :type filterSQL: str
        :param noDataValue: output raster no data value
        :type noDataValue: float
        :param filename: output filename
        :type filename: str
        :param driver:
        :type driver: RasterDriver
        :param options: creation options
        :type options:
        :return:
        :rtype: RasterDataset
        '''

        assert isinstance(grid, Grid)
        if driver is None:
            driver = RasterDriver.MEM()
        assert isinstance(driver, RasterDriver)

        if self.projection().equal(other=grid.extent().projection()):
            vector = self
        else:
            if not grid.extent().projection().wkt() in self._reprojectionCache:
                self._reprojectionCache[grid.extent().projection().wkt()] = self.reprojectOnTheFly(projection=grid.extent().projection())
            vector = self._reprojectionCache[grid.extent().projection().wkt()]

        vector.ogrLayer().SetAttributeFilter(filterSQL)
        vector.ogrLayer().SetSpatialFilter(grid.extent().ogrGeometry())

        if not driver.equal(other=RasterDriver.MEM()) and not exists(dirname(filename)):
            makedirs(dirname(filename))

        rasterDataset = RasterDataset.fromSpecification(grid=grid, bands=1, gdalType=gdalType, filename=filename, options=options)

        if noDataValue is not None:
            rasterDataset.setNoDataValue(noDataValue)
        rasterDataset.band(index=0).fill(value=initValue)

        rasterizeLayerOptions = list()
        # special options controlling rasterization:
        #    "ATTRIBUTE": Identifies an attribute field on the features to be used for a burn in value. The value will be burned into all output bands. If specified, padfLayerBurnValues will not be used and can be a NULL pointer.
        #    "CHUNKYSIZE": The height in lines of the chunk to operate on. The larger the chunk size the less times we need to make a pass through all the shapes. If it is not set or set to zero the default chunk size will be used. Default size will be estimated based on the GDAL cache buffer size using formula: cache_size_bytes/scanline_size_bytes, so the chunk will not exceed the cache.
        #    "ALL_TOUCHED": May be set to TRUE to set all pixels touched by the line or polygons, not just those whose center is within the polygon or that are selected by brezenhams line algorithm. Defaults to FALSE.
        #    "BURN_VALUE_FROM": May be set to "Z" to use the Z values of the geometries. The value from padfLayerBurnValues or the attribute field value is added to this before burning. In default case dfBurnValue is burned as it is. This is implemented properly only for points and lines for now. Polygons will be burned using the Z value from the first point. The M value may be supported in the future.
        #    "MERGE_ALG": May be REPLACE (the default) or ADD. REPLACE results in overwriting of value, while ADD adds the new value to the existing raster, suitable for heatmaps for instance.
        if allTouched:
            rasterizeLayerOptions.append('ALL_TOUCHED=TRUE')
        if burnAttribute:
            rasterizeLayerOptions.append('ATTRIBUTE=' + burnAttribute)

        gdal.RasterizeLayer(rasterDataset.gdalDataset(), [1], vector.ogrLayer(), burn_values=[burnValue],
                            options=rasterizeLayerOptions)
        vector.ogrLayer().SetAttributeFilter(None)
        return rasterDataset

    def reprojectOnTheFly(self, projection):
        '''Returns a reprojection of self into the given :class:`~hubdc.model.Projection`.'''

        #todo do this in memory!!!

        # need to temporary create a VRT file
        vrtDefinition = ['<OGRVRTDataSource>\n',
                         '    <OGRVRTWarpedLayer>\n',
                         '        <OGRVRTLayer name="{}">\n'.format(basename(self.filename()).replace('.shp', '')),
                         '            <SrcDataSource>{ds}</SrcDataSource>\n'.format(ds=self.filename()),
                         '        </OGRVRTLayer>\n',
                         '        <TargetSRS>{}</TargetSRS>\n'.format(projection.wkt()),
                         '    </OGRVRTWarpedLayer>\n',
                         '</OGRVRTDataSource>\n']

        vrtFilename = join(tempfile.gettempdir(), str(randint(0, 10 ** 10)) + '.vrt')
        with open(vrtFilename, 'w') as f:
            f.writelines(vrtDefinition)

        # open VRT vector file
        ogrDataSource = ogr.Open(vrtFilename)
        assert ogrDataSource is not None
        vector = VectorDataset(ogrDataSource=ogrDataSource, layerNameOrIndex=0)

        # delete the VRT file
        remove(vrtFilename)

        # todo cache result

        return vector

    def featureCount(self):
        '''Returns the number of features.'''
        return self._ogrLayer.GetFeatureCount()

    def fieldCount(self):
        '''Returns the number of attribute fields.'''
        return self._ogrLayer.GetLayerDefn().GetFieldCount()

    def fieldNames(self):
        '''Returns the attribute field names.'''
        names = [self._ogrLayer.GetLayerDefn().GetFieldDefn(i).GetName() for i in range(self.fieldCount())]
        return names

    def fieldTypeNames(self):
        '''Returns the attribute field data type names.'''
        typeNames = [self._ogrLayer.GetLayerDefn().GetFieldDefn(i).GetTypeName() for i in range(self.fieldCount())]
        return typeNames

    def zsize(self):
        '''Returns number of layers (i.e. 1).'''
        return 1


class RasterDriver(object):
    '''Class for managing GDAL Drivers'''


    def __init__(self, name):
        self._name = name
        assert self.gdalDriver() is not None

    def __repr__(self):
        return '{cls}(name={name})'.format(cls=self.__class__.__name__, name=repr(self.name()))

    @staticmethod
    def MEM():
        return RasterDriver(name='MEM')

    @classmethod
    def fromFilename(cls, filename):

        ext = splitext(filename)[1][1:].lower()
        if filename == '':
            name = 'MEM'
        elif ext == 'tif':
            name = 'GTiff'
        else:
            name = 'ENVI'
        return RasterDriver(name=name)

    def gdalDriver(self):
        '''Returns the GDAL driver object.'''
        return gdal.GetDriverByName(self._name)

    def name(self):
        '''Returns the driver name.'''
        return self._name

    def equal(self, other):
        '''Returns whether self is equal to the other driver.'''
        assert isinstance(other, RasterDriver)
        return self.name() == other.name()


def createVRTDataset(rasterDatasetsOrFilenames, filename='', **kwargs):
    '''
    Creates a virtual raster file (VRT) from raster datasets or filenames given by ``rastersOrFilenames``.

    :param filename: output filename
    :type filename: str
    :param rastersOrFilenames: list of filenames or rasters
    :type rastersOrFilenames:
    :param kwargs: passed to gdal.BuildVRTOptions
    :type kwargs:
    :return:
    :rtype: RasterDataset
    '''

    srcDSOrSrcDSTab = list()
    for rasterDatasetsOrFilename in rasterDatasetsOrFilenames:
        if isinstance(rasterDatasetsOrFilename, RasterDataset):
            srcDSOrSrcDSTab.append(rasterDatasetsOrFilename.gdalDataset())
        elif isinstance(rasterDatasetsOrFilename, str):
            srcDSOrSrcDSTab.append(rasterDatasetsOrFilename)
        else:
            assert 0

    options = gdal.BuildVRTOptions(**kwargs)
    gdalDataset = gdal.BuildVRT(destName=filename, srcDSOrSrcDSTab=srcDSOrSrcDSTab, options=options)
    return RasterDataset(gdalDataset=gdalDataset)

class Table(object):

    def __init__(self, data, names):
        assert isinstance(data, np.ndarray)
        assert data.ndim == 2 # [samples, features]
        assert data.shape[1] == len(names)
        self.data = data
        self.names = names

class Classifier(object):

    def __init__(self, sklClassifier):
        assert isinstance(sklClassifier, ClassifierMixin)
        self._sklClassifier = sklClassifier

    def fit(self, features, classProperty, inputProperties):
        assert isinstance(features, Table)
        self._inputProperties = inputProperties
        X = np.float64(features.data[:,[features.names.index(name) for name in inputProperties]])
        y = np.uint32(features.data[:, features.names.index(classProperty)])
        self._sklClassifier.fit(X=X, y=y)
        return self


def createPoint(x, y, projection):
    return Geometry(wkt='Point({} {})'.format(x, y), projection=projection)

def openRasterDataset(filename, eAccess=gdal.GA_ReadOnly):
    '''
    Opens the raster given by ``filename``.

    :param filename: input filename
    :type filename: str
    :param eAccess: access mode ``gdal.GA_ReadOnly`` or ``gdal.GA_Update``
    :type eAccess: int
    :return:
    :rtype: hubdc.core.RasterDataset
    '''

    assert isinstance(filename, str), type(filename)
    if not filename.startswith('/vsimem/') and not exists(filename):
        raise errors.FileNotExistError(filename)
    gdalDataset = gdal.Open(filename, eAccess)

    if gdalDataset is None:
        raise errors.InvalidGDALDatasetError(filename)

    return RasterDataset(gdalDataset=gdalDataset)

def openVectorDataset(filename, layerNameOrIndex=0, update=False):
    '''
    Opens the vector layer given by ``filename`` and ``layerNameOrIndex``.

    :param filename: input filename
    :type filename: str
    :param layerNameOrIndex: layer index or name
    :type layerNameOrIndex: int | str
    :param update: whether to open in update mode
    :type update: bool
    :return:
    :rtype: hubdc.core.VectorDataset
    '''

    assert isinstance(filename, str), type(filename)
    if not exists(filename):
        raise errors.FileNotExistError(filename)
    if str(layerNameOrIndex).isdigit():
        layerNameOrIndex = int(layerNameOrIndex)
    ogrDataSource = ogr.Open(filename, int(update))
    if ogrDataSource is None:
        raise errors.InvalidOGRDataSourceError(filename)

    return VectorDataset(ogrDataSource=ogrDataSource, layerNameOrIndex=layerNameOrIndex)
