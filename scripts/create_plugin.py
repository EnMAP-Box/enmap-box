# -*- coding: utf-8 -*-

"""
***************************************************************************
    create_plugin.py
    Script to build the EnMAP-Box QGIS Plugin from Repository code
    ---------------------
    Date                 : August 2017
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as pclearublished by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.
                 *
*                                                                         *
***************************************************************************
"""
import argparse
import configparser
import fnmatch
import io
import os
import re
import shutil
import sys
import textwrap
import typing
import warnings
from os.path import exists
from pathlib import Path
from typing import Union

import docutils.core
import markdown

import enmapbox
from enmapbox import DIR_REPO
from enmapbox.qgispluginsupport.qps.make.deploy import QGISMetadataFileWriter, userProfileManager
from enmapbox.qgispluginsupport.qps.utils import zipdir
from qgis.core import QgsFileUtils, QgsUserProfile, QgsUserProfileManager
from qgis.testing import start_app

app = start_app()
# consider default Git location on Windows systems to avoid creating a Start-Up Script
try:
    import git
except (ImportError, ModuleNotFoundError) as ex:
    # try to import after expanding PATH with known locations
    potentialLocations = [r'C:\Program Files\Git\bin']
    found = False
    oldPath = os.environ['PATH']
    for p in potentialLocations:
        if exists(p):
            os.environ['PATH'] = oldPath + os.pathsep + p
            sys.path.append(p)
            try:
                import git

                found = True
                break
            except ModuleNotFoundError:
                sys.path.remove(p)
    if found:
        warnings.warn(f'Git executable was not available in PATH! Found it in {p}')
    else:
        os.environ['PATH'] = oldPath  # avoid side-effects!
        raise ex

DIR_REPO = Path(DIR_REPO)

PATH_CONFIG_FILE = DIR_REPO / 'tox.ini'
assert PATH_CONFIG_FILE.is_file()


def scanfiles(root: typing.Union[str, Path]) -> typing.Iterator[Path]:
    """
    Recursively returns file paths in directory
    :param root: root directory to search in
    :return: Path
    """

    for entry in os.scandir(root):
        entry: os.DirEntry
        if entry.is_dir(follow_symlinks=False):
            yield from scanfiles(entry.path)
        else:
            path = Path(entry.path)
            if path.is_file():
                yield path


def fileRegex(root: typing.Optional[str], pattern: str) -> typing.Pattern:
    """
    Create a regex to match a file pattern
    :param root:
    :param pattern:
    :return:
    """

    is_regex = False
    if pattern.startswith('rx:'):
        is_regex = True
        pattern = pattern[3:]

    if root:
        pattern = f'{root}/{pattern}'

    if is_regex:
        return re.compile(pattern)
    else:
        return re.compile(fnmatch.translate(pattern))


