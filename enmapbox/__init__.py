# -*- coding: utf-8 -*-
# noinspection PyPep8Naming
"""
***************************************************************************
    enmapbox/__init__.py
    EnMAP-Box package definition
    -----------------------------------------------------------------------
    begin                : Jan 2016
    copyright            : (C) 2016 by Benjamin Jakimow
    email                : benjamin.jakimow@geo.hu-berlin.de

***************************************************************************
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this software. If not, see <https://www.gnu.org/licenses/>.
***************************************************************************
"""

import os
import pathlib
import site
import sys
import traceback
import typing
import warnings

from osgeo import gdal

from qgis.PyQt.QtCore import QSettings, PYQT_VERSION_STR
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis, QgsApplication, QgsProcessingAlgorithm, QgsProcessingProvider, QgsProcessingRegistry
from qgis.gui import QgisInterface, QgsMapLayerConfigWidgetFactory

# provide shortcuts

# true version is added from .plugin.ini during plugin build process
__version__ = 'dev'
# commit this version refers to. will be replaced during plugin build process
__version_sha__ = ''
# note that the exampledata folder is part of the repo,
# but will be removed from the plugin ZIP

HOMEPAGE = 'https://github.com/EnMAP-Box/enmap-box'
REPOSITORY = 'https://github.com/EnMAP-Box/enmap-box.git'
ISSUE_TRACKER = 'https://github.com/EnMAP-Box/enmap-box/issues'
CREATE_ISSUE = 'https://github.com/EnMAP-Box/enmap-box/issues/new'
REQUIREMENTS_CSV = pathlib.Path(__file__).parents[1] / '.env' / 'requirements.csv'
DOCUMENTATION = 'https://enmap-box.readthedocs.io/'
URL_TESTDATA = 'https://github.com/EnMAP-Box/enmap-box-exampledata/releases/download/v1.1/exampledata.zip'
URL_INSTALLATION = r'https://enmap-box.readthedocs.io/en/latest/usr_section/usr_installation.html#install-required-python-packages'
URL_QGIS_RESOURCES = r'https://box.hu-berlin.de/f/6949ab1099044018a5e4/?dl=1'
PLUGIN_DEPENDENCIES = ['vrtbuilderplugin>=0.9']

DIR_ENMAPBOX = os.path.dirname(__file__)
DIR_REPO = os.path.dirname(DIR_ENMAPBOX)
DIR_UIFILES = os.path.join(DIR_ENMAPBOX, *['gui', 'ui'])
DIR_ICONS = os.path.join(DIR_ENMAPBOX, *['gui', 'ui', 'icons'])
DIR_EXAMPLEDATA = (pathlib.Path(DIR_REPO) / 'enmapbox' / 'exampledata').as_posix()
DIR_REPO_TMP = (pathlib.Path(DIR_REPO) / 'tmp').as_posix()
DIR_UNITTESTS = (pathlib.Path(DIR_REPO) / 'tests').as_posix()

ENMAP_BOX_KEY = 'EnMAP-Box'

_ENMAPBOX_MAPLAYER_CONFIG_WIDGET_FACTORIES: typing.List[QgsMapLayerConfigWidgetFactory] = []

gdal.SetConfigOption('GDAL_VRT_ENABLE_PYTHON', 'YES')

# ensure that PyQtGraph uses the same PyQt as QGIS
os.environ.setdefault('PYQTGRAPH_QT_LIB', f'PyQt{PYQT_VERSION_STR[0]}')

# test if PyQtGraph is available
try:
    import pyqtgraph  # noqa
except ModuleNotFoundError:
    # use PyQtGraph brought by QPS
    pSrc = pathlib.Path(DIR_ENMAPBOX) / 'qgispluginsupport' / 'qps' / 'pyqtgraph'
    assert pSrc.is_dir()
    site.addsitedir(pSrc)
    # import pyqtgraph


def enmapboxSettings() -> QSettings:
    """
    Returns the QSettings object for EnMAP-Box Settings
    :return: QSettings
    """
    return QSettings('HU-Berlin', ENMAP_BOX_KEY)


settings = enmapboxSettings()
DEBUG = str(os.environ.get('DEBUG', False)).lower() in ['1', 'true']
RAISE_ALL_EXCEPTIONS = str(os.environ.get('RAISE_ALL_EXCEPTIONS', False)).lower() in ['1', 'true']


def icon() -> QIcon:
    """
    Returns the EnMAP icon.
    (Requires that the EnMAP resources have been loaded before)
    :return: QIcon
    """
    return QIcon(':/enmapbox/gui/ui/icons/enmapbox.svg')


