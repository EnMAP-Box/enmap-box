class GdalMetadataValueFormatter(object):
    """Class for managing GDAL metadata value formatting."""

    @classmethod
    def valueToString(cls, value):
        """Returns a string representation of value."""

        if isinstance(value, (list, tuple)):
            return cls._listToString(value)
        else:
            return str(value)

    @classmethod
    def stringToValue(cls, string, dtype=None):
        """Returns a representation of string as value of given type."""

        if dtype is None:
            dtype = str
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
    def _stringToList(cls, string, type_):
        values = [type_(v.strip()) for v in string[1:-1].split(',')]
        return values