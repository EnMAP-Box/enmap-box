# -*- coding: utf-8 -*-

"""
***************************************************************************
    examples/minimumexample/tests.py

    Unit tests to check the minimum example
    ---------------------
    Date                 : January 2019
    Copyright            : (C) 2019 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from unittest import TestCase

from enmapbox import EnMAPBoxApplication
from enmapbox.testing import initQgisApplication
from minimumexample.exampleapp import exampleAlgorithm, ExampleProcessingAlgorithm, ExampleApplicationGUI, \
    ExampleApplication
from qgis.core import QgsProcessingAlgorithm, QgsProcessingContext, QgsProcessingFeedback, QgsProcessingProvider

# initialize the QGIS API + several background states
APP = initQgisApplication()

# set on True to show widgets and wait until a user closes them.
SHOW_GUI = True


class TestExampleEnMAPBoxApp(TestCase):

    def test_algorithms(self):
        """
        Test your core algorithms, which might not require any GUI or QGIS.
        """

        args, kwds = exampleAlgorithm()

        self.assertEqual(args, ())
        self.assertEqual(kwds, dict())

        args, kwds = exampleAlgorithm(42, foo='bar')
        self.assertEqual(args[0], 42)
        self.assertEqual(kwds['foo'], 'bar')

    def test_processingAlgorithms(self):

        alg = ExampleProcessingAlgorithm()
        self.assertIsInstance(alg, QgsProcessingAlgorithm)

        alg2 = alg.createInstance()
        self.assertIsInstance(alg2, QgsProcessingAlgorithm)

        outputs = alg.processAlgorithm({'foo': 'bar'}, QgsProcessingContext(), QgsProcessingFeedback())
        self.assertIsInstance(outputs, dict)
        self.assertTrue(outputs['args'] == ({'foo': 'bar'},))

    def test_dialog(self):
        """
        Test your GUI components, without any EnMAP-Box
        """
        g = ExampleApplicationGUI()
        g.show()

        self.assertIsInstance(g.numberOfClicks(), int)
        self.assertEqual(g.numberOfClicks(), 0)

        # click the button programmatically
        g.btn.click()
        self.assertEqual(g.numberOfClicks(), 1)

        if SHOW_GUI:
            APP.exec_()

    def test_with_EnMAPBox(self):
        """
        Finally, test if your application can be added into the EnMAP-Box
        """
        from enmapbox import EnMAPBox
        enmapBox = EnMAPBox(None)
        self.assertIsInstance(enmapBox, EnMAPBox)

        myApp = ExampleApplication(enmapBox)
        self.assertIsInstance(myApp, EnMAPBoxApplication)
        enmapBox.addApplication(myApp)

        provider = enmapBox.processingProvider()
        self.assertIsInstance(provider, QgsProcessingProvider)
        algorithmNames = [a.name() for a in provider.algorithms()]
        for name in ['examplealgorithm', 'examplealgorithmwithmanywidgets']:
            self.assertTrue(name in algorithmNames)

        if SHOW_GUI:
            APP.exec_()


if __name__ == "__main__":
    import unittest

    SHOW_GUI = False
    unittest.main()