def debugLog(msg: str):
    if str(os.environ.get('DEBUG', False)).lower() in ['1', 'true']:
        print('DEBUG:' + msg, flush=True)


def messageLog(msg, level=Qgis.Info, notifyUser: bool = True):
    """
    Writes a log message to the QGIS EnMAP-Box Log
    :param msg: log message string
    :param level: Qgis.MessageLevel=[Qgis.Info|Qgis.Warning|Qgis.Critical|Qgis.Success|Qgis.NONE]
    """
    if not isinstance(msg, str):
        msg = str(msg)
    app = QgsApplication.instance()
    if isinstance(app, QgsApplication):
        app.messageLog().logMessage(msg, 'EnMAP-Box',
                                    level=level,
                                    notifyUser=notifyUser)
        from qgis.utils import iface
        if isinstance(iface, QgisInterface) and level == Qgis.Critical:
            iface.openMessageLog()
            title = msg.split('\n')[0]
            iface.messageBar().pushMessage(title, msg, msg, level=level)
    else:
        if level == Qgis.Critical:
            print(msg, file=sys.stderr)
        elif level == Qgis.Warning:
            warnings.warn(msg, stacklevel=2)
        else:
            print(msg)


def scantree(path, ending: str = '') -> pathlib.Path:
    """Recursively returns file paths in directory"""
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path, ending=ending)
        else:
            if entry.path.endswith(ending):
                yield pathlib.Path(entry.path)


def initPythonPaths():
    """
    Adds EnMAP-Box internal paths to PYTHONPATH
    Can be used e.g. in unit-tests to ensure that sub-packages are imported right
    """
    ROOT = pathlib.Path(__file__).parent
    site.addsitedir(ROOT / 'site-packages')
    site.addsitedir(ROOT / 'apps')
    site.addsitedir(ROOT / 'coreapps')
    site.addsitedir(ROOT / 'eo4qapps')


def initEnMAPBoxResources():
    """
    Loads (or reloads) all Qt resource files
    """
    debugLog('started initEnMAPBoxResources')
    from .qgispluginsupport.qps.resources import initQtResources
    initQtResources(DIR_ENMAPBOX)
    debugLog('finished initEnMAPBoxResources')


def registerEditorWidgets():
    """
    Initialises QgsEditorWidgets
    """
    debugLog('started initEditorWidgets')

    from enmapbox.qgispluginsupport.qps import registerEditorWidgets
    registerEditorWidgets()

    debugLog('finished initEditorWidgets')


def unregisterEditorWidgets():
    """
    just for convenience. So far editor widgets can not be unregistered
    :return:
    :rtype:
    """
    pass


def collectEnMAPBoxAlgorithms() -> typing.List[QgsProcessingAlgorithm]:
    """
    Safely collects all QgsProcessingAlgorithms from enmapboxprocessing.algorithm.algorithms.
    Missing dependencies or import errors will not stop the EnMAP-Box from being loaded.
    """
    algs = []
    try:
        from enmapboxprocessing.algorithm.algorithms import algorithms
        for alg in algorithms():
            try:
                algs.append(alg.create())
            except Exception as ex2:
                traceback.print_stack()
                messageLog(str(ex2), Qgis.Warning)
    except Exception as ex:
        traceback.print_exc()
        info = 'Unable to load enmapboxprocessing.algorithm.algorithms'
        info += '\n' + str(ex)
        messageLog(info, Qgis.Critical)

    try:
        from enmapbox.qgispluginsupport.qps.speclib.processing.aggregateprofiles import AggregateProfiles
        from enmapbox.qgispluginsupport.qps.speclib.processing.importspectralprofiles import ImportSpectralProfiles
        algs.extend([AggregateProfiles(), ImportSpectralProfiles()])
    except Exception as ex:
        traceback.print_exc()
        info = f'Unable to load processing algorithms: {ex}'
        info += '\n' + str(ex)
        messageLog(info, Qgis.Critical)

    return algs


