class HubDcError(Exception):
    '''Generic HUB Datacube error.'''



class ObjectParserError(HubDcError):
    '''Object cannot be interpreted as specific type.'''
    def __init__(self, obj, type):
        Exception.__init__(self, 'ObjectParserError: {} cannot be parsed as {} object'.format(obj, type))

class TypeError(HubDcError):
    '''Object has invalid type.'''
    def __init__(self, obj):
        HubDcError.__init__(self, 'TypeError: invalid type ({})'.format(type(obj)))

class IndexError(HubDcError):
    '''Invalid index.'''
    def __init__(self, index, min, max):
        HubDcError.__init__(self, 'IndexError: index {} not in valid range [{}, {}]'.format(index, min, max))

class InvalidRasterSize(HubDcError):
    '''Raster size must be greater than zero.'''

class GeometryIntersectionError(HubDcError):
    '''Geometries do not intersect.'''

class AccessGridOutOfRangeError(HubDcError):
    '''Read or write access grid is out of dataset grid range.'''


class ArrayShapeMismatchError(HubDcError):
    '''Array shape is not matching the expected shape.'''

class FileNotExistError(HubDcError):
    '''File not exist.'''


class FileOpenError(HubDcError):
    '''Failed to open an input or output file.'''


class InvalidGDALDatasetError(HubDcError):
    '''gdal.Open returned None.'''


class InvalidGDALDriverError(HubDcError):
    '''gdal.GetDriverByName returned None.'''


class InvalidOGRDriverError(HubDcError):
    '''ogr.GetDriverByName returned None.'''


class InvalidOGRDataSourceError(HubDcError):
    '''ogr.Open returned None.'''

class InvalidOGRLayerError(HubDcError):
    '''ogr.Open returned None.'''

class ApplierOperatorTypeError(HubDcError):
    '''Applier operator must be a subclass of :class:`~_classic.hubdc.applier.ApplierOperator` or function.'''


class ApplierOutputRasterNotInitializedError(HubDcError):
    '''Applier output raster is not initialized, use :meth:`~_classic.hubdc.applier.ApplierOutputRaster.initialize`.'''

class MissingNoDataValueError(HubDcError):
    def __init__(self, filename, index):
        HubDcError.__init__(self, 'MissingNoDataValueError: required no data value not found: {} (Band {})'.format(filename, index))

class MissingMetadataItemError(HubDcError):
    def __init__(self, key, domain):
        HubDcError.__init__(self, "MissingNoDataValueError: required metadata item '{}' in domain '{}' not found".format(key, domain))

class MissingApplierProjectionError(HubDcError):
    '''Applier projection was not explicitely set and could not be derived from raster inputs.'''

class MissingApplierExtentError(HubDcError):
    '''Applier extent was not explicitely set and could not be derived from raster inputs.'''

class MissingApplierResolutionError(HubDcError):
    '''Applier resolution was not explicitely set and could not be derived from raster inputs.'''

class UnknownApplierAutoExtentOption(HubDcError):
    '''See :class:`~_classic.hubdc.applier.Options.AutoExtent` for valid options.'''

class UnknownApplierAutoResolutionOption(HubDcError):
    '''See :class:`~_classic.hubdc.applier.Options.AutoResolution` for valid options.'''

class UnknownAttributeTableField(HubDcError):
    def __init__(self, name):
        HubDcError.__init__(self, "UnknownAttributeTableField: field '{}' not found".format(name))
