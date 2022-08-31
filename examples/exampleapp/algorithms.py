# -*- coding: utf-8 -*-

"""
***************************************************************************
    exampleapp/algorithms.py

    Some example algorithms, as they might be implemented somewhere else
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


def dummyAlgorithm(*args, **kwds):
    """
    A dummy algorithm that prints its parametrisation and returns this print out.
    :param args: any argument tuple
    :param kwds: any keyword dictionary
    :return: print-out-string
    """
    info = ['Dummy Algorithm started']

    if len(args) > 0:
        info.append('Print arguments:')
        for i, arg in enumerate(args):
            info.append('Argument {} = {}'.format(i + 1, str(arg)))
    else:
        info.append('No arguments defined')
    if len(kwds) > 0:
        info.append('Print keywords:')
        for k, v in kwds.items():
            info.append('Keyword {} = {}'.format(k, str(v)))
    else:
        info.append('No keywords defined')
    info.append('Dummy Algorithm finished')
    print(info)
    return '\n'.join(info)


### Interfaces to use algorithms in algorithms.py within
### QGIS Processing Framework

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterRaster
from processing.core.outputs import OutputRaster


class MyEnMAPBoxAppProcessingAlgorithm(GeoAlgorithm):

    def defineCharacteristics(self):
        self.name = 'Example Algorithm'
        self.group = 'My Example App'

        self.addParameter(ParameterRaster('infile', 'Example Input Image'))
        self.addOutput(OutputRaster('outfile', 'Example Output Image'))

    def processAlgorithm(self, progress):
        # map processing framework parameters to that of you algorithm
        infile = self.getParameterValue('infile')
        outfile = self.getOutputValue('outfile')

        # run your algorithm here

        dummyAlgorithm(infile, outfile)

    def help(self):
        return True, 'Shows how to implement an GeoAlgorithm'
