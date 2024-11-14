import unittest
import time
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QWidget

from enmapbox.gui.splashscreen.splashscreen import EnMAPBoxSplashScreen
from enmapbox.testing import EnMAPBoxTestCase, start_app

start_app()


class TestEnMAPBoxSplashScreen(EnMAPBoxTestCase):

    def test_splashScreen(self):
        w = QWidget()

        splash = EnMAPBoxSplashScreen(parent=w)
        self.assertIsInstance(splash, EnMAPBoxSplashScreen)
        i = 0
        splash.showMessage('Message {} {}'.format(i, str(time.time())))

        def onTimeOut(*args):
            nonlocal i
            splash.showMessage('Message {} {}'.format(i, str(time.time())))
            i += 1

        # self.assertFalse(splash.size().isNull())

        timer = QTimer()
        timer.startTimer(2)
        timer.timeout.connect(onTimeOut)

        self.showGui([w, splash])


if __name__ == '__main__':

    unittest.main(buffer=False)
