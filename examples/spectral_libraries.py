# -*- coding: utf-8 -*-

"""
***************************************************************************
    examples/spectral_libraries.py

    This example shows how you can write and read spectral libraries
    using QGIS QgsVectorLayers and the EnMAP-Box
    ---------------------
    Date                 : March 2023
    Copyright            : (C) 2023 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
**************************************************************************
"""

import re

from enmapbox import initAll
# How to write a spectral library
from enmapbox.qgispluginsupport.qps.speclib.core import profile_field_list, is_spectral_library
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import prepareProfileValueDict, encodeProfileValueDict, \
    decodeProfileValueDict
from enmapbox.testing import start_app
from qgis.core import QgsVectorLayer, QgsField, QgsFeature, edit

app = start_app()
initAll()

path = 'myspeclib.gpkg'

x = [452, 453, 454]
xUnit = 'nm'

y_values = [
    [0.005, 0.018, 0.051],
    [0.127, 0.267, 0.476],
    [0.719, 0.921, 1.0],
    [0.921, 0.719, 0.476],
    [0.267, 0.127, 0.051],
]


speclib: QgsVectorLayer = SpectralLibraryUtils.createSpectralLibrary()
assert isinstance(speclib, QgsVectorLayer)
assert is_spectral_library(speclib)

pfields = profile_field_list(speclib)
print(f'profile fields: {pfields}')

# add profiles to 1st profile field

profileField: QgsField = pfields[0]

with edit(speclib):
    for y in y_values:
        feature: QgsFeature = QgsFeature(speclib.fields())

        # express a spectral profile as dictionary
        profileDict = prepareProfileValueDict(x=x, xUnit=xUnit, y=y)

        # convert the dictionary into a data type that can be stored according to
        # the QgsField definition (text,json,binary)
        dump = encodeProfileValueDict(profileDict, encoding=profileField)

        feature.setAttribute(profileField.name(), dump)

        # add other attributes here
        # ...

        assert speclib.addFeature(feature)

# write in-memory spectral library to file
files = SpectralLibraryUtils.writeToSource(speclib, path)

# print files:
for file in files:
    print(f'File {file}:')
    if re.search('(csv|json)$', file):
        with open(file, 'r') as f:
            print(f.read())

# read the written speclib
speclib2: QgsVectorLayer = SpectralLibraryUtils.readFromSource(files[0])


# print the profiles
pfield2 = profile_field_list(speclib)[0]
for i, feature in enumerate(speclib2.getFeatures()):
    profileDict = decodeProfileValueDict(feature.attribute(pfield2.name()))
    print(f'Profile {i + 1}: {profileDict}')

del speclib
del speclib2
app.processEvents()
app.exit()
