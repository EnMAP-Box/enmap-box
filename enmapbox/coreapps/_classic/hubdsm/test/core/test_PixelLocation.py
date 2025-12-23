from unittest import TestCase

from _classic.hubdsm.core.pixellocation import PixelLocation


class TestPixelLocation(TestCase):

    def test(self):
        self.assertEqual(PixelLocation(x=0.1, y=0.1).upperLeft, PixelLocation(x=0, y=0))
        self.assertEqual(PixelLocation(x=0.1, y=0.9).upperLeft, PixelLocation(x=0, y=0))
        self.assertEqual(PixelLocation(x=0.9, y=0.1).upperLeft, PixelLocation(x=0, y=0))
        self.assertEqual(PixelLocation(x=0.9, y=0.9).upperLeft, PixelLocation(x=0, y=0))
        self.assertEqual(PixelLocation(x=0.5, y=0.5).upperLeft, PixelLocation(x=0, y=0))

        self.assertEqual(PixelLocation(x=0.1, y=0.1).lowerRight, PixelLocation(x=1, y=1))
        self.assertEqual(PixelLocation(x=0.1, y=0.9).lowerRight, PixelLocation(x=1, y=1))
        self.assertEqual(PixelLocation(x=0.9, y=0.1).lowerRight, PixelLocation(x=1, y=1))
        self.assertEqual(PixelLocation(x=0.9, y=0.9).lowerRight, PixelLocation(x=1, y=1))
        self.assertEqual(PixelLocation(x=0.5, y=0.5).lowerRight, PixelLocation(x=1, y=1))

        self.assertEqual(PixelLocation(x=0.1, y=0.1).center, PixelLocation(x=0.5, y=0.5))
        self.assertEqual(PixelLocation(x=0.1, y=0.9).center, PixelLocation(x=0.5, y=0.5))
        self.assertEqual(PixelLocation(x=0.9, y=0.1).center, PixelLocation(x=0.5, y=0.5))
        self.assertEqual(PixelLocation(x=0.9, y=0.9).center, PixelLocation(x=0.5, y=0.5))
        self.assertEqual(PixelLocation(x=0.5, y=0.5).center, PixelLocation(x=0.5, y=0.5))

        self.assertEqual(PixelLocation(x=0.1, y=0.1).round, PixelLocation(x=0, y=0))
        self.assertEqual(PixelLocation(x=0.1, y=0.9).round, PixelLocation(x=0, y=1))
        self.assertEqual(PixelLocation(x=0.9, y=0.1).round, PixelLocation(x=1, y=0))
        self.assertEqual(PixelLocation(x=0.9, y=0.9).round, PixelLocation(x=1, y=1))
