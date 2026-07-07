from enmapbox.gui.widgets.codeeditwidget import CodeEditWidget
from enmapbox.testing import EnMAPBoxTestCase

from enmapbox.testing import start_app

start_app()


class TestCodeEditWidget(EnMAPBoxTestCase):

    def test_code_edit_widget(self):
        w = CodeEditWidget()

        self.showGui(w)
