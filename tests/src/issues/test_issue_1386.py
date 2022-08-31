"""
This is a template to create an EnMAP-Box test
"""
import unittest

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMenu, QWidgetAction, QToolButton

from qgis.PyQt.QtWidgets import QApplication
from qgis._gui import QgsColorButton
from qgis.core import QgsApplication, QgsRasterLayer, QgsVectorLayer
from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from enmapbox import EnMAPBox
from qps.plotstyling.plotstyling import PlotStyleWidget, PlotStyleButton


class TestCaseIssue1386(EnMAPBoxTestCase):

    def test_issue_1386(self):

        tBtn = QToolButton()

        w = QWidget()

        ly = QVBoxLayout()
        cBtn = QgsColorButton()
        ly.addWidget(cBtn)
        w.setLayout(ly)

        menu = QMenu(parent=tBtn)
        #menu.triggered.connect(self.onAboutToShowMenu)

        mWA = QWidgetAction(menu)
        mWA.setDefaultWidget(w)
        menu.addAction(mWA)
        #menu.aboutToShow.connect(self.onAboutToShowMenu)

        tBtn.setMenu(menu)

        tBtn.setPopupMode(QToolButton.MenuButtonPopup)

        # tb.clicked.connect(lambda: self.activateWindow())
        self.showGui(tBtn)

    def test_plotStyleWidget(self):

        btn = PlotStyleButton()

        self.showGui(btn)


if __name__ == '__main__':
    unittest.main(buffer=False)
