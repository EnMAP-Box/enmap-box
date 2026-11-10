from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QCheckBox, QWidget
from qgis.PyQt.QtWidgets import QSizePolicy, QVBoxLayout
from qgis.PyQt.uic import loadUi
from qgis.gui import (QgsColorButton, QgsOptionsPageWidget, QgsOptionsWidgetFactory)

from enmapbox import icon
from enmapbox.enmapboxsettings import EnMAPBoxSettings


class EnMAPBoxSettingsPageWidget(QgsOptionsPageWidget):

    PAGE_NAME = "EnMAPBoxSettingsPageWidget"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(self.PAGE_NAME)

        settings = EnMAPBoxSettings()
        self.w = EnMAPBoxOptionsWidget()

        self.w.mShowWarnings.setChecked(settings.value(EnMAPBoxSettings.SHOW_WARNING, True, type=bool))
        self.w.mShowSplashScreen.setChecked(settings.value(EnMAPBoxSettings.SHOW_SPLASHSCREEN, True, type=bool))
        self.w.mMapBackground.setColor(settings.value(EnMAPBoxSettings.MAP_BACKGROUND, QColor("black")))

        self.w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.w)

    def apply(self):
        settings = EnMAPBoxSettings()
        settings.setValue(EnMAPBoxSettings.SHOW_WARNING, self.w.mShowWarnings.isChecked())
        settings.setValue(EnMAPBoxSettings.SHOW_SPLASHSCREEN, self.w.mShowSplashScreen.isChecked())
        settings.setValue(EnMAPBoxSettings.MAP_BACKGROUND, self.w.mMapBackground.color())


class EnMAPBoxSettingsPageWidgetFactory(QgsOptionsWidgetFactory):

    def __init__(self):
        super().__init__("EnMAP-Box", icon())

    def createWidget(self, parent=None):
        return EnMAPBoxSettingsPageWidget(parent)


class EnMAPBoxOptionsWidget(QWidget):
    mShowWarnings: QCheckBox
    mShowSplashScreen: QCheckBox
    mMapBackground: QgsColorButton

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)
