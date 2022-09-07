# -*- coding: utf-8 -*-

"""
***************************************************************************

    ---------------------
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import copy
import re

import numpy as np
from osgeo import gdal, ogr

from enmapbox.gui import ClassificationScheme
from qgis.PyQt.QtCore import QDate
from qgis.core import QgsCoordinateReferenceSystem

IMMUTABLE_DOMAINS = ['IMAGE_STRUCTURE', 'SUBDATASETS', 'DERIVED_SUBDATASETS']


def getKwds(valueType=None, valueMin=None, valueMax=None,
            isImmutable=None, options=None, tooltip=None):
    kwds = {}
    if valueType:
        kwds['valueType'] = valueType
    if valueMin:
        kwds['valueMin'] = valueMin
    if valueMax:
        kwds['valueMax'] = valueMax
    if isImmutable:
        kwds['isImmutable'] = isImmutable
    if options:
        kwds['options'] = options
    if tooltip:
        kwds['tooltip'] = tooltip
    return kwds


regexIsOLI = re.compile(r'(gdal\.(Dataset|Band_[1-9]\d*))|ogr\.(DataSource|Layer_\d+)')


class MDKeyAbstract(object):

    @staticmethod
    def object2oli(obj):
        """
        Creates an object location identifier string which decribes the positon of a MetadataItem
        without keeping a reference to an underlying gdal/ogr object.
        :param obj: gdal.MajorObject | ogr.MajorObject
        :return: str
        """

        if obj is None or not (isinstance(obj, gdal.MajorObject) or isinstance(obj, ogr.MajorObject)):
            return None

        if isinstance(obj, gdal.Dataset):
            oli = 'gdal.Dataset'
        elif isinstance(obj, gdal.Band):
            oli = 'gdal.Band_{}'.format(obj.GetBand())
        elif isinstance(obj, ogr.DataSource):
            oli = 'ogr.DataSource'
        elif isinstance(obj, ogr.Layer):
            oli = 'ogr.Layer_{}'.format(obj.GetRefCount())
        else:
            raise NotImplementedError()

        assert regexIsOLI.search(oli)
        return oli

    @staticmethod
    def oli2obj(oli, majorObject):
        """
        Returns the gdal/ogr object to which a oli refers to
        :param oli: OLI string, e.g. `gdal.Dataset` or `ogr.Layer_0`
        :param majorObject: gdal.MajorObject | ogr.MajorObject
        :return:
        """
        assert isinstance(majorObject, gdal.MajorObject) or isinstance(majorObject, ogr.MajorObject)
        assert isinstance(oli, str)
        assert regexIsOLI.search(oli)
        parts = oli.split('_')

        objStr = parts[0]

        if objStr.startswith('gdal') and not isinstance(majorObject, gdal.MajorObject):
            raise Exception('"majorObject" needs to be of type gdal.MajorObject to use {}'.format(oli))

        if objStr.startswith('ogr') and not isinstance(majorObject, ogr.MajorObject):
            raise Exception('"majorObject" needs to be of type ogr.MajorObject to use {}'.format(oli))

        if objStr == 'gdal.Dataset':
            if isinstance(majorObject, gdal.Dataset):
                return majorObject
            elif isinstance(majorObject, gdal.Band):
                return majorObject.GetDataset()

        elif objStr == 'ogr.DataSource':
            if isinstance(majorObject, ogr.DataSource):
                return majorObject
            elif isinstance(majorObject, ogr.Layer):
                pass
            #    return majorObject.GetDataSource()

        elif objStr == 'gdal.Band':
            b = int(parts[1])
            if isinstance(majorObject, gdal.Band):
                majorObject = majorObject.GetDataset()
            assert isinstance(majorObject, gdal.Dataset)
            assert b <= majorObject.RasterCount
            return majorObject.GetRasterBand(b)

        elif objStr == 'ogr.Layer':
            i = int(parts[1])
            if isinstance(majorObject, ogr.DataSource):
                return majorObject.GetLayer(i)
            elif isinstance(majorObject, ogr.Layer):
                raise NotImplementedError('Can not refere to ogr.DataSource from ogr.Layer')
                return majorObject
        else:
            raise NotImplementedError()
        raise Exception()

    """
    A MDKey is an internal representation of a metadata item.
    It connects a gdal.MajorObject or ogr.MajorObject and a TreeNode.
    It stores DataSet-specific state variables.
    """

    def __init__(self, obj, name, valueType=str, isImmutable=False, options=None, tooltip=None):
        """
        :param name: Name of the Metadata Key
        :param valueType: the type a returned DataSet Value will have in Python, e.g. str, int, MyClass
        :param isImmutable: True, if this Metadata Value can not be changed by a user
        :param options: [list-of-options]
        """
        if isinstance(obj, str) and regexIsOLI.search(obj):
            self.mOLI = obj
        else:
            self.mOLI = MDKeyAbstract.object2oli(obj)

        self.mName = name
        self.mType = valueType
        self.mIsImmutable = isImmutable
        self.mOptions = options
        self.mTooltip = tooltip
        self.mValue0Initialized = False
        self.mValue = None
        self.mValue0 = None

        if isinstance(obj, gdal.MajorObject) or isinstance(obj, ogr.MajorObject):
            self.readValueFromSource(obj)

    def tooltip(self):
        return self.mTooltip

    def isImmutable(self):
        """
        Returns True if the key value can be changed with setValue(value)
        :return: True | False
        """
        return self.mIsImmutable

    def name(self):
        """
        Returns the Metadata key name
        :return: str
        """
        return self.mName

    def value(self):
        """
        Returns the Metadata key value
        :return: <value>
        """
        return self.mValue

    def setValue(self, value):
        """
        Sets the key value if self.isImmutable() == True or if it was not set before.
        :param value: the value to set
        """
        if not self.mValue0Initialized:
            if isinstance(value, QgsCoordinateReferenceSystem):
                self.mValue0 = value
            else:
                self.mValue0 = copy.copy(value)

            self.mValue = self.mValue0
            self.mValue0Initialized = True

        elif not self.mIsImmutable:
            self.mValue = value

    def valueHasChanged(self):
        """
        Returns True if the value was changed
        :return: True | False
        """
        return self.mValue0 != self.mValue

    def readValueFromSource(self, obj):
        """
        Reads a value from a gdal/ogr object `obj
        :param obj: gdal.MajorObject or ogr.MajorObject, e.g. gdal.DataSet or gdal.Band
        :return: None, if Metadata does not exist
        """
        raise NotImplementedError('Abstract class')

    def writeValueToSource(self, obj):
        """
        Converts `value` into something gdal/ogr can write to the gdal/ogr object `obj`.
        :param obj: gdal.MajorObject or ogr.MajorObject, e.g. gdal.Dataset
        :param value: The value to be written, might be of any type
        :return: None (= success) or Exception (= unable to write)
        """
        raise NotImplementedError('Abstract class')

    def __hash__(self):
        return hash(self.mName)

    def __eq__(self, other):
        if isinstance(other, MDKeyDomainString):
            return self.mName == other.mName
        else:
            return False


class MDKeyDomainString(MDKeyAbstract):
    """
    A MDKey provides a link between a gdal.MajorObject or ogr.MajorObject and a TreeNode.
    It does not store any state variables.
    """

    @staticmethod
    def fromDomain(obj, domain: str, name: str, **kwds):
        assert isinstance(domain, str)
        assert isinstance(name, str)

        if type(obj) in [gdal.Dataset, gdal.Band]:

            return MDKeyDomainString.fromRasterDomain(obj, domain, name, **kwds)

        elif type(obj) in [ogr.DataSource, ogr.Layer]:

            return MDKeyDomainString.fromVectorDomain(obj, domain, name, **kwds)

        else:
            raise NotImplementedError()

    @staticmethod
    def fromVectorDomain(obj, domain: str, name: str):

        # OGR Default Domain
        if domain == '':
            # see http://www.gdal.org/drv_shapefile.html
            if name == 'DBF_DATE_LAST_UPDATE':
                return MDKeyDomainString(obj, domain, name, valueType=str)
            else:
                return MDKeyDomainString(obj, domain, name)
        else:
            # default behavior: return a string
            return MDKeyDomainString(obj, domain, name)
            # raise NotImplementedError()

    @staticmethod
    def fromRasterDomain(obj, domain: str, name: str, **kwds):

        # GDAL Default Domain
        if domain == '':

            if name == 'AREA_OR_POINT':
                return MDKeyDomainString(obj, domain, name, isImmutable=True,
                                         options=['Area', 'Point'],
                                         tooltip='Indicates whether a pixel value should be assumed to represent a '
                                                 'sampling over the region of the pixel or a point sample at the center '
                                                 'of the pixel. This is not intended to influence interpretation of '
                                                 'georeferencing which remains area oriented.',
                                         **kwds)

            if name == 'METADATATYPE':
                return MDKeyDomainString(obj, domain, name, isImmutable=True,
                                         tooltip='Describes the reader which processes the metadata if IMAGERY Domain is present.',
                                         **kwds)

        if domain in IMMUTABLE_DOMAINS or domain.startswith('xml:'):
            return MDKeyDomainString(obj, domain, name, isImmutable=True, **kwds)

        # ENVI Domain
        # see http://www.harrisgeospatial.com/docs/enviheaderfiles.html for details
        if domain == 'ENVI':

            if name == 'bands':
                return MDKeyDomainString(obj, domain, name,
                                         valueType=int, valueMin=1, isImmutable=True, **kwds)

            if name == 'sample':
                return MDKeyDomainString(obj, domain, name,
                                         valueType=int, valueMin=1, isImmutable=True, **kwds)

            if name == 'lines':
                return MDKeyDomainString(obj, domain, name,
                                         valueType=int, valueMin=1, isImmutable=True, **kwds)

            if name == 'header_offset':
                return MDKeyDomainString(obj, domain, name,
                                         valueType=int, valueMin=0, **kwds)

            if name == 'data_type':
                return MDKeyDomainString(obj, domain, name,
                                         valueType=int, valueMin=1, valueMax=16, isImmutable=True, **kwds)

            if name == 'data_type':
                return MDKeyDomainString(obj, domain, name,
                                         valueType=int, valueMin=1, valueMax=16, isImmutable=True, **kwds)

            if name == 'interleave':
                return MDKeyDomainString(obj, domain, name,
                                         options=['bsq', 'bil', 'bip'], isImmutable=True, **kwds)

            if name == 'band_names':
                return MDKeyDomainString(obj, domain, name, listLength='nb', **kwds)
            if name == 'bbl':
                return MDKeyDomainString(obj, domain, name, listLength='nb', valueType=int, **kwds)

            if name == 'fwhm':
                return MDKeyDomainString(obj, domain, name, listLength='nb', valueType=float, **kwds)

            if name == 'wavelength':
                return MDKeyDomainString(obj, domain, name, listLength='nb', valueType=float, **kwds)

            if name == 'wavelength_units':
                return MDKeyDomainString(obj, domain, name,
                                         options=[
                                             'Micrometers', 'um', 'Nanometers', 'nm', 'Millimeters', 'mm',
                                             'Centimeters', 'cm',
                                             'Meters', 'm', 'Wavenumber', 'Angstroms', 'GHz', 'MHz', 'Index',
                                             'Unknown'],
                                         **kwds)

            if name == 'cloud_cover':
                return MDKeyDomainString(obj, domain, name, valueType=float, **kwds)

            if name == 'acquisition_time':
                return MDKeyDomainString(obj, domain, name, valueType=np.datetime64, **kwds)

        # try to parse the string as int or float
        if isinstance(obj, gdal.MajorObject) or isinstance(obj, ogr.MajorObject):
            value = obj.GetMetadataItem(name, domain)
            if domain == 'ENVI' and name == 'byte_order':
                s = ""
            if value is not None and len(value) > 0:
                for t in [int, float, np.datetime64, str]:
                    try:
                        v = t(value)
                        break
                    except Exception:
                        pass
                key = MDKeyDomainString(obj, domain, name, valueType=t, **kwds)
                key.setValue(v)
                return key

        return MDKeyDomainString(obj, domain, name, **kwds)

    def __init__(self, obj, domain, name, valueMin=None, valueMax=None,
                 listLength=None, **kwargs):
        """

        :param obj: gdal.MajorObject or ogr.MajorObject
        :param domain: metadata domain name (str)
        :param name: metadata item name
        :param valueMin: metadata minimum value (optional)
        :param valueMax: metadata maximum value (optional)
        :param isImmutable: True | False
        :param listLength: -1, None or listLength > 0
                * None (default) no limitations
                * 'nb' the list needs to have the length of the number of bands or layers
                * 'nc' the list needs to have the length of the number of classes
                * n with n > 0: the list need to have n elements
                * - 1: list-length will be determined from the first call of setValues() or readFromSource()
                the total number of bands
        :param options: a list of possible values
        :param kwargs: other arguments
        """

        self.mDomain = domain
        self.mMin = valueMin
        self.mMax = valueMax
        self.mListLength = listLength

        super(MDKeyDomainString, self).__init__(obj, name, **kwargs)

    def initListLength(self, obj, value):
        if self.mListLength not in [-1, 'nb', 'nl']:
            return

        if self.mListLength in ['nb', 'nl']:
            if isinstance(obj, gdal.Dataset):
                self.mListLength = obj.RasterCount
            elif isinstance(obj, gdal.Dataset):
                self.mListLength = obj.GetDataset().RasterCount
            elif isinstance(obj, ogr.DataSource):
                self.mListLength = obj.LayerCount()
            elif isinstance(obj, ogr.Layer):
                self.mListLength = obj.GetDataSource().LayerCount()
            else:
                raise NotImplementedError()

    def setValue(self, value):

        def convertOrFail(value):
            if type(value) != self.mType:
                try:
                    value = self.mType(value)
                except Exception as ex:
                    raise Exception('Value(s) need(s) to be of type {0} or convertible to {0}'.format(self.mType))
            return value

        if isinstance(self.mListLength, int) and self.mListLength > 0:
            if isinstance(value, np.ndarray):
                value = list(value)

            assert isinstance(value, list) and len(value) == self.mListLength, \
                'setValue(value): `value` needs to be a list of {} elements'.format(self.mListLength)

            value = [convertOrFail(v) for v in value]

        else:
            value = convertOrFail(value)
        super(MDKeyDomainString, self).setValue(value)

    def setListLength(self, listLength):
        self.mListLength = listLength

    def readValueFromSource(self, obj):
        """
        Reads a value from a gdal/ogr object `obj
        :param obj:
        :return:
        """

        if type(obj) in [gdal.Dataset, gdal.Band, ogr.DataSource, ogr.Layer]:
            valueString = obj.GetMetadataItem(self.mName, self.mDomain)

            self.initListLength(obj, valueString)
            if self.mListLength is not None:
                # convert the string values into a list
                parts = re.split('[,{}]', valueString)
                parts = [p.strip() for p in parts]
                parts = [p for p in parts if p != '']
                parts = [self.mType(p) for p in parts]

                if len(parts) != self.mListLength:
                    s = ""

                # try to convert to target type
                try:
                    parts2 = [self.mType(p) for p in parts]
                except Exception as ex:
                    parts2 = parts

                self.setValue(parts2)
            elif self.mType == QDate:
                self.setValue(QDate.fromString(valueString, 'yyyy-MM-dd'))
            elif self.mType == np.datetime64:
                self.setValue(np.datetime64(valueString))
            else:
                self.setValue(self.mType(valueString))
        else:
            raise NotImplementedError()

    def writeValueToSource(self, obj):
        """
        Formats the value `value` into a fitting string and writes it to the gdal/ogr object `obj`
        :param obj: gdal.MajorObject or ogr.MajorObject
        :param value: value of any type
        :return: None (= success) or Exception (= unable to write)
        """
        assert isinstance(obj, gdal.MajorObject) or isinstance(obj, ogr.MajorObject)

        value = self.value()
        if isinstance(value, list):

            value = [str(v) for v in value]
            value = ', '.join(value)

            if self.mDomain == 'ENVI':
                value = '{' + value + '}'
        else:
            value = str(value)

        # in all cases, write a string
        obj.SetMetadataItem(self.mName, value, domain=self.mDomain)


class MDKeyCoordinateReferenceSystem(MDKeyAbstract):
    def __init__(self, obj, **kwds):
        super(MDKeyCoordinateReferenceSystem, self).__init__(obj, 'CRS', **kwds)
        if not kwds.get('tooltip'):
            self.mTooltip = 'Coordinate Reference System.'

    def readValueFromSource(self, obj):
        crs = None
        if isinstance(obj, gdal.Dataset):
            wkt = obj.GetProjection()
            crs = QgsCoordinateReferenceSystem(wkt)

        elif isinstance(obj, gdal.Band):
            crs = self.readValueFromSource(obj.GetDataset())

        elif isinstance(obj, ogr.Layer):
            wkt = obj.GetSpatialRef().ExportToWkt()
            crs = QgsCoordinateReferenceSystem(wkt)
        elif isinstance(obj, ogr.DataSource):
            crs = self.readValueFromSource(obj.GetLayer(0))
        else:
            raise NotImplementedError()

        self.setValue(crs)

    def writeValueToSource(self, obj, crs):
        error = None

        wkt = ''
        if isinstance(crs, QgsCoordinateReferenceSystem):
            wkt = crs.toWkt()

        if isinstance(obj, gdal.Dataset):
            obj.SetProjection(wkt)
        elif isinstance(obj, ogr.Layer):
            pass
        else:
            raise NotImplementedError()

        return error


class MDKeyDescription(MDKeyAbstract):
    def __init__(self, obj, name='Description', **kwds):
        super(MDKeyDescription, self).__init__(obj, name, **kwds)

    def readValueFromSource(self, obj):
        assert isinstance(obj, gdal.MajorObject) or isinstance(obj, ogr.MajorObject)
        self.setValue(obj.GetDescription())

    def writeValueToSource(self, obj):
        assert isinstance(obj, gdal.MajorObject) or isinstance(obj, ogr.MajorObject)
        value = self.value()
        if value is None:
            v = ''
        else:
            v = str(value)
        obj.SetDescription(v)


class MDKeyClassification(MDKeyAbstract):

    def __init__(self, obj):
        super(MDKeyClassification, self).__init__(obj, 'Classification')

    def setValue(self, value):
        assert value is None or isinstance(value, ClassificationScheme)
        if not self.mValue0Initialized:
            self.mValue0 = ClassificationScheme()
            self.mValue = ClassificationScheme()
            self.mValue0Initialized = True

        self.mValue.clear()
        if isinstance(value, ClassificationScheme):
            self.mValue.insertClasses(value[:])

    def readValueFromSource(self, obj):
        classScheme = None
        if isinstance(obj, gdal.Band):
            classScheme = ClassificationScheme.fromRasterBand(obj)
        elif isinstance(obj, gdal.Dataset):
            classScheme = ClassificationScheme.fromRasterBand(obj.GetRasterBand(1))
        else:
            raise NotImplementedError()

        self.setValue(classScheme)

    def writeValueToSource(self, obj):

        if isinstance(obj, gdal.Dataset):
            self.writeValueToSource(obj.GetRasterBand(1))
        elif isinstance(obj, gdal.Band):
            assert isinstance(self.mValue, ClassificationScheme)
            if len(self.mValue) > 0:
                ct = self.mValue.gdalColorTable()
                classNames = self.mValue.classNames()
                obj.SetCategoryNames(classNames)
                obj.SetColorTable(ct)

            else:  # remove the class information
                obj.SetCategories([])
                obj.SetColorTable(gdal.ColorTable())

        else:
            raise NotImplementedError()


if __name__ == '__main__':

    from enmapbox.exampledata import enmap, landcover
    from enmapbox.testing import initQgisApplication

    # this will initialize the QApplication/QgsApplication which runs in the background
    # see https://qgis.org/api/classQgsApplication.html for details
    qgsApp = initQgisApplication()

    dsR = gdal.Open(enmap)
    dsV = ogr.Open(landcover)

    drv = gdal.GetDriverByName('MEM')
    dsRM = drv.CreateCopy('', dsR)

    drv = ogr.GetDriverByName('Memory')
    dsVM = drv.CopyDataSource(dsV, '')

    for d in [dsV.GetLayer(0), dsR, dsR.GetRasterBand(1), dsV]:
        oli = None
        try:
            oli = MDKeyAbstract.object2oli(d)
        except Exception as ex:
            s = ""
        s = ""

    qgsApp.exec_()
