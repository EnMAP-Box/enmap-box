from functools import partial
from pathlib import Path

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.PyQt.QtGui import QIcon, QDesktopServices

import enmapbox
from enmapbox import DIR_UIFILES
from enmapbox.qgispluginsupport.qps.utils import loadUi
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsApplication
from qgis.core import QgsSettings
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory


class EnMAPBoxSettings(QgsSettings):
    SHOW_WARNING = 'SHOW_WARNINGS'
    SHOW_SPLASHSCREEN = 'SHOW_SPLASHSCREEN'
    MAP_BACKGROUND = 'MAP_BACKGROUND'
    STARTUP_LOAD_PROJECT = 'STARTUP_LOAD_PROJECT'

    def __init__(self):
        super().__init__('EnMAP', 'EnMAP-Box')

        # init default settings
        self.setIfUndefined(self.SHOW_WARNING, True)
        self.setIfUndefined(self.SHOW_SPLASHSCREEN, True)
        self.setIfUndefined(self.MAP_BACKGROUND, QColor('black'))
        self.setIfUndefined(self.STARTUP_LOAD_PROJECT, False)

    def setIfUndefined(self, key, value):
        if key not in self.allKeys():
            self.setValue(key, value)

    def print(self):
        print('EnMAP-Box Settings:')
        for k in self.allKeys():
            print(f'{k}={self.value(k)}')

    def valueAsBool(self, key, default=None) -> bool:
        v = self.value(key, default)
        if isinstance(v, bool):
            return v
        else:
            return str(v).lower() in ['1', 'true']


def enmapboxSettings() -> EnMAPBoxSettings:
    return EnMAPBoxSettings()


class EnMAPBoxSettingsPage(QgsOptionsPageWidget):
    """Settings form embedded into QGIS 'options' menu."""

    configChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.log = PlgLogger().log
        # self.plg_settings = PlgOptionsManager()
        # self.setupUi(self)
        loadUi(Path(DIR_UIFILES) / 'settingspage.ui', self)
        # load UI and set objectName
        self.setObjectName("mOptionsPageEnMAPBox")
        from enmapbox import __version__, URL_INSTALLATION
        # header
        self.labelTitle.setText(f"EnMAPBox - Version {__version__}")

        # customization
        self.btnHelp.setIcon(QIcon(QgsApplication.iconPath("mActionHelpContents.svg")))
        self.btnHelp.pressed.connect(
            partial(QDesktopServices.openUrl, QUrl(URL_INSTALLATION))
        )

        self.btnReport.setIcon(
            QIcon(QgsApplication.iconPath("console/iconSyntaxErrorConsole.svg"))
        )
        import enmapbox
        self.btnReport.pressed.connect(
            partial(QDesktopServices.openUrl, QUrl(enmapbox.CREATE_ISSUE))
        )

        self.btnReset.setIcon(QIcon(QgsApplication.iconPath("mActionUndo.svg")))
        self.btnReset.pressed.connect(self.resetSettings)

        # load previously saved settings
        self.loadSettings()

    def apply(self):
        """Called to permanently apply the settings shown in the options page (e.g. \
        save them to QgsSettings objects). This is usually called when the options \
        dialog is accepted."""
        settings = self.get_plg_settings()

        # misc
        settings.debug_mode = self.opt_debug.isChecked()
        settings.toolbar_browser_shortcut = (
            self.opt_toolbar_browser_shortcut.isChecked()
        )
        settings.version = enmapbox.__version__

        prefix_filters = self.te_resource_prefixes.toPlainText().strip().split("\n")
        filetype_filters = self.te_resource_filetypes.toPlainText().strip().split("\n")
        settings.prefix_filters = [f for f in prefix_filters if f != ""]
        settings.filetype_filters = [f for f in filetype_filters if f != ""]
        settings.filter_filetypes = self.gb_filter_resourcefiletype.isChecked()
        settings.filter_prefixes = self.gb_filter_resourceprefix.isChecked()

        # dump new settings into QgsSettings
        self.plg_settings.save_from_object(settings)

        if __debug__:
            self.log(
                message="DEBUG - Settings successfully saved.",
                log_level=4,
            )
        self.configChanged.emit()

    def loadSettings(self):
        """Load options from QgsSettings into UI form."""
        settings = enmapboxSettings()

        # set settings widgets
        self.cbDebugMode.setChecked(settings.value('DEBUG_MODE', defaultValue=False))
        self.labelTitle.setText(enmapbox.__version__)

    def resetSettings(self):
        """Reset settings to default values (set in preferences.py module)."""

        # default_settings = PlgSettingsStructure()

        # dump default settings into QgsSettings
        # self.plg_settings.save_from_object(default_settings)

        # update the form
        self.loadSettings()
        self.configChanged.emit()


class EnMAPBoxOptionsFactory(QgsOptionsWidgetFactory):
    """Factory for options widget."""

    configChanged = pyqtSignal()

    def __init__(self):
        """Constructor."""
        super().__init__()

    def icon(self) -> QIcon:
        """Returns plugin icon, used to as tab icon in QGIS options tab widget.

        :return: _description_
        :rtype: QIcon
        """
        return enmapbox.icon()

    def createWidget(self, parent) -> EnMAPBoxSettingsPage:
        """Create settings widget.

        :param parent: Qt parent where to include the options page.
        :type parent: QObject

        :return: options page for tab widget
        :rtype: ConfigOptionsPage
        """
        page = EnMAPBoxSettingsPage(parent)
        page.configChanged.connect(self.configChanged.emit)
        return page

    def title(self) -> str:
        """Returns plugin title, used to name the tab in QGIS options tab widget.

        :return: plugin title from about module
        :rtype: str
        """

        return 'EnMAP-Box'

    def helpId(self) -> str:
        """Returns plugin help URL.

        :return: plugin homepage url from about module
        :rtype: str
        """
        return enmapbox.DOCUMENTATION
