import unittest

from enmapbox.dependencycheck import requiredPackages
from enmapbox.enmapboxplugin import EnMAPBoxPlugin
from enmapbox.testing import start_app, EnMAPBoxTestCase
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMessageBox

start_app()


class EnMAPBoxPluginTests(EnMAPBoxTestCase):
    def test_load_with_missing(self):
        plugin = EnMAPBoxPlugin()

        if plugin.corePackagesAvailable():
            self.assertTrue(len(plugin.mMissingCoreRequirements) == 0)

        plugin.initGui()
        plugin.unload()
        plugin.initProcessing()
        plugin.unload()

    def test_missing_package_infos(self):

        required = requiredPackages()
        missing = [p for p in required if p.isCoreRequirement()]

        msg_cli = EnMAPBoxPlugin.missingPackageInfos(missing, cli=True)
        msg_gui = EnMAPBoxPlugin.missingPackageInfos(missing, cli=False)
        for m in missing:
            self.assertTrue(m.pipPkgName in msg_cli)
            self.assertTrue(m.pipPkgName in msg_gui)

        mbox = QMessageBox()
        mbox.setWindowTitle('Missing Packages')
        mbox.setTextFormat(Qt.TextFormat.RichText)
        mbox.setText(msg_gui)
        self.showGui(mbox)


if __name__ == '__main__':
    unittest.main()
