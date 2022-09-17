# -*- coding: utf-8 -*-
"""
***************************************************************************
    __init__.py
    ---------------------
    Date                 : October 2018
    Copyright            : (C) 2018 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This file is part of the EnMAP-Box.                                   *
*                                                                         *
*   The EnMAP-Box is free software; you can redistribute it and/or modify *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
*   The EnMAP-Box is distributed in the hope that it will be useful,      *
*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          *
*   GNU General Public License for more details.                          *
*                                                                         *
*   You should have received a copy of the GNU General Public License     *
*   along with the EnMAP-Box. If not, see <http://www.gnu.org/licenses/>. *
*                                                                         *
***************************************************************************
"""

# make EnMAP-Box site-packages available
import sys
from os.path import dirname, join
import os

sys.path.append(join(dirname(__file__), 'site-packages'))


def classFactory(iface):
    """
    Loads the EnMAP-Box Plugin
    :param iface:
    :return: enmapboxplugin.EnMAPBoxPlugin(iface)
    """

    pluginDirectory = os.path.dirname(__file__)
    added = []
    if pluginDirectory not in sys.path:
        sys.path.append(pluginDirectory)
        added.append(pluginDirectory)
    try:
        from enmapbox.enmapboxplugin import EnMAPBoxPlugin
        plugin = EnMAPBoxPlugin(iface)
    except ModuleNotFoundError as ex:
        for path in added:
            sys.path.remove(path)
        raise ex
    return plugin
