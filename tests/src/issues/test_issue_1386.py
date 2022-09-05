"""
This is a template to create an EnMAP-Box test
"""
import unittest

from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QMenu, QWidgetAction, QToolButton

from enmapbox.qgispluginsupport.qps.plotstyling.plotstyling import PlotStyleButton
from enmapbox.testing import EnMAPBoxTestCase
from qgis.gui import QgsColorButton


class TestCaseIssue1386(EnMAPBoxTestCase):

    def test_issue_1386(self):
        tBtn = QToolButton()

        w = QWidget()

        ly = QVBoxLayout()
        cBtn = QgsColorButton()
        ly.addWidget(cBtn)
        w.setLayout(ly)

        menu = QMenu(parent=tBtn)
        # menu.triggered.connect(self.onAboutToShowMenu)

        mWA = QWidgetAction(menu)
        mWA.setDefaultWidget(w)
        menu.addAction(mWA)
        # menu.aboutToShow.connect(self.onAboutToShowMenu)

        tBtn.setMenu(menu)

        tBtn.setPopupMode(QToolButton.MenuButtonPopup)

        # tb.clicked.connect(lambda: self.activateWindow())
        self.showGui(tBtn)

    def test_plotStyleWidget(self):
        btn = PlotStyleButton()

        self.showGui(btn)


if __name__ == '__main__':
    unittest.main(buffer=False)
