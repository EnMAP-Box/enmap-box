import os
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.gui import QgisInterface
import qgis.utils
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.applications import EnMAPBoxApplication

NAME = 'Image Cube'
VERSION = '0.2'
APP_DIR = os.path.dirname(__file__)


class ImageCubeApplication(EnMAPBoxApplication):
    mActionStartGUI: QAction

    def __init__(self, enmapBox: EnMAPBox, parent=None):

        super(ImageCubeApplication, self).__init__(enmapBox, parent=parent)

        self.name = NAME
        self.version = VERSION
        self.licence = 'GNU GPL-3'
        self.mErrorMessage = None
        # self.mImageCubeWidget: QWidget = None
        self.mIcon = enmapBox.icon()

    def icon(self):
        return self.mIcon

    def openglAvailable(self) -> bool:
        try:
            __import__('OpenGL')
            __import__('qgis.PyQt.QtOpenGL')
            self.mErrorMessage = None
            return True
        except (ImportError, ModuleNotFoundError) as ex:
            self.mErrorMessage = ex
            return False

    def menu(self, appMenu):
        appMenu = self.enmapbox.menu('Tools')
        assert isinstance(appMenu, QMenu)

        self.mActionStartGUI = self.utilsAddActionInAlphanumericOrder(appMenu, self.name)
        self.mActionStartGUI.setIcon(self.icon())
        self.mActionStartGUI.triggered.connect(self.startGUI)

        return None

    def startGUI(self, *args):

        if self.openglAvailable():
            from imagecubeapp.imagecube import ImageCubeWidget
            # if not isinstance(self.mImageCubeWidget, ImageCubeWidget):
            mImageCubeWidget = ImageCubeWidget()
            mImageCubeWidget.setWindowTitle(self.name)
            mImageCubeWidget.setWindowIcon(self.icon())
            mImageCubeWidget.sigExtentRequested.connect(self.onExtentRequested)
            mImageCubeWidget.show()
        else:
            text = ['Unable to start ' + NAME, 'OpenGL / PyQt5.QtOpenGL not available']
            if isinstance(self.mErrorMessage, Exception):
                text.append(str(self.mErrorMessage))
            text = '\n'.join(text)
            QMessageBox.information(None, 'Missing Package', text)

    def onExtentRequested(self, w):
        from imagecubeapp.imagecube import ImageCubeWidget
        if isinstance(w, ImageCubeWidget):
            canvases = self.enmapbox.mapCanvases()
            if isinstance(qgis.utils.iface, QgisInterface):
                canvases.extend(qgis.utils.iface.mapCanvases())
            for c in canvases:
                w.createExtentRequestMapTool(c)


def enmapboxApplicationFactory(enmapBox: EnMAPBox) -> list:
    """
    Returns a list of EnMAPBoxApplications
    :param enmapBox: the EnMAP-Box instance.
    :return: [list-of-EnMAPBoxApplications]
    """
    return [ImageCubeApplication(enmapBox)]