def create_enmapbox_plugin(include_testdata: bool = False,
                           include_qgisresources: bool = False,
                           create_zip: bool = True,
                           copy_to_profile: bool = False,
                           build_name: str = None) -> typing.Optional[Path]:
    assert (DIR_REPO / '.git').is_dir()
    config = configparser.ConfigParser()
    config.read(PATH_CONFIG_FILE)

    MAX_PLUGIN_SIZE = int(config['enmapbox:plugin']['max_size_mb'])
    DIR_DEPLOY_LOCAL = DIR_REPO / 'deploy'
    DIR_QGIS_USERPROFILE: Path = None

    if copy_to_profile:
        profileManager: QgsUserProfileManager = userProfileManager()
        assert len(profileManager.allProfiles()) > 0
        if isinstance(copy_to_profile, str):
            profileName = copy_to_profile
        else:
            profileName = profileManager.defaultProfileName()
        assert profileManager.profileExists(profileName), \
            f'QGIS profiles "{profileName}" does not exist in {profileManager.allProfiles()}'

        profileManager.setActiveUserProfile(profileName)
        profile: QgsUserProfile = profileManager.userProfile()

        DIR_QGIS_USERPROFILE = Path(profile.folder())
        if DIR_QGIS_USERPROFILE:
            os.makedirs(DIR_QGIS_USERPROFILE, exist_ok=True)
            if not DIR_QGIS_USERPROFILE.is_dir():
                raise f'QGIS profile directory "{profile.name()}" does not exists: {DIR_QGIS_USERPROFILE}'

    REPO = git.Repo(DIR_REPO)
    active_branch = REPO.active_branch.name
    VERSION = config['enmapbox:metadata']['version']
    VERSION_SHA = REPO.active_branch.commit.hexsha
    lastCommitDate = REPO.active_branch.commit.authored_datetime
    timestamp = re.split(r'[.+]', lastCommitDate.isoformat())[0]

    if build_name is None:
        # we are on release branch
        if re.search(r'release_\d+\.\d+', active_branch):
            BUILD_NAME = VERSION
        else:
            BUILD_NAME = '{}.{}.{}'.format(VERSION, timestamp, active_branch)
            BUILD_NAME = re.sub(r'[:-]', '', BUILD_NAME)
            BUILD_NAME = re.sub(r'[\\/]', '_', BUILD_NAME)
    else:
        BUILD_NAME = build_name

    if REPO.is_dirty():
        if BUILD_NAME == VERSION and build_name is None:
            raise Exception('Repository has uncommitted changes!\n'
                            'Commit / rollback them first to ensure a valid VERSION_SHA for release builds!')
        else:
            warnings.warn('Repository has uncommitted changes!')

    PLUGIN_DIR = DIR_DEPLOY_LOCAL / 'enmapboxplugin'
    PLUGIN_ZIP = DIR_DEPLOY_LOCAL / 'enmapboxplugin.{}.zip'.format(BUILD_NAME)

    if PLUGIN_DIR.is_dir():
        shutil.rmtree(PLUGIN_DIR)
    os.makedirs(PLUGIN_DIR, exist_ok=True)

    PATH_METADATAFILE = PLUGIN_DIR / 'metadata.txt'

    pathAbout = DIR_REPO / 'ABOUT.md'

    # set QGIS Metadata file values
    MD = QGISMetadataFileWriter()
    MD.mName = config['enmapbox:metadata']['name']
    MD.mDescription = config['enmapbox:metadata']['description']
    MD.mTags = config['enmapbox:metadata']['tags'].strip().split('\n')
    MD.mCategory = config['enmapbox:metadata']['category']
    MD.mAuthor = config['enmapbox:metadata']['authors'].strip().split('\n')
    MD.mIcon = config['enmapbox:metadata']['icon']
    MD.mHomepage = config['enmapbox:metadata']['homepage']
    MD.mAbout = config.get('enmapbox:metadata', 'about').splitlines()
    MD.mTracker = enmapbox.ISSUE_TRACKER
    MD.mRepository = enmapbox.REPOSITORY
    MD.mQgisMinimumVersion = config['enmapbox:metadata']['qgisMinimumVersion']
    MD.mEmail = config['enmapbox:metadata']['email']
    MD.mHasProcessingProvider = True

    MD.mVersion = VERSION
    MD.writeMetadataTxt(PATH_METADATAFILE)

    # (re)-compile all enmapbox resource files
    from scripts.compile_resourcefiles import compileEnMAPBoxResources
    compileEnMAPBoxResources()

    # copy EnMAP-Box icon source
    path_icon_source = DIR_REPO / config['enmapbox:files']['icon']
    path_icon_plugin = PLUGIN_DIR / config['enmapbox:metadata']['icon']
    assert path_icon_source.is_file(), f'Icon source does not exists: {path_icon_source}'
    shutil.copy(path_icon_source, path_icon_plugin)

    # copy python and other resource files
    root = DIR_REPO.as_posix()
    ignore_rx = [fileRegex(None, p) for p in config['enmapbox:files'].get('ignore').split()]
    include_rx = [fileRegex(root, p) for p in config['enmapbox:files'].get('include').split()]
    exclude_rx = [fileRegex(root, p) for p in config['enmapbox:files'].get('exclude').split()]

    files = []
    for file in scanfiles(DIR_REPO):
        path = file.as_posix()
        ignored = False
        for rx in ignore_rx + exclude_rx:
            if rx.match(path):
                ignored = True
                break
        if ignored:
            continue
        for rx in include_rx:
            if rx.match(path):
                files.append(file)
                break

    for fileSrc in files:
        assert fileSrc.is_file()
        fileDst = PLUGIN_DIR / fileSrc.relative_to(DIR_REPO)
        os.makedirs(fileDst.parent, exist_ok=True)
        shutil.copy(fileSrc, fileDst.parent)

    # make the LICENSE.md a LICENSE
    shutil.copy(PLUGIN_DIR / 'LICENSE.md', PLUGIN_DIR / 'LICENSE')

    # update metadata version

    f = open(DIR_REPO / 'enmapbox' / '__init__.py')
    lines = f.read()
    f.close()
    lines = re.sub(r'(__version__\W*=\W*)([^\n]+)', f'__version__ = "{BUILD_NAME}"\n', lines)
    lines = re.sub(r'(__version_sha__\W*=\W*)([^\n]+)', f'__version_sha__ = "{VERSION_SHA}"\n', lines)
    f = open(PLUGIN_DIR / 'enmapbox' / '__init__.py', 'w')
    f.write(lines)
    f.flush()
    f.close()

    # include test data into test versions
    if include_testdata:
        if os.path.isdir(enmapbox.DIR_EXAMPLEDATA):
            DEST = PLUGIN_DIR / 'enmapbox' / 'exampledata'
            shutil.copytree(enmapbox.DIR_EXAMPLEDATA, DEST, dirs_exist_ok=True)

    if include_qgisresources:
        qgisresources = Path(DIR_REPO) / 'qgisresources'
        shutil.copytree(qgisresources, PLUGIN_DIR / 'qgisresources')

    createCHANGELOG(PLUGIN_DIR)

    # Copy to other deploy directory
    QGIS_PROFILE_DEPLOY = None
    if DIR_QGIS_USERPROFILE:
        QGIS_PROFILE_DEPLOY = DIR_QGIS_USERPROFILE / 'python' / 'plugins' / PLUGIN_DIR.name
        # just in case the <profile>/python/plugins folder has not been created before
        os.makedirs(DIR_QGIS_USERPROFILE.parent, exist_ok=True)
        if QGIS_PROFILE_DEPLOY.is_dir():
            shutil.rmtree(QGIS_PROFILE_DEPLOY)
        shutil.copytree(PLUGIN_DIR, QGIS_PROFILE_DEPLOY)

    # Create a zip
    if create_zip:
        print('Create zipfile...')
        zipdir(PLUGIN_DIR, PLUGIN_ZIP)
        pluginSize: int = os.stat(PLUGIN_ZIP).st_size

        if pluginSize > MAX_PLUGIN_SIZE * 2 ** 20:
            msg = f'{PLUGIN_ZIP.name} ({QgsFileUtils.representFileSize(pluginSize)}) ' + \
                  f'Compressed plugin size exceeds limit of {MAX_PLUGIN_SIZE} MB)'

            if re.search(active_branch, r'release_.*', re.I):
                warnings.warn(msg, Warning, stacklevel=2)
            else:
                print(msg, file=sys.stderr)
        else:
            print(f'Compressed plugin size ({QgsFileUtils.representFileSize(pluginSize)}) ok.')

    print(f'Finished building {BUILD_NAME}', flush=True)

    if QGIS_PROFILE_DEPLOY:
        info = [f'Plugin copied to {QGIS_PROFILE_DEPLOY}',
                'Restart QGIS to load changes']
        print('\n'.join(info), flush=True)

    if create_zip:
        info = ['\n',
                '### To update/install the EnMAP-Box, run this command on your QGIS Python shell:',
                'from pyplugin_installer.installer import pluginInstaller',
                'pluginInstaller.installFromZipFile(r"{}")'.format(PLUGIN_ZIP),
                '#### Close (and restart manually)',
                'QProcess.startDetached(QgsApplication.arguments()[0], [])', 'QgsApplication.quit()',
                '## press ENTER',
                '\n']
        # print('iface.mainWindow().close()\n')

        print('\n'.join(info))

        return PLUGIN_ZIP

    return None


