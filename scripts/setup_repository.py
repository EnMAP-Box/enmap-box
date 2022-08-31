"""
Initial setup of the EnMAP-Box repository.
Run this script after you have cloned the EnMAP-Box repository
"""
import pathlib
import site
import requests
import zipfile
import io
import os
import shutil
import argparse

DIR_REPO = pathlib.Path(__file__).parents[1].resolve()
site.addsitedir(DIR_REPO)


def install_zipfile(url: str, localPath: pathlib.Path, zip_root: str = None):
    assert isinstance(localPath, pathlib.Path)
    localPath = localPath.resolve()

    print('Download {} \nto {}'.format(url, localPath))

    response = requests.get(url, stream=True)

    z = zipfile.ZipFile(io.BytesIO(response.content))
    os.makedirs(localPath, exist_ok=True)
    for src in z.namelist():
        srcPath = pathlib.Path(src)
        if isinstance(zip_root, str):
            if zip_root not in srcPath.parts:
                continue
            i = srcPath.parts.index(zip_root)
            dst = localPath / pathlib.Path(*srcPath.parts[i + 1:])
        else:
            dst = localPath / pathlib.Path(*srcPath.parts)
        info = z.getinfo(src)
        if info.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            os.makedirs(dst, exist_ok=True)
        else:
            if dst.exists():
                os.remove(dst)
            with open(dst, "wb") as f:
                f.write(z.read(src))

    # z.extractall(path=localPath, members=to_extract)
    del response


def install_qgisresources():
    localpath = DIR_REPO / 'qgisresources'
    from enmapbox import URL_QGIS_RESOURCES
    install_zipfile(URL_QGIS_RESOURCES, localpath)


def setup_enmapbox_repository(resources=True, qgis_resources=True):
    # specify the local path to the cloned QGIS repository

    # 1. compile EnMAP-Box resource files (*.qrc) into corresponding python modules (*.py)
    if resources:
        print('Compile EnMAP-Box resource files...')
        from scripts.compile_resourcefiles import compileEnMAPBoxResources
        compileEnMAPBoxResources()

    if qgis_resources:
        print('Install QGIS resource files')
        install_qgisresources()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Setup Repository. Run this after you have cloned the '
                                                 'EnMAP-Box repository')
    parser.add_argument('-r', '--resources',
                        required=False,
                        default=False,
                        help='Create *_rc.py resource file modules from *.qrc files',
                        action='store_true'
                        )

    parser.add_argument('-q', '--qgisresources',
                        required=False,
                        default=False,
                        action='store_true',
                        help='Download and install QGIS resource files compiled as *_rc.py modules',
                        )

    args = parser.parse_args()

    if not any([args.resources,
                args.qgisresources]):
        args.resources = True
        args.qgisresources = True

    print('Setup repository')
    setup_enmapbox_repository(resources=args.resources,
                              qgis_resources=args.qgisresources)
    print('EnMAP-Box repository setup finished')
