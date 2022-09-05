# describes a Test Case for https://github.com/qgis/QGIS/issues/48598
import pathlib
from qgis.core import QgsProcessingContext, QgsProcessingParameterFile, QgsProcessingUtils
from qgis.testing import start_app

app = start_app()


context = QgsProcessingContext()
parameter = QgsProcessingParameterFile('file', fileFilter='Any file (*.*)')
path = QgsProcessingUtils.generateTempFilename('tempfile.txt')
with open(path, 'w') as f:
    f.write('Dummy')
assert pathlib.Path(path).is_file()
assert parameter.checkValueIsAcceptable(path, context)
print(f'asString={parameter.valueAsString(path, context)}')
print(f'asPythonString={parameter.valueAsPythonString(path, context)}')
print(f'asJsonObject={parameter.valueAsJsonObject(path, context)}')