def markdownToHTML(path_md: Union[str, Path]) -> str:
    path_md = Path(path_md)

    html = None
    if not path_md.is_file():
        for s in ['.md', '.rst']:
            p = path_md.parent / (os.path.splitext(path_md.name)[0] + s)
            if p.is_file():
                path_md = p
                break

    if path_md.name.endswith('.rst'):

        assert path_md.is_file(), path_md
        overrides = {'stylesheet': None,
                     'embed_stylesheet': False,
                     'output_encoding': 'utf-8',
                     }

        buffer = io.StringIO()
        html = docutils.core.publish_file(
            source_path=path_md,
            writer_name='html5',
            destination=buffer,
            settings_overrides=overrides)
    elif path_md.name.endswith('.md'):
        with open(path_md, 'r', encoding='utf-8') as f:
            md = f.read()

            # skip start comment in autogenerated changelog.md
            if '# CHANGELOG' in md:
                rxComments = re.compile(r'^.*(?=# CHANGELOG)', re.DOTALL)
                md = rxComments.sub('', md)

                # skip details lines
                rxDetails = re.compile(r'</?details.*')
                md = rxDetails.sub('', md)

        html = markdown.markdown(''.join(md))
    else:
        raise Exception(f'Unsupported file: {path_md}')
    return html


