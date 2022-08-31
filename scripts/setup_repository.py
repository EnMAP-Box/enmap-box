"""
Initial setup of the EnMAP-Box repository.
Run this script after you have cloned the EnMAP-Box repository
"""
import pathlib
import site

def setup_enmapbox_repository():
    # specify the local path to the cloned QGIS repository


    DIR_REPO = pathlib.Path(__file__).parents[1].resolve()
    DIR_SITEPACKAGES = DIR_REPO / 'site-packages'
    DIR_QGISRESOURCES = DIR_REPO / 'qgisresources'

    site.addsitedir(DIR_REPO)

    from scripts.compile_resourcefiles import compileEnMAPBoxResources
    from scripts.install_testdata import install_qgisresources, install_exampledata

    # 1. compile EnMAP-Box resource files (*.qrc) into corresponding python modules (*.py)
    print('Compile EnMAP-Box resource files...')
    compileEnMAPBoxResources()

    # 2. install the EnMAP-Box test data
    print('Install EnMAP-Box Test Data')
    install_exampledata()

    print('Install QGIS resource files')
    install_qgisresources()
    print('EnMAP-Box repository setup finished')


if __name__ == "__main__":
    print('setup repository')
    setup_enmapbox_repository()
