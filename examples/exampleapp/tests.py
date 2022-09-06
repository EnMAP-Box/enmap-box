# -*- coding: utf-8 -*-

"""
***************************************************************************
    exampleapp/tests.py

    Some unit tests to check exampleapp components
    ---------------------
    Date                 : Juli 2017
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

from unittest import TestCase
import pathlib
import site

site.addsitedir(pathlib.Path(__file__).parents[1])


class TestExampleEnMAPBoxApp(TestCase):
    @classmethod
    def setUpClass(cls):
        from enmapbox.testing import start_app
        cls.qgsApp = start_app()

    @classmethod
    def tearDownClass(cls):

        cls.qgsApp.quit()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_algorithms(self):
        from exampleapp.algorithms import dummyAlgorithm

        args = (1, 2, 3)
        kwds = {'key1': 1, 'key2': 2}
        printout = dummyAlgorithm(*args, **kwds)
        self.assertIsInstance(printout, str)
        self.assertTrue(len(printout) > 0)

        for i, a in enumerate(args):
            self.assertTrue('Argument {} = {}'.format(i + 1, a) in printout)
        for key, value in kwds.items():
            self.assertTrue('Keyword {} = {}'.format(key, value) in printout)

    def test_dialog(self):

        from exampleapp.userinterfaces import ExampleGUI
        from qgis.PyQt.QtCore import QCoreApplication

        g = ExampleGUI()
        g.show()
        QCoreApplication.processEvents()

        params = g.collectParameters()
        self.assertIsInstance(params, dict)

        requiredKeys = ['parameter1', 'parameter2']
        for key in requiredKeys:
            self.assertTrue(key in params.keys())

        # change a GUI element
        g.comboBoxParameter1.setCurrentIndex(1)

        # ensure that changes are applied before we continue testing
        QCoreApplication.processEvents()

        # test how the change influenced the returning arguments
        params = g.collectParameters()
        self.assertTrue(params['parameter1'] == 'Value 2')


if __name__ == "__main__":
    import unittest

    unittest.main()
