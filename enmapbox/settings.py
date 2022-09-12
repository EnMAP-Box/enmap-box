from typing import Any

from PyQt5.QtCore import QObject

from qgis.PyQt.QtCore import QSettings

from qgis.core import QgsSettingsEntryBase
from qgis.core import QgsSettingsEntryBool, QgsApplication


def enmapboxSettings() -> QSettings:
    """
    Returns the QSettings object for EnMAP-Box Settings
    :return: QSettings
    """
    return QSettings('HU-Berlin', 'EnMAP-Box')


class Keys:
    SHOW_WARNING = 'SHOW_WARNINGS'

class Settings(QObject):

    PREFIX = 'plugins/EnMAP-Box/'


    @classmethod
    def setEntry(cls, entry: QgsSettingsEntryBase):

        core = QgsApplication.instance().settingsRegistryCore()

        if not entry.definitionKey().startswith(cls.PREFIX):
            s = ""
        core.addSettingsEntry(entry)

    @classmethod
    def expandKey(cls, key:str):
        return f'{cls.PREFIX}{key}'

    @classmethod
    def entry(cls, name: str) -> QgsSettingsEntryBase:
        core = QgsApplication.instance().settingsRegistryCore()
        return core.settingsEntry(cls.expandKey(name))

    @classmethod
    def setEntryValue(cls, name: str, value: Any):
        e = cls.entry(name)
        if not isinstance(e, QgsSettingsEntryBase):
            if value is None:
                return

            # create new Entry
            key = name.removeprefix(cls.PREFIX)

            if isinstance(value, bool):
                e = QgsSettingsEntryBool(key, 'EnMAP-Box')
                core = QgsApplication.instance().settingsRegistryCore()
                e.setValue(value)
                core.addSettingsEntry(e)

            s = ""
        else:
            e.setVariantValue(value)

    @classmethod
    def entryValue(cls, name: str, default: Any = None) -> Any:
        e = cls.entry(name)
        if not isinstance(e, QgsSettingsEntryBase):
            return default
        value = e.valueAsVariant()
        if value is None:
            return default
        else:
            return value


