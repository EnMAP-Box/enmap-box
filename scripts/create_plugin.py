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
import pathlib
import re
import shutil
import site
import sys
import textwrap
import typing
import warnings
from os.path import exists

from qgis.core import QgsUserProfileManager, QgsUserProfile

site.addsitedir(pathlib.Path(__file__).parents[1])  # noqa

from qgis.testing import start_app

app = start_app()
import enmapbox
from enmapbox import DIR_REPO
from enmapbox.qgispluginsupport.qps.make.deploy import QGISMetadataFileWriter, userProfileManager
from enmapbox.qgispluginsupport.qps.utils import zipdir
from qgis.core import QgsFileUtils

# concider default Git location on Windows systems to avaid creating a Start-Up Script
addDefaultGitLocation = True
if addDefaultGitLocation:
    potentialGitPath = r"C:\Program Files\Git\bin"
    if exists(potentialGitPath):
        os.environ["PATH"] = os.environ["PATH"] + os.pathsep + potentialGitPath
    import git

DIR_REPO = pathlib.Path(DIR_REPO)

PATH_CONFIG_FILE = DIR_REPO / '.plugin.ini'
assert PATH_CONFIG_FILE.is_file()


def scanfiles(root: typing.Union[str, pathlib.Path]) -> typing.Iterator[pathlib.Path]:
    """
    Recursively returns file paths in directory
    :param root: root directory to search in
    :return: pathlib.Path
    """

    for entry in os.scandir(root):
        entry: os.DirEntry
        if entry.is_dir(follow_symlinks=False):
            yield from scanfiles(entry.path)
        else:
            path = pathlib.Path(entry.path)
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
                           build_name: str = None) -> typing.Optional[pathlib.Path]:
    assert (DIR_REPO / '.git').is_dir()
    config = configparser.ConfigParser()
    config.read(PATH_CONFIG_FILE)

    MAX_PLUGIN_SIZE = int(config['plugin']['max_size_mb'])
    DIR_DEPLOY_LOCAL = DIR_REPO / 'deploy'
    DIR_QGIS_USERPROFILE: pathlib.Path = None

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

        DIR_QGIS_USERPROFILE = pathlib.Path(profile.folder())
        if DIR_QGIS_USERPROFILE:
            os.makedirs(DIR_QGIS_USERPROFILE, exist_ok=True)
            if not DIR_QGIS_USERPROFILE.is_dir():
                raise f'QGIS profile directory "{profile.name()}" does not exists: {DIR_QGIS_USERPROFILE}'

    REPO = git.Repo(DIR_REPO)
    active_branch = REPO.active_branch.name
    VERSION = config['metadata']['version']
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
        if BUILD_NAME == VERSION:
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

    # set QGIS Metadata file values
    MD = QGISMetadataFileWriter()
    MD.mName = config['metadata']['name']
    MD.mDescription = config['metadata']['description']
    MD.mTags = config['metadata']['tags'].strip().split('\n')
    MD.mCategory = config['metadata']['category']
    MD.mAuthor = config['metadata']['authors'].strip().split('\n')
    MD.mIcon = config['metadata']['icon']
    MD.mHomepage = config['metadata']['homepage']
    MD.mAbout = enmapbox.ABOUT
    MD.mTracker = enmapbox.ISSUE_TRACKER
    MD.mRepository = enmapbox.REPOSITORY
    MD.mQgisMinimumVersion = enmapbox.MIN_VERSION_QGIS
    MD.mEmail = config['metadata']['email']
    MD.mHasProcessingProvider = True
    MD.mPlugin_dependencies = ['Google Earth Engine']  # the best way to make sure that the 'ee' module is available

    MD.mVersion = VERSION
    MD.writeMetadataTxt(PATH_METADATAFILE)

    # (re)-compile all enmapbox resource files
    from scripts.compile_resourcefiles import compileEnMAPBoxResources
    compileEnMAPBoxResources()

    # copy EnMAP-Box icon source
    path_icon_source = DIR_REPO / config['files']['icon']
    path_icon_plugin = PLUGIN_DIR / config['metadata']['icon']
    assert path_icon_source.is_file(), f'Icon source does not exists: {path_icon_source}'
    shutil.copy(path_icon_source, path_icon_plugin)

    # copy python and other resource files
    root = DIR_REPO.as_posix()
    ignore_rx = [fileRegex(None, p) for p in config['files'].get('ignore').split()]
    include_rx = [fileRegex(root, p) for p in config['files'].get('include').split()]
    exclude_rx = [fileRegex(root, p) for p in config['files'].get('exclude').split()]

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
        qgisresources = pathlib.Path(DIR_REPO) / 'qgisresources'
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


def createCHANGELOG(dirPlugin):
    """
    Reads the CHANGELOG.rst and creates the deploy/CHANGELOG (without extension!) for the QGIS Plugin Manager
    :return:
    """

    pathMD = os.path.join(DIR_REPO, 'CHANGELOG.rst')
    pathCL = os.path.join(dirPlugin, 'CHANGELOG')

    os.makedirs(os.path.dirname(pathCL), exist_ok=True)
    assert os.path.isfile(pathMD)
    #    import sphinx.transforms
    import docutils.core

    overrides = {'stylesheet': None,
                 'embed_stylesheet': False,
                 'output_encoding': 'utf-8',
                 }

    buffer = io.StringIO()
    html = docutils.core.publish_file(
        source_path=pathMD,
        writer_name='html5',
        destination=buffer,
        settings_overrides=overrides)

    from xml.dom import minidom
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
    # make html compact

    with open(pathCL, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_cleaned))


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

    if isinstance(path, pathlib.Path) and re.search(r'\.master\.', path.name):
        message = \
            r"""
            Very important checklist. Do not remove!!!
            Checklist for release:
            Run scripts\runtests.bat (win) or scripts/runtests.sh (linux/mac)
            Change log up-to-date?
            Processing algo documentation up-to-date (run create_processing_rst).
            Run weblink checker (in doc folder make linkcheck).
            Check if box runs without optional dependencies (see tests/non-blocking-dependencies/readme.txt).
            Version number increased? (enmapbox/__init__.py -> __version__)
            QGIS Min-Version? (enmapbox/__init__.py -> MIN_VERSION_QGIS)
            ZIP containing branch (i.e. master) information (GIT installed)?
            Install ZIP and quick-test under the latest supported QGIS versions and OS, e.g.:
                Andreas: latest Windows Conda QGIS
                Fabian: Linux QGIS used in Greifswald-Teaching
                Benjamin: latest OSGeo4W (maybe also MacOS?) QGIS
                Plugin promotion (Slack, Email, ...)
                  RTD
                  Email an Saskia: update auf enmap.org (enmap news + enmap news letter)
                  Email an enmap_wiss@gfz-potsdam.de
                  Email an Ettore: reach out to PRISMA community
                  EOL Slack + EnMAP Slack
                  EOL Twitter
            """

        print(message)
