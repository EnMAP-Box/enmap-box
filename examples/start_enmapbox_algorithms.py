"""
This example shows how to initialize and run QGIS + EnMAP-Box processing algorithms
"""

import os
import pathlib
from math import nan

import processing
from enmapbox import DIR_REPO
from enmapbox.exampledata import enmap
from enmapbox.testing import start_app
from qgis.core import QgsApplication

start_app()

# print available processing algorithms:
reg = QgsApplication.processingRegistry()
for i, a in enumerate(reg.algorithms()):
    print(f'{i + 1}: {a.id()} "{a.displayName()}"')


# Example: "enmapbox:TranslateRasterLayer"
def onFinish(algorithm, context, feedback):
    print('\n'.join(feedback.htmlLog().split('<br/>')))
    print(f'Finished {algorithm.id()}')


DIR_TMP = pathlib.Path(DIR_REPO) / 'tmp'
os.makedirs(DIR_TMP, exist_ok=True)

path_translated = DIR_TMP / 'translatedRaster.bsq'

params = {
    'raster': enmap,
    'bandList': [1, 2, 3],
    'grid': enmap,
    'copyMetadata': True,
    'copyStyle': False,
    'excludeBadBands': False,
    'writeEnviHeader': True,
    'spectralSubset': None,
    'spectralBandList': None,
    'offset': None,
    'scale': None,
    'extent': '153943.482900000,225608.888500000,5277017.619200000,5317102.410300000 [EPSG:32633]',
    'sourceColumns': [nan, nan],
    'sourceRows': [nan, nan],
    'resampleAlg': 0,
    'sourceNoData': None,
    'noData': None,
    'unsetSourceNoData': False,
    'unsetNoData': False,
    'workingType': None,
    'dataType': None,
    'creationProfile': 'ENVI INTERLEAVE=BSQ',
    'outputTranslatedRaster': path_translated.as_posix()
}

results = processing.run("enmapbox:TranslateRasterLayer", params, onFinish=onFinish)

print('Results:')
print(results)
print('Done')
