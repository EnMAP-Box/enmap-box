import unittest

from enmapbox.enmapboxplugin import EnMAPBoxPlugin
from enmapbox.testing import start_app

start_app()


class EnMAPBoxPluginTests(unittest.TestCase):
    def test_load_with_missing(self):
        plugin = EnMAPBoxPlugin()

        if plugin.corePackagesAvailable():
            self.assertTrue(len(plugin.mMissingCoreRequirements) == 0)

        plugin.initGui()
        plugin.unload()
        plugin.initProcessing()
        plugin.unload()


if __name__ == '__main__':
    unittest.main()
