# this example shows how to save and restore settings
# check http://doc.qt.io/qt-5/qsettings.html#details for details


from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QApplication, QInputDialog
from enmapbox import enmapboxSettings


def printSettings(settings: QSettings):
    assert isinstance(settings, QSettings)
    print('# Organisation=' + settings.organizationName())
    print('# Application=' + settings.applicationName())
    for key in sorted(settings.allKeys()):
        print('{}={}'.format(key, settings.value(key, defaultValue='<EMPTY>')))


# 1. print official EnMAP-Box settings
printSettings(enmapboxSettings())

# 2. print own settings
mySettings = QSettings('My Software', 'My App')
printSettings(mySettings)

# 3. edit own settings
app = QApplication([])
oldText = mySettings.value('My Text', defaultValue='')
newText, ok = QInputDialog.getText(None, 'Set a text', 'New Text', text=oldText)
assert isinstance(ok, bool)
if ok:
    mySettings.setValue('My Text', newText)

# restart this script to see that 'My Text' was saved permanently.