def registerEnMAPBoxProcessingProvider():
    """
    Initializes the EnMAPBoxProcessingProvider
    """
    debugLog('started initEnMAPBoxProcessingProvider')
    from enmapbox.algorithmprovider import EnMAPBoxProcessingProvider, ID

    registry = QgsApplication.instance().processingRegistry()
    assert isinstance(registry, QgsProcessingRegistry)
    provider = registry.providerById(ID)
    if not isinstance(provider, QgsProcessingProvider):
        provider = EnMAPBoxProcessingProvider.instance()
        registry.addProvider(provider)

    assert isinstance(provider, EnMAPBoxProcessingProvider)
    assert id(registry.providerById(ID)) == id(provider)

    try:
        existingAlgNames = [a.name() for a in registry.algorithms() if a.groupId() == provider.id()]
        missingAlgs = [a for a in collectEnMAPBoxAlgorithms() if a.name() not in existingAlgNames]
        provider.addAlgorithms(missingAlgs)
    except Exception as ex:
        traceback.print_exc()
        info = ['EnMAP-Box: Failed to load enmapboxprocessing.algorithm.algorithms.\n{}'.format(str(ex)),
                'PYTHONPATH:']
        for p in sorted(sys.path):
            info.append(p)
        messageLog(info, Qgis.Warning)
        print('\n'.join(info), file=sys.stderr)

    debugLog('started initEnMAPBoxProcessingProvider')


def unregisterEnMAPBoxProcessingProvider():
    """Removes the EnMAPBoxProcessingProvider"""
    from enmapbox.algorithmprovider import EnMAPBoxProcessingProvider, ID
    registry = QgsApplication.instance().processingRegistry()
    provider = registry.providerById(ID)

    if isinstance(provider, EnMAPBoxProcessingProvider):
        EnMAPBoxProcessingProvider._ENMAPBOX_PROCESSING_PROVIDER = None
        # this deletes the C++ object
        registry.removeProvider(ID)


def registerMapLayerConfigWidgetFactories():
    """
    Registers widgets to be shown into the QGIS layer properties dialog
    """
    debugLog('started initMapLayerConfigWidgetFactories')
    # global _ENMAPBOX_MAPLAYER_CONFIG_WIDGET_FACTORIES
    from enmapbox.qgispluginsupport.qps import registerMapLayerConfigWidgetFactory

    from enmapbox.qgispluginsupport.qps.layerconfigwidgets.rasterbands import RasterBandConfigWidgetFactory
    from enmapbox.qgispluginsupport.qps.layerconfigwidgets.gdalmetadata import GDALMetadataConfigWidgetFactory

    for factory in [RasterBandConfigWidgetFactory(),
                    GDALMetadataConfigWidgetFactory(),
                    ]:

        registered = registerMapLayerConfigWidgetFactory(factory)
        if isinstance(registered, QgsMapLayerConfigWidgetFactory):
            _ENMAPBOX_MAPLAYER_CONFIG_WIDGET_FACTORIES.append(registered)

    debugLog('finished initMapLayerConfigWidgetFactories')


def unregisterMapLayerConfigWidgetFactories():
    """
    Removes MapLayerConfigWidgetFactories which had been registered with the EnMAP-Box
    """
    from .qgispluginsupport.qps import unregisterMapLayerConfigWidgetFactory
    for factory in _ENMAPBOX_MAPLAYER_CONFIG_WIDGET_FACTORIES:
        unregisterMapLayerConfigWidgetFactory(factory)


def registerExpressionFunctions():
    """
    Adds Expression functions for the QGIS expression editor
    """
    from .qgispluginsupport.qps.qgsfunctions import registerQgsExpressionFunctions
    registerQgsExpressionFunctions()


def unregisterExpressionFunctions():
    """
    Removes added expression functions
    """
    from .qgispluginsupport.qps.qgsfunctions import unregisterQgsExpressionFunctions
    unregisterQgsExpressionFunctions()


def initAll():
    """
    Calls other init routines required to run the EnMAP-Box properly
    """
    initEnMAPBoxResources()
    from enmapbox.qgispluginsupport.qps import \
        registerSpectralLibraryIOs, \
        registerSpectralLibraryPlotFactories
    registerSpectralLibraryIOs()
    registerSpectralLibraryPlotFactories()

    registerEditorWidgets()
    registerExpressionFunctions()
    registerEnMAPBoxProcessingProvider()
    registerMapLayerConfigWidgetFactories()


def unloadAll():
    """
    Reomves all registered factories etc.
    """
    unregisterEditorWidgets()
    unregisterExpressionFunctions()
    unregisterMapLayerConfigWidgetFactories()
    unregisterEnMAPBoxProcessingProvider()


def tr(text: str) -> str:
    """
    to be implemented: string translation
    :param text:
    :return: str
    """
    return text


def run():
    """
    Call to start the EnMAP-Box
    :return:
    """
    import enmapbox.__main__
    enmapbox.__main__.run()
