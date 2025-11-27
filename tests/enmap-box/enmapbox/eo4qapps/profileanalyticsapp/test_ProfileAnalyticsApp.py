from qgis.core import QgsFeature

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import prepareProfileValueDict
from enmapbox.testing import TestObjects
from enmapbox.testing import start_app

start_app()
initAll()


def myFunc(fid):
    print('HELLO', fid)


qgsApp = start_app()
enmapBox = EnMAPBox()
library = TestObjects.createSpectralLibrary(n=0, profile_field_names=['profiles'], wlu='nanometers')
library.featureAdded.connect(myFunc)
library.setName('My Profiles')

# TODO
# - add a new Spectral View
# - add a visualization to the Spectral View and select the "library:profiles" field

# add a feature
profileValueDict = prepareProfileValueDict([100, 200, 300], [1, 2, 1], 'nanometers')
feature = QgsFeature()
id = 1
feature.setId(id)
feature.setFields(library.fields())
feature.setAttribute('name', 'myProfile')
feature.setAttribute('profiles', profileValueDict)
library.dataProvider().truncate()  # delete all features
library.startEditing()
library.addFeature(feature)
library.commitChanges()

enmapBox.addSources([library])
qgsApp.exec_()
