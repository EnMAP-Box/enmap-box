"""
Updates the version number in enmapbox/gui/ui/logo/splashscreen.png
Requires that Inkscape (https://inkscape.org) is installed an can be used from shell
Does not update the version number in splashscreen.svg (!), but create a temporary svg only.
"""
import argparse
import configparser
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Match, Union

from enmapbox import DIR_REPO
from enmapbox.gui.splashscreen.splashscreen import PATH_SPLASHSCREEN

DIR_REPO = Path(DIR_REPO)
PATH_CONFIG_FILE = DIR_REPO / '.plugin.ini'
PATH_SVG = DIR_REPO / 'enmapbox/gui/splashscreen/splashscreen.svg'
ENV_INKSCAPE_BIN = 'INKSCAPE_BIN'


def inkscapeBin() -> Path:
    """
    Searches for the Inkscape binary
    """
    if ENV_INKSCAPE_BIN in os.environ:
        path = os.environ[ENV_INKSCAPE_BIN]
    else:
        path = shutil.which('inkscape')
    if path:
        path = Path(path)

    assert path.is_file(), f'Could not find inkscape executable. Set {ENV_INKSCAPE_BIN}=<path to inkscape binary>'
    return path


def update_splashscreen(version: str = None,
                        pure: bool = False,
                        path_png: Union[str, Path] = None):
    assert PATH_SVG.is_file()
    PATH_INKSCAPE = inkscapeBin()

    if path_png:
        path_png = Path(path_png)
    else:
        path_png = PATH_SVG.parent / PATH_SVG.name.replace('.svg', '.png')

    if version is None:
        assert PATH_CONFIG_FILE.is_file()
        config = configparser.ConfigParser()
        config.read(PATH_CONFIG_FILE)
        version = config['metadata']['version']

    rxVersion = re.compile(r'(?P<major>\d+)\.(?P<minor>\d+)(?P<rest>.*)')

    match = rxVersion.match(version)
    assert isinstance(match, Match)

    txt_major = match.group('major')
    txt_minor = '.' + match.group('minor')

    with open(PATH_SVG, encoding='utf-8') as f:
        tree = ET.parse(f)
    root = tree.getroot()
    # namespaces = dict([node for _, node in ET.iterparse(PATH_SVG, events=['start-ns'])])
    namespaces = {'inkscape': "http://www.inkscape.org/namespaces/inkscape",
                  'sodipodi': "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
                  'svg': 'http://www.w3.org/2000/svg'}

    for prefix, namespace in namespaces.items():
        ET.register_namespace(prefix, namespace)

    # set version number
    node_major = root.find(".//*[@inkscape:label='maj_version']/*", namespaces)
    node_minor = root.find(".//*[@inkscape:label='min_version']/*", namespaces)
    assert isinstance(node_major, ET.Element), 'SVG misses tspan element below inkscape:label = "maj_version"'
    assert isinstance(node_minor, ET.Element), 'SVG misses tspan element below inkscape:label = "min_version"'

    node_major.text = txt_major
    node_minor.text = txt_minor

    if pure:
        # disable lower bar
        node_bar = root.find(".//*[@inkscape:label='LowerBar']", namespaces)
        node_bar.attrib['style'] = 'display:none'

    PATH_EXPORT_TMP = PATH_SVG.parent / 'splashscreen_tmp.svg'

    # PATH_EXPORT = PATH_SVG
    tree.write(PATH_EXPORT_TMP, encoding='utf8')

    # see https://inkscape.org/doc/inkscape-man.html
    cmd = [
        #  'inkscape',
        f'{PATH_INKSCAPE}',
        '--export-type=png',
        '--export-area-page',
        f'--export-filename={path_png}',
        f'{PATH_EXPORT_TMP}'
    ]

    print('Run:\n' + ' '.join(cmd))
    print('to export the svg as png with Inkscape (https://inkscape.org)')
    subprocess.run(cmd, check=True)
    os.remove(PATH_EXPORT_TMP)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update the EnMAP-Box splashscreen.',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-v', '--version',
                        required=False,
                        default=None,
                        help='A version string with major and minor version, like "3.12"')

    parser.add_argument('-p', '--pure',
                        required=False,
                        default=False,
                        action='store_true',
                        help='Pure splashscreen, without the lower bar to show the loading status.')

    parser.add_argument('--png',
                        required=False,
                        default=PATH_SPLASHSCREEN,
                        help=f'Path of PNG file to create. Defaults to {PATH_SPLASHSCREEN}')

    args = parser.parse_args()
    update_splashscreen(version=args.version, pure=args.pure)
