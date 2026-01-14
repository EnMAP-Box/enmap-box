from os import listdir
from os.path import join, splitext, dirname, basename, exists
from collections import OrderedDict
from typing import NamedTuple
import copy
import fnmatch
import numpy as np
import datetime
import _classic.hubflow.core as hfc



class RasterOutOfBoundsError(Exception):
    pass




