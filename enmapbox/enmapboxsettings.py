from qgis.PyQt.QtGui import QColor

from qgis.core import QgsSettings


class EnMAPBoxSettings(QgsSettings):
    SHOW_WARNING = 'SHOW_WARNINGS'
    SHOW_SPLASHSCREEN = 'SHOW_SPLASHSCREEN'
    MAP_BACKGROUND = 'MAP_BACKGROUND'

    def __init__(self):
        super().__init__('EnMAP', 'EnMAP-Box')

        # init default settings
        self.setIfUndefined(self.SHOW_WARNING, True)
        self.setIfUndefined(self.SHOW_SPLASHSCREEN, True)
        self.setIfUndefined(self.MAP_BACKGROUND, QColor('black'))

    def setIfUndefined(self, key, value):
        if key not in self.allKeys():
            self.setValue(key, value)

    def print(self):
        print('EnMAP-Box Settings:')
        for k in self.allKeys():
            print(f'{k}={self.value(k)}')


def enmapboxSettings() -> EnMAPBoxSettings:
    return EnMAPBoxSettings()
