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
import pathlib
import webbrowser
from typing import Union

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtWidgets import QTextBrowser
from qgis.PyQt.QtCore import Qt
from enmapbox import DIR_REPO, REPOSITORY
from enmapbox.gui.utils import loadUi
from qgis.PyQt.QtWidgets import QDialog


def anchorClicked(url: QUrl):
    """Opens a URL in local browser / mail client"""
    assert isinstance(url, QUrl)
    webbrowser.open(url.url())


class AboutDialog(QDialog):
    def __init__(self, *args, **kwds):
        """Constructor."""
        super().__init__(*args, **kwds)
        from enmapbox import DIR_UIFILES
        pathUi = pathlib.Path(DIR_UIFILES) / 'aboutdialog.ui'
        loadUi(pathUi, self)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.tbAbout: QTextBrowser
        self.tbLicense: QTextBrowser
        self.tbCredits: QTextBrowser
        self.tbContributors: QTextBrowser
        self.tbChanges: QTextBrowser

        for tb in [self.tbAbout, self.tbLicense, self.tbCredits, self.tbContributors, self.tbChanges]:
            tb: QTextBrowser
            tb.setOpenLinks(False)
            tb.setOpenExternalLinks(False)

        self.tbAbout.anchorClicked.connect(anchorClicked)
        self.tbLicense.anchorClicked.connect(anchorClicked)
        self.tbCredits.anchorClicked.connect(anchorClicked)
        self.tbContributors.anchorClicked.connect(anchorClicked)
        self.tbChanges.anchorClicked.connect(anchorClicked)

        self.mTitle = self.windowTitle()
        self.listWidget.currentItemChanged.connect(lambda: self.setAboutTitle())
        from enmapbox import __version__, __version_sha__
        info = f'Version {__version__}'
        if len(__version_sha__) > 10:
            info += f'\t Code ' \
                    f'<a href="{REPOSITORY.replace(".git", "")}/commit/{__version_sha__}">{__version_sha__[0:11]}</a>'
        self.labelVersion.setText(info)
        self.setAboutTitle()

        def loadMDAndremoveDetailsSection(p: Union[str, pathlib.Path]):  # see issue #990
            with open(p, 'r', encoding='utf-8') as f:
                md = f.readlines()
            md = [l for l in md if 'details>' not in l]
            return ''.join(md)

        def loadMD(p: Union[str, pathlib.Path]):
            p = pathlib.Path(p)

            try:
                assert p.is_file()
                assert p.name.endswith('.md')
                with open(p, 'r', encoding='utf-8') as f:
                    md = f.read()
            except (AssertionError, FileNotFoundError) as ex:
                md = f'Unable to load "{p}"\n{ex}'
            return md

        r = pathlib.Path(DIR_REPO)

        # self.labelAboutText.setText(f'<html><head/><body>{ABOUT}</body></html>')
        self.tbAbout.setMarkdown(loadMD(r / 'ABOUT.md'))
        self.tbLicense.setMarkdown(loadMD(r / 'LICENSE.md'))
        self.tbCredits.setMarkdown(loadMD(r / 'CREDITS.md'))
        self.tbContributors.setMarkdown(loadMD(r / 'CONTRIBUTORS.md'))
        self.tbChanges.setMarkdown(loadMDAndremoveDetailsSection(r / 'CHANGELOG.md'))

    def setAboutTitle(self, suffix: str = None):
        """
        Sets the dialog title
        """
        item = self.listWidget.currentItem()

        if item:
            title = '{} | {}'.format(self.mTitle, item.text())
        else:
            title = self.mTitle
        if suffix:
            title += ' ' + suffix
        self.setWindowTitle(title)


if __name__ == '__main__':
    from enmapbox.testing import start_app

    app = start_app()
    d = AboutDialog()
    d.show()
    app.exec_()
