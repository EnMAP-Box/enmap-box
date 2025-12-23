from os.path import join, basename, dirname
import numpy as np
from osgeo import gdal

class EEException(Exception):
    pass


class ComputedObject(object):

    def __init__(self, cls, func, args, opt_varName=None):

        if opt_varName and (func or args):
            raise EEException('When "opt_varName" is specified, "func" and "args" must be null.')
        self.func = '{}.{}'.format(cls.__name__, func.__name__)
        self.args = args
        self.varName = opt_varName

    def getInfo(self):
        """Fetch and return information about this object."""

        cls, method = 'Backend{}'.format(self.func).split('.')
        cls = eval(cls)
        #if hasattr(cls, method): # static method
        result = getattr(cls, method)(**self.args)
        #else: # instance method
        #    result =1

        #result = func(**self.args)
        info = result.getInfo()
        return info

class Element(ComputedObject):
  """Base class for ImageCollection and FeatureCollection."""

  def __init__(self, cls, func, args, opt_varName=None):
    """Constructs a collection by initializing its ComputedObject."""
    ComputedObject.__init__(self, cls=cls, func=func, args=args, opt_varName=opt_varName)


class Image(Element):
    """An object to represent an Earth Engine image."""

    def __init__(self, args=None):
        """Constructs an Earth Engine image.

        args: This constructor accepts a variety of arguments:
          - A string - an EarthEngine asset id,
          - A string and a number - an EarthEngine asset id and version,
          - A number - creates a constant image,
          - An EEArray - creates a constant array image,
          - A list - creates an image out of each element of the array and
            combines them into a single image,
          - An ee.Image - returns the argument,
          - Nothing - results in an empty transparent image.

        """

        if isinstance(args, (int, float)):
            # A constant image.
            Element.__init__(self, cls=Image, func=Image.constant, args={'value': args})
        elif isinstance(args, str):
            # An ID.
            Element.__init__(self, cls=Image, func=Image.load, args={'id': args})
        else:
          raise EEException('Unrecognized argument type to convert to an Image: %s'.format(args))

    @staticmethod
    def load(id):
        assert isinstance(id, str)
        return Image(args=id)

    def getInfo(self):
        """Fetch and return information about this image."""
        return Element.getInfo(self)

    def select(self, opt_selectors=None, opt_names=None, *args):
        """Selects bands from an image.

        Can be called in one of two ways:
            - Passed any number of non-list arguments. All of these will be
              interpreted as band selectors. These can be band names, regexes, or
              numeric indices. E.g.
              selected = image.select('a', 'b', 3, 'd');
            - Passed two lists. The first will be used as band selectors and the
              second as new names for the selected bands. The number of new names
              must match the number of selected bands. E.g.
              selected = image.select(['a', 4], ['newA', 'newB']);

        Args:
            opt_selectors: An array of names, regexes or numeric indices specifying
                the bands to select.
            opt_names: An array of strings specifying the new names for the
                selected bands.
            *args: Selector elements as varargs.

        Returns:
          An image with the selected bands.
        """
        if opt_selectors is not None:
          args = list(args)
          if opt_names is not None:
            args.insert(0, opt_names)
          args.insert(0, opt_selectors)
        algorithm_args = {
            'input': self,
            'bandSelectors': args[0] if args else [],
        }
        if args:
          # If the user didn't pass an array as the first argument, assume
          # that everything in the arguments array is actually a selector.
          if (len(args) > 2 or isString(args[0]) or isNumber(args[0])):
            # Varargs inputs.
            selectors = args
            # Verify we didn't get anything unexpected.
            for selector in selectors:
              if (not isString(selector) and
                  not isNumber(selector) and
                  not isinstance(selector, ComputedObject)):
                raise EEException('Illegal argument to select(): {}'.format(selector))
            algorithm_args['bandSelectors'] = selectors
          elif len(args) > 1:
            algorithm_args['newNames'] = args[1]

        # create element and coerse type to
        image = Element(cls=Image, func=Image.select, args=algorithm_args)
        image.__class__ = Image
        return image

def isString(obj):
    return isinstance(obj, str)

def isNumber(obj):
    return isinstance(obj, (int, float))


class BackendBand(object):

    def __init__(self, filename, id, data_type, dimensions, crs, crs_transform):
        self.filename = filename
        self.id = id
        self.data_type = data_type
        self.dimensions = dimensions
        self.crs = crs
        self.crs_transform = crs_transform


class BackendImage(object):

    def __init__(self, args=None):
        self.type = 'Image'
        self.bands = list()

        if isinstance(args, (int, float)):
            assert 0
        elif isinstance(args, str):
            self.id = args
            for bandid in ['B{}'.format(i+1) for i in range(11)] + ['BQA']:
                filename = join(self.id, '{}.{}.tif'.format(basename(self.id), bandid))

                if bandid == 'B1':
                    ds = gdal.Open(filename)
                    dimensions = ds.RasterXSize, ds.RasterYSize
                    crs = str(ds.GetProjection())
                    crs = 'EPSG:' + ''.join([c for c in crs.split('EPSG')[-1] if c in '0123456789'])
                    crs_transform = ds.GetGeoTransform()

                self.bands.append(BackendBand(filename=filename, id=bandid, data_type=np.float32, dimensions=dimensions, crs=crs, crs_transform=crs_transform))
            self.properties = {'dummy': 123}
        else:
            raise EEException('Unrecognized argument type to convert to an Image: %s'.format(args))

    @staticmethod
    def load(id):
        assert isinstance(id, str)
        return BackendImage(args=id)

    def getInfo(self):
        info = dict()
        info['type'] = self.type
        info['id'] = self.id
        info['bands'] = list()
        for band in self.bands:
            assert isinstance(band, BackendBand)
            bandInfo = dict()
            bandInfo['id'] = band.id
            bandInfo['data_type'] = band.data_type
            bandInfo['dimensions'] = band.dimensions
            bandInfo['crs'] = band.crs
            bandInfo['crs_transform'] = band.crs_transform
            info['bands'].append(bandInfo)
        info['properties'] = self.properties
        return info

    def select(input, bandSelectors):
        pass
        a=1