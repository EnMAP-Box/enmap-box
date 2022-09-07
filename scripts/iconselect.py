import pathlib

from qgis.PyQt.QtWidgets import QApplication


def run():
    from enmapbox.qgispluginsupport.qps.resources import ResourceBrowser
    from enmapbox.qgispluginsupport.qps.testing import start_app
    from enmapbox.gui import file_search

    DIR_REPO = pathlib.Path(__file__).resolve().parents[1]
    resource_files = list(file_search(DIR_REPO, '*_rc.py', recursive=True))
    needApp = not isinstance(QApplication.instance(), QApplication)
    if needApp:
        app = start_app(resources=resource_files)

    global browser
    browser = ResourceBrowser()
    browser.setWindowTitle('EnMAP-Box Resource Browser')
    browser.show()

    if needApp:
        app.exec_()


if __name__ == '__main__':
    run()
