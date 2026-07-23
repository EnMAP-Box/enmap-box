from unittest import TestCase

from _classic.hubdsm.core.shape import GridShape, RasterShape


class TestGridShape(TestCase):

    def test(self):
        shape = GridShape(y=10, x=20)
        self.assertEqual(shape.withY(y=20), GridShape(y=20, x=20))
        self.assertEqual(shape.withX(x=10), GridShape(y=10, x=10))
        self.assertEqual(shape.withZ(z=30), RasterShape(z=30, y=10, x=20))

class TestRasterShape(TestCase):

    def test(self):
        shape = RasterShape(z=30, y=10, x=20)
        self.assertEqual(shape.withZ(z=50), RasterShape(z=50, y=10, x=20))
        self.assertEqual(shape.gridShape, GridShape(y=10, x=20))
