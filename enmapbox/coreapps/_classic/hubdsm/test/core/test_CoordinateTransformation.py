from unittest.case import TestCase

from _classic.hubdsm.core.coordinatetransformation import CoordinateTransformation
from _classic.hubdsm.core.geometry import Geometry
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.projection import Projection


class TestCoordinateTransformation(TestCase):

    def test(self):
        coordinateTransformationForward = CoordinateTransformation(
            source=Projection.fromEpsg(32632), target=Projection.fromEpsg(32633)
        )
        coordinateTransformationBackward = CoordinateTransformation(
            source=Projection.fromEpsg(32633), target=Projection.fromEpsg(32632)
        )
        g1 = Geometry.fromLocation(location=Location(x=0, y=0))
        g2 = g1.reproject(coordinateTransformation=coordinateTransformationForward)
        g3 = g2.reproject(coordinateTransformation=coordinateTransformationBackward)
        self.assertTrue(g1.locations[0].equal(other=g3.locations[0], tol=1e-6))
