#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
***************************************************************************
    about
    ---------------------
    Date                 : September 2017
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
import pathlib
from qgis.PyQt.QtWidgets import QDialog
from enmapbox import DIR_REPO, ABOUT, REPOSITORY
from enmapbox.gui.utils import loadUi


class AboutDialog(QDialog):
    def __init__(self, *args, **kwds):
        """Constructor."""
        super().__init__(*args, **kwds)
        from enmapbox import DIR_UIFILES
        pathUi = pathlib.Path(DIR_UIFILES) / 'aboutdialog.ui'
        loadUi(pathUi, self)

        self.mTitle = self.windowTitle()
        self.listWidget.currentItemChanged.connect(lambda: self.setAboutTitle())
        from enmapbox import __version__, __version_sha__
        info = f'Version {__version__}'
        if len(__version_sha__) > 10:
            info += f'\t Code ' \
                    f'<a href="{REPOSITORY.replace(".git", "")}/commit/{__version_sha__}">{__version_sha__[0:11]}</a>'
        self.labelVersion.setText(info)
        self.setAboutTitle()

        def loadTextFile(p):
            if not os.path.isfile(p):
                return 'File not found "{}"'.format(p)

            f = open(p, 'r', encoding='utf-8')
            lines = f.read()
            f.close()
            return lines

        self.labelAboutText.setText(f'<html><head/><body>{ABOUT}</body></html>')
        self.tbLicense.setText(loadTextFile(os.path.join(DIR_REPO, 'LICENSE.md')))
        self.tbContributors.setText(loadTextFile(os.path.join(DIR_REPO, 'CONTRIBUTORS.rst')))
        self.tbChanges.setText(loadTextFile(os.path.join(DIR_REPO, 'CHANGELOG.rst')))

    def setAboutTitle(self, suffix=None):
        item = self.listWidget.currentItem()

        if item:
            title = '{} | {}'.format(self.mTitle, item.text())
        else:
            title = self.mTitle
        if suffix:
            title += ' ' + suffix
        self.setWindowTitle(title)


if __name__ == '__main__':
    from enmapbox.testing import initQgisApplication

    app = initQgisApplication()
    d = AboutDialog()
    d.show()
    app.exec_()
