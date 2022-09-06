"""
This script checks *.py files for QGS103 and QGS101 errors

See https://github.com/GispoCoding/flake8-qgis for bad and good examples

"""
import argparse
import os
import pathlib
import re

from enmapbox.qgispluginsupport.qps.utils import file_search

RX_QGS101 = re.compile(r'from qgis\._(core|gui) import')
RX_QGS102 = re.compile(r'import qgis\._(core|gui)')
RX_QGS103 = re.compile(r'from PyQt5\.(Qt[^. ]+) import')
RX_QGS104 = re.compile(r'import PyQt5\.(Qt[^. ]+)')


def repairString(text) -> str:
    text = RX_QGS101.sub(r'from qgis.\1 import', text)
    text = RX_QGS102.sub(r'import qgis.\1', text)
    text = RX_QGS103.sub(r'from qgis.PyQt.\1 import', text)
    text = RX_QGS104.sub(r'import qgis.PyQt.\1', text)
    return text


def test_repairString():
    EXAMPLES = [
        ('from qgis._core import QgsMapLayer, QgsVectorLayer', 'from qgis.core import QgsMapLayer, QgsVectorLayer'),
        ('from qgis._core import QgsApplication', 'from qgis.core import QgsApplication'),
        ('import qgis._core.QgsVectorLayer as QgsVectorLayer', 'import qgis.core.QgsVectorLayer as QgsVectorLayer'),
        ('from PyQt5.QtCore import pyqtSignal', 'from qgis.PyQt.QtCore import pyqtSignal'),
        ('import PyQt5.QtCore.pyqtSignal as pyqtSignal', 'import qgis.PyQt.QtCore.pyqtSignal as pyqtSignal'),
    ]

    for (bad, good) in EXAMPLES:
        assert good == repairString(bad), f'Failed to repair {bad}'

    # check multi-line examples
    BAD = '\n'.join([v[0] for v in EXAMPLES])
    GOOD = '\n'.join([v[1] for v in EXAMPLES])

    assert GOOD == repairString(BAD)


def repairFile(path, check_only=True):
    path = pathlib.Path(path)
    with open(path, 'r') as f:
        textBad = f.read()
    textGood = repairString(textBad)
    if textGood != textBad:
        print(f'Found errors in {path}')
        if not check_only:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(textGood)


def repairRepositoryFiles(dry_run: bool = True):
    DIR_REPO = pathlib.Path(__file__).parents[1]
    for path in file_search(DIR_REPO, re.compile('.*\.py$')):
        repairFile(path, check_only=dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Repair Flake8 QGIS issues', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-t',
                        required=False,
                        default=False,
                        help='Runs internal test routine',
                        action='store_true')
    parser.add_argument('-d', '--dry-run',
                        required=False,
                        default=True,
                        help='Dry mode. prints affected files without repairing them',
                        action='store_true')
    parser.add_argument('-r', '--repair',
                        required=False,
                        default=False,
                        help='Repairs affected files in this repository',
                        action='store_true')
    args = parser.parse_args()

    if args.t is True:
        test_repairString()
    else:
        if args.r is True:
            args.d = False
        repairRepositoryFiles(dry_run=args.d)
