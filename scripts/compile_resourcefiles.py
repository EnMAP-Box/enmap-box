import pathlib
from qgis.testing import start_app

DIR_REPO = pathlib.Path(__file__).parents[1]


app = start_app()


def compileEnMAPBoxResources():
    from enmapbox.qgispluginsupport.qps.resources import compileResourceFiles
    directories = [DIR_REPO / 'enmapbox',
                   # DIR_REPO / 'site-packages'
                   ]

    for d in directories:
        compileResourceFiles(d, compressThreshold=100, compressLevel=19)


if __name__ == "__main__":
    compileEnMAPBoxResources()
    print('Finished')
