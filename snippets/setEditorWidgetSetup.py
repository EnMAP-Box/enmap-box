from qgis.core import QgsVectorLayer, QgsEditorWidgetSetup, QgsMapLayer

# create a simple library with a field "html"
filename = __file__.replace('.py', '.geojson')
with open(filename, 'w') as file:
    file.write(
        """
            {
                "type": "FeatureCollection",
                "name": "dummy",
                "description": "",
                "features": [{"type": "Feature", "properties": {"html": "dummy.html"}}]
            }
        """
    )

# setup widget type for "html"
library = QgsVectorLayer(filename)
assert library.isValid()
fields = library.fields()
htmlField = fields.field(fields.indexFromName('html'))
htmlSetup = QgsEditorWidgetSetup(
    'ExternalResource',
    {
        'DocumentViewer': 2, 'DocumentViewerHeight': 0, 'DocumentViewerWidth': 0, 'FileWidget': True,
        'FileWidgetButton': False, 'FileWidgetFilter': '',
        'PropertyCollection': {'name': None, 'properties': {}, 'type': 'collection'}, 'RelativeStorage': 0,
        'StorageAuthConfigId': None, 'StorageMode': 0, 'StorageType': None
    }
)
htmlField.setEditorWidgetSetup(htmlSetup)
library.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)
print('done!')
