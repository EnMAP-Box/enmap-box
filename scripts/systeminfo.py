import csv
import platform
import sys
from pathlib import Path

from qgis.core import Qgis

print(platform.platform())
print(platform.processor())
print(platform.python_implementation())
print(platform.python_version())
print(f'Sys exe: {sys.executable}')

print(f'QGIS: {Qgis.version()} {Qgis.devVersion()}')

print('Package locations:')

packageinfo = Path(__file__).parents[1] / '.env' / 'requirements.csv'
if packageinfo.is_file():
    packages = []
    with open(packageinfo, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pkg = row['py_name'] if row['py_name'] else row['pip_name']
            pkg = pkg.strip()
            if pkg != '':
                packages.append(pkg)
            else:
                s = ""
else:
    packages = ['osgeo.gdal', 'numpy', 'scipy',
                'sklearn', 'OpenGL', 'ee',
                'matplotlib', 'pip', 'astropy', 'xgboost', 'lightgbm', 'catboost',
                'sympy', 'numba', 'netCDF4', 'enpt_enmapboxapp', ]
for p in packages:
    try:
        pkg = __import__(p)
        version = 'unknown'
        if hasattr(pkg, '__version__'):
            version = pkg.__version__
        info = f'{p} version {version}: {pkg.__file__}'
        print(info)

    except Exception as ex:
        print(ex)
