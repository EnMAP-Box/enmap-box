from unittest.case import TestCase

import numpy as np

from _classic.hubdsm.core.coordinatetransformation import CoordinateTransformation
from _classic.hubdsm.core.geometry import Geometry, Envelope
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.projection import Projection
from _classic.hubdsm.core.size import Size


class TestGeometry(TestCase):

    def test(self):
        try:
            Geometry(wkt='Point(1 2)')
        except ValueError:
            pass
        try:
            Geometry.formatWkt(wkt='foobar(1 2)')
        except ValueError:
            pass

        geometry1 = Geometry(wkt='POINT (1 2)')
        self.assertEqual(geometry1.locations, [Location(x=1.0, y=2.0)])

        geometry2 = Geometry(wkt=Geometry.formatWkt('Point(1 2)'))
        geometry3 = Geometry.fromLocation(location=Location(x=1, y=2))
        self.assertTrue(geometry1 == geometry2 == geometry3)

        poly = Geometry.fromPolygonCoordinates(locations=[Location(x=0, y=0), Location(x=1, y=0),Location(x=0.5, y=1)])
        self.assertEqual(poly, Geometry(wkt='POLYGON ((0 0 0,1 0 0,0.5 1.0 0,0 0 0))'))
        self.assertEqual(poly.envelope, Envelope(xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0))
        self.assertEqual(
            poly.locations,
            [Location(x=0.0, y=0.0), Location(x=1.0, y=0.0), Location(x=0.5, y=1.0), Location(x=0.0, y=0.0)]
        )

    def test_collision(self):
        p1 = Geometry.fromPolygonCoordinates(
            locations=[Location(x=0, y=0), Location(x=2, y=0), Location(x=2, y=2), Location(x=0, y=2)]
        )
        p2 = Geometry.fromPolygonCoordinates(
            locations=[Location(x=1, y=1), Location(x=3, y=1), Location(x=3, y=3), Location(x=1, y=3)]
        )
        intersection = Geometry.fromPolygonCoordinates(
            locations=[Location(x=1, y=1), Location(x=2, y=1), Location(x=2, y=2), Location(x=1, y=2)]
        )
        union = Geometry.fromPolygonCoordinates(
            locations=[Location(x=0, y=0), Location(x=3, y=0), Location(x=3, y=3), Location(x=0, y=3)]
        )

        self.assertTrue(p1.intersects(other=p2))
        self.assertEqual(p1.intersection(other=p2).envelope, intersection.envelope)
        self.assertEqual(p1.union(other=p2).envelope, union.envelope)
        self.assertFalse(p1.within(other=p2))
        self.assertTrue(p1.within(other=p1))

    def test_reproject(self):
        p1 = Geometry(wkt='POINT (0 0)')
        coordinateTransformationForward = CoordinateTransformation(
            source=Projection.fromEpsg(32632), target=Projection.fromEpsg(32633)
        )
        coordinateTransformationBackward = CoordinateTransformation(
            source=Projection.fromEpsg(32633), target=Projection.fromEpsg(32632)
        )
        p2 = p1.reproject(coordinateTransformation=coordinateTransformationForward)
        p3 = p2.reproject(coordinateTransformation=coordinateTransformationBackward)
        self.assertTrue(p1.locations[0].equal(other=p3.locations[0], tol=1e-5))

    def test_buffer(self):
        p1 = Geometry(wkt='POINT (0 0)')
        p2 = p1.buffer(distance=1)
        for l in p2.locations:
            self.assertEqual(round((l.x**2 + l.y**2)**0.5, 5), 1)

class TestEnvelope(TestCase):

    def test(self):
        e = Envelope(xmin=0, xmax=1, ymin=10, ymax=15)
        self.assertEqual(e.size, Size(x=1, y=5))
        self.assertEqual(e.ul, Location(x=0, y=15))
        self.assertEqual(e.ur, Location(x=1, y=15))
        self.assertEqual(e.ll, Location(x=0, y=10))
        self.assertEqual(e.lr, Location(x=1, y=10))


