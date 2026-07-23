from unittest.case import TestCase

from _classic.hubdsm.core.color import Color


class TestColor(TestCase):

    def test(self):
        Color.fromRandom()
