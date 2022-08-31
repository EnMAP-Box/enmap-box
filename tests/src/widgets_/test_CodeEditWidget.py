from enmapbox.gui.widgets.codeeditwidget import CodeEditWidget
from enmapbox.testing import EnMAPBoxTestCase


class TestCodeEditWidget(EnMAPBoxTestCase):

    def test(self):
        w = CodeEditWidget()
        # nothing really to test here, because the whole purpose of the widget is code highlighting
