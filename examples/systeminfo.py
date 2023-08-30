import sys
import platform
from qgis.core import Qgis
print(platform.platform())
print(platform.processor())
print(platform.python_implementation())
print(platform.python_version())
print(f'Sys exe: {sys.executable}')

print(f'QGIS: {Qgis.version()} {Qgis.devVersion()}')

print('Package locations:')
packages = ['osgeo.gdal', 'numpy', 'scipy',
            'sklearn', 'OpenGL', 'ee',
            'matplotlib', 'pip', 'astropy', 'xgboost', 'lightgbm', 'catboost',
            'sympy', 'numba', 'netCDF4', 'enpt-enmapboxapp', ]
for p in packages:
    try:
        pkg = __import__(p)
        print(pkg.__file__)
    except Exception as ex:
        print(ex)