def createCHANGELOG(dirPlugin: Path) -> str:
    """
    Reads the CHANGELOG.rst and creates the deploy/CHANGELOG (without extension!) for the QGIS Plugin Manager
    :return:
    """

    pathMD = DIR_REPO / 'CHANGELOG.md'
    pathCL = dirPlugin / 'CHANGELOG'

    os.makedirs(os.path.dirname(pathCL), exist_ok=True)
    assert os.path.isfile(pathMD)
    #    import sphinx.transforms

    html = markdownToHTML(pathMD)
    if False:
        xml = minidom.parseString(html)
        #  remove headline
        for i, node in enumerate(xml.getElementsByTagName('h1')):
            if i == 0:
                node.parentNode.removeChild(node)
            else:
                node.tagName = 'h4'

        for node in xml.getElementsByTagName('link'):
            node.parentNode.removeChild(node)

        for node in xml.getElementsByTagName('meta'):
            if node.getAttribute('name') == 'generator':
                node.parentNode.removeChild(node)

        xml = xml.getElementsByTagName('body')[0]
        html = xml.toxml()

    if True:
        html_cleaned = html
    else:
        html_cleaned = []
        for line in html.split('\n'):
            # line to modify
            line = re.sub(r'class="[^"]*"', '', line)
            line = re.sub(r'id="[^"]*"', '', line)
            line = re.sub(r'<li><p>', '<li>', line)
            line = re.sub(r'</p></li>', '</li>', line)
            line = re.sub(r'</?(dd|dt|div|body)[ ]*>', '', line)
            line = line.strip()
            if line != '':
                html_cleaned.append(line)
        html_cleaned = '\n'.join(html_cleaned)
    # make html compact
    # remove newlines as each line will be shown in a table row <tr>
    # see qgspluginmanager.cpp
    html_cleaned = html_cleaned.replace('\n', '')

    with open(pathCL, 'w', encoding='utf-8') as f:
        f.write(html_cleaned)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Install testdata', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-t', '--testdata',
                        required=False,
                        default=False,
                        help='Add enmapboxtestdata directory to plugin zip',
                        action='store_true')
    parser.add_argument('-q', '--qgisresources',
                        required=False,
                        default=False,
                        help='Add qgisresources directory to plugin zip. This is only required for test environments',
                        action='store_true')
    parser.add_argument('-z', '--skip_zip',
                        required=False,
                        default=False,
                        help='Skip zip file creation',
                        action='store_true')
    parser.add_argument('-b', '--build-name',
                        required=False,
                        default=None,
                        help=textwrap.dedent("""
                            The build name in "enmapboxplugin.<build name>.zip"
                            Defaults:
                                <version> in case of a release.* branch
                                <version>.<timestamp>.<branch name> in case of any other branch.
                            Can be specified by:
                            -b mytestversion -> enmapboxplugin.mytestversion.zip
                            """
                                             ))
    parser.add_argument('-p', '--profile',
                        nargs='?',
                        const=True,
                        default=False,
                        help=textwrap.dedent("""
                            Install the EnMAP-Box plugin into a QGIS user profile.
                            Requires that QGIS is closed. Use:
                            -p or --profile for installation into the active user profile
                            --profile=myProfile for installation install it into profile "myProfile"
                            """)
                        )

    args = parser.parse_args()

    path = create_enmapbox_plugin(include_testdata=args.testdata,
                                  include_qgisresources=args.qgisresources,
                                  create_zip=not args.skip_zip,
                                  copy_to_profile=args.profile,
                                  build_name=args.build_name)
