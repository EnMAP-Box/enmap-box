import fnmatch
import os
import re

from qgis.PyQt.QtGui import QImage
from enmapbox import DIR_REPO, DIR_ICONS


def file_search(rootdir, pattern, recursive=False, ignoreCase=False):
    assert os.path.isdir(rootdir), "Path is not a directory:{}".format(rootdir)
    regType = type(re.compile(r'.*'))

    for root, dirs, files in os.walk(rootdir):
        for file in files:
            if isinstance(pattern, regType):
                if pattern.search(file):
                    path = os.path.join(root, file)
                    yield path

            elif (ignoreCase and fnmatch.fnmatch(file.lower(), pattern.lower())) \
                    or fnmatch.fnmatch(file, pattern):

                path = os.path.join(root, file)
                yield path
        if not recursive:
            break
            pass

    return None


def convert2png(pathSVG: str):
    if os.path.isfile(pathSVG) and pathSVG.endswith('.svg'):
        pathPNG = re.sub(r'\.svg$', '.png', pathSVG)
        image = QImage(pathSVG)
        image.save(pathPNG)


dirTest = os.path.join(DIR_REPO, 'test')
pathSVG = os.path.join(DIR_ICONS, 'enmapbox.svg')
convert2png(pathSVG)
print('Done')
