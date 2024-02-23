"""
Updates the version number in enmapbox/gui/ui/logo/splashscreen.png
Requires that Inkscape (https://inkscape.org) is installed an can be used from shell
Does not update the version number in splashscreen.svg (!), but create a temporary svg only.
"""
import configparser
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Match

from qgis.testing import start_app

app = start_app()
from enmapbox import DIR_REPO

DIR_REPO = Path(DIR_REPO)
PATH_CONFIG_FILE = DIR_REPO / '.plugin.ini'
PATH_SVG = DIR_REPO / 'enmapbox/gui/ui/logo/splashscreen.svg'


def update_splashscreen():
    assert PATH_CONFIG_FILE.is_file()
    config = configparser.ConfigParser()
    config.read(PATH_CONFIG_FILE)
    VERSION = config['metadata']['version']

    rxVersion = re.compile(r'(?P<major>\d+)\.(?P<minor>\d+)(?P<rest>.*)')

    match = rxVersion.match(VERSION)
    assert isinstance(match, Match)

    txt_major = match.group('major') + '.'
    txt_minor = match.group('minor')

    tree = ET.parse(PATH_SVG)
    root = tree.getroot()
    namespaces = dict([node for _, node in ET.iterparse(PATH_SVG, events=['start-ns'])])
    for prefix, namespace in namespaces.items():
        ET.register_namespace(prefix, namespace)
    node_major_id = 'tspan_major_version'
    node_minor_id = 'tspan_minor_version'
    node_major = root.find(f".//*[@id='{node_major_id}']")
    node_minor = root.find(f".//*[@id='{node_minor_id}']")
    assert isinstance(node_major, ET.Element), f'SVG misses text element with id "{node_major}"'
    assert isinstance(node_minor, ET.Element), f'SVG misses text element with id "{node_minor}"'
    node_major.text = txt_major
    node_minor.text = txt_minor

    PATH_EXPORT = PATH_SVG.parent / 'splashscreen_tmp.svg'
    # PATH_EXPORT = PATH_SVG
    PATH_PNG = PATH_SVG.parent / PATH_EXPORT.name.replace('.svg', '.png')
    tree.write(PATH_EXPORT, encoding='utf8')

    # see https://inkscape.org/doc/inkscape-man.html
    cmd = ['inkscape',
           '--export-type=png',
           '--export-area-page',
           f'--export-filename={PATH_PNG}',
           f'{PATH_EXPORT}']

    print('Run:\n' + ' '.join(cmd))
    print('to export the svg as png with Inkscape (https://inkscape.org)')
    subprocess.run(cmd)

    os.remove(PATH_EXPORT)


if __name__ == "__main__":
    update_splashscreen()
