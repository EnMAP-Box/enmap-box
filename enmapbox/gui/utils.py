# -*- coding: utf-8 -*-

"""
***************************************************************************
    enmapbox/gui/utils.py

    ---------------------
    Date                 : January 2019
    Copyright            : (C) 2018 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import pathlib
import random
import re
from pathlib import Path
from typing import Optional

from enmapbox.qgispluginsupport.qps.utils import loadUi
from qgis.PyQt.QtGui import QColor
from qgis.core import Qgis

loadUi = loadUi

QGIS_DATATYPE_INFO = {
    Qgis.UnknownDataType: ('UnknownDataType', 'Unknown or unspecified type'),
    Qgis.Byte: ('Byte', 'Eight bit unsigned integer (quint8)'),
    Qgis.UInt16: ('UInt16', 'Sixteen bit unsigned integer (quint16)'),
    Qgis.Int16: ('Int16', 'Sixteen bit signed integer (qint16)'),
    Qgis.UInt32: ('UInt32', 'Thirty two bit unsigned integer (quint32)'),
    Qgis.Int32: ('Int32', 'Thirty two bit signed integer (qint32)'),
    Qgis.Float32: ('Float32', 'Thirty two bit floating point (float)'),
    Qgis.Float64: ('Float64', 'Sixty four bit floating point (double)'),
    Qgis.CInt16: ('CInt16', 'Complex Int16.'),
    Qgis.CInt32: ('CInt32', 'Complex Int32.'),
    Qgis.CFloat32: ('CFloat32', 'Complex Float32.'),
    Qgis.CFloat64: ('CFloat64', 'Complex Float64.'),
    Qgis.ARGB32: ('ARGB32', 'Color, alpha, red, green, blue, 4 bytes the same as QImage::Format_ARGB32.'),
    Qgis.ARGB32_Premultiplied: (
        'ARGB32_Premultiplied',
        'Color, alpha, red, green, blue, 4 bytes the same as QImage::Format_ARGB32_Premultiplied.'
    )
}


def dataTypeName(dataType: Qgis.DataType, verbose: bool = False) -> str:
    """
    Returns a description for a Qgis.DataType
    """
    if dataType in QGIS_DATATYPE_INFO.keys():
        if verbose:
            return QGIS_DATATYPE_INFO[dataType][1]
        else:
            return QGIS_DATATYPE_INFO[dataType][0]
    else:
        return 'Unknown'


def enmapboxUiPath(name: str) -> Path:
    """
    Translate a base name `name` into the absolute path of an ui-file
    :param name: str
    :type name: pathlib.Path
    :return:
    :rtype:
    """
    from enmapbox import DIR_UIFILES
    path = pathlib.Path(DIR_UIFILES) / name
    if not path.is_file():
        raise FileNotFoundError(f'Could not find ui-file {path}')
    return path


def guessDataProvider(src: str) -> Optional[str]:
    """
    Get an str and guesses the QgsDataProvider for
    :param str: str
    :return: str, provider key like 'gdal', 'ogr' or None
    """
    # GDAL / GDAL-subdataset
    if (
        re.search(r'\.(bsq|tiff?|jp2|jp2000|j2k|png)', src, re.I)
        or re.search(r'^.+:.+:.+', src, re.I)
    ):
        return 'gdal'

    # probably a spectral library
    elif re.search(r'\.(sli|esl|asd|asd\.txt)$', src, re.I):
        return 'enmapbox_speclib'
    elif re.search(r'\.(shp|gpkg|kml|csv)$', src, re.I):  # probably a vector file
        return 'ogr'
    elif re.search(r'\.(skops)$', src, re.I):
        return 'enmapbox_skops'
    elif re.search(r'\.(txt|csv|json)$', src, re.I):  # probably normal text file
        return 'enmapbox_textfile'

    elif re.search(r'url=https?.*wfs', src, re.I):
        return 'WFS'
    return None


def high_contrast_random_color(c1: QColor) -> QColor:
    """
    Generates a random QColor that guarantees high contrast against c1
    by ensuring opposite brightness (Value) levels.
    """
    # 1. Get the Hue, Saturation, and Value of the base color
    h1, s1, v1, a1 = c1.getHsv()

    # 2. Pick a completely random Hue (0 to 359 degrees)
    random_hue = random.randint(0, 359)  # nosec B311 # no-security relevant random sampling

    # 3. Force a high-contrast Saturation and Value
    # If c1 is dark, make the random color bright (and vice versa)
    if v1 > 127:
        # c1 is light -> Make the new color dark
        random_value = random.randint(30, 80)  # nosec B311 # no-security relevant random sampling
        # Richer colors stand out better on light
        random_saturation = random.randint(180, 255)  # nosec B311 # no-security relevant random sampling
    else:
        # c1 is dark -> Make the new color bright
        random_value = random.randint(200, 255)  # nosec B311 # no-security relevant random sampling
        # Slightly pastel/vibrant stand out on dark
        random_saturation = random.randint(50, 150)  # nosec B311 # no-security relevant random sampling

    # 4. Return the new QColor
    return QColor.fromHsv(random_hue, random_saturation, random_value)
