"""
Just prints some information on the standard QGIS installation.
specificially the PKGDATAPATH={path to library}
To be used from the CLI, e.g. calling python qgisinfo.py
"""
import pathlib
from qgis.core import QgsApplication, Qgis


pkg = pathlib.Path(QgsApplication.pkgDataPath())
print(f'QGIS Version:{Qgis.version()}\nRevision: {Qgis.devVersion()}')
print(f'PKGDATAPATH={pkg}')
