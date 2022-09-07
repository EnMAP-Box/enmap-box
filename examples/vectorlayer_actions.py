# -*- coding: utf-8 -*-
# noinspection PyPep8Naming
"""
***************************************************************************
    vectorlayer_actions.py
    An example how to define and use QgsActions with QgsVectorLayers
    ---------------------
    Date                 : Okt 2018
    Copyright            : (C) 2018 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This file is part of the EnMAP-Box.                                   *
*                                                                         *
*   The EnMAP-Box is free software; you can redistribute it and/or modify *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
*   The EnMAP-Box is distributed in the hope that it will be useful,      *
*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          *
*   GNU General Public License for more details.                          *
*                                                                         *
*   You should have received a copy of the GNU General Public License     *
*   along with the EnMAP-Box. If not, see <http://www.gnu.org/licenses/>. *
*                                                                         *
***************************************************************************
"""
from qgis.PyQt.QtCore import QVariant, QSize
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QCheckBox

from enmapbox.testing import start_app
from qgis.core import QgsPythonRunner, QgsFeature, QgsField, QgsVectorLayer, QgsAttributeTableConfig, QgsActionManager, \
    QgsAction, QgsProject
from qgis.gui import QgsMapCanvas, QgsDualView

# read https://github.com/qgis/QGIS/blob/master/tests/src/python/test_qgsactionmanager.py


APP = start_app()  # this instantiates a QGIS environment.
assert QgsPythonRunner.isValid()  # this! is important to run QgsAction of type QgsAction.GenericPython


def create_vectordataset() -> QgsVectorLayer:
    vl = QgsVectorLayer("Point?crs=EPSG:4326", 'test_layer', "memory")
    vl.startEditing()
    vl.addAttribute(QgsField(name='fString', type=QVariant.String, typeName='varchar', len=50))
    vl.addAttribute(QgsField(name='fInt', type=QVariant.Int, typeName='int'))
    vl.addAttribute(QgsField(name='fDouble', type=QVariant.Double))
    vl.addFeature(QgsFeature(vl.fields()))
    vl.commitChanges()

    return vl


# create a small GUI
canvas = QgsMapCanvas()
myWidget = QWidget()
myWidget.setWindowTitle('Layer Action Example')
myWidget.setLayout(QVBoxLayout())
dualView = QgsDualView()
dualView.setView(QgsDualView.AttributeTable)

checkBox = QCheckBox()
checkBox.setText('Show Form View')


def onClicked(b: bool):
    if b:
        dualView.setView(QgsDualView.AttributeEditor)
    else:
        dualView.setView(QgsDualView.AttributeTable)


checkBox.clicked.connect(onClicked)
myWidget.layout().addWidget(dualView)
myWidget.layout().addWidget(checkBox)
myWidget.show()
myWidget.resize(QSize(300, 250))

# get a QgsVectorLayer
layer = create_vectordataset()
# fill some testdata
layer.startEditing()
for i in range(5):
    f = QgsFeature(layer.fields())
    f.setAttribute('fInt', i)
    f.setAttribute('fString', 'Name: {}'.format(i + 1))
    layer.addFeature(f)
layer.commitChanges()

# we like to see the "Action
columns = layer.attributeTableConfig().columns()
columns = [columns[-1]] + columns[:-1]
conf = QgsAttributeTableConfig()
conf.setColumns(columns)
conf.setActionWidgetVisible(True)
conf.setActionWidgetStyle(QgsAttributeTableConfig.ButtonList)
layer.setAttributeTableConfig(conf)

actionManager = layer.actions()
assert isinstance(actionManager, QgsActionManager)

iconPath = ':/qt-project.org/styles/commonstyle/images/standardbutton-delete-128.png'
pythonCode = """
print('Remove features from [% @layer_name %]...')
layer = QgsProject.instance().mapLayer('[% @layer_id %]')
assert isinstance(layer, QgsVectorLayer)
if layer.selectedFeatureCount():
    ids = layer.selectedFeatureIds()
else:
    ids = [[% $id %]]
b= layer.isEditable()
layer.startEditing()
layer.deleteFeatures(ids)
if not b:
    layer.commitChanges()
"""

action = QgsAction(QgsAction.GenericPython, 'Remove this feature', pythonCode, iconPath, True,
                   notificationMessage='msgDelete',
                   actionScopes={'Feature'})
actionManager.addAction(action)
QgsProject.instance().addMapLayer(layer)
canvas.setLayers([layer])
dualView.init(layer, canvas)
dualView.setAttributeTableConfig(layer.attributeTableConfig())
layer.startEditing()

APP.exec_()
