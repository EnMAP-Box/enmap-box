from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QCheckBox, QFormLayout
from qgis.gui import (QgsColorButton, QgsOptionsPageWidget, QgsOptionsWidgetFactory)

from enmapbox import icon
from enmapbox.enmapboxsettings import EnMAPBoxSettings


class EnMAPBoxOptionsPage(QgsOptionsPageWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        settings = EnMAPBoxSettings()

        self.showWarnings = QCheckBox("Show warnings")
        self.showWarnings.setChecked(settings.value(EnMAPBoxSettings.SHOW_WARNING, True, type=bool))

        self.showSplashscreen = QCheckBox("Show splash screen")
        self.showSplashscreen.setChecked(settings.value(EnMAPBoxSettings.SHOW_SPLASHSCREEN, True, type=bool))

        self.mapBackground = QgsColorButton(self)
        self.mapBackground.setColor(settings.value(EnMAPBoxSettings.MAP_BACKGROUND, QColor("black")))

        layout = QFormLayout(self)
        layout.addRow(self.showWarnings)
        layout.addRow(self.showSplashscreen)
        layout.addRow("Map background:", self.mapBackground)

    def apply(self):
        settings = EnMAPBoxSettings()
        settings.setValue(EnMAPBoxSettings.SHOW_WARNING, self.showWarnings.isChecked())
        settings.setValue(EnMAPBoxSettings.SHOW_SPLASHSCREEN, self.showSplashscreen.isChecked())
        settings.setValue(EnMAPBoxSettings.MAP_BACKGROUND, self.mapBackground.color())


class EnMAPBoxOptionsFactory(QgsOptionsWidgetFactory):

    def __init__(self):
        super().__init__("EnMAP-Box", icon())

    def createWidget(self, parent=None):
        return EnMAPBoxOptionsPage(parent)
