from unittest.case import TestCase

from _classic.hubdsm.core.coordinatetransformation import CoordinateTransformation
from _classic.hubdsm.core.extent import Extent
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.projection import Projection
from _classic.hubdsm.core.size import Size


class TestExtent(TestCase):

    def test_reproject(self):
        coordinateTransformationForward = CoordinateTransformation(
            source=Projection.fromEpsg(32632), target=Projection.fromEpsg(32633)
        )
        coordinateTransformationBackward = CoordinateTransformation(
            source=Projection.fromEpsg(32633), target=Projection.fromEpsg(32632)
        )
        e1 = Extent(ul=Location(x=0, y=0), size=Size(x=10, y=20))
        e2 = e1.reproject(coordinateTransformation=coordinateTransformationForward)
        e3 = e2.reproject(coordinateTransformation=coordinateTransformationBackward)
        self.assertTrue(e1.equal(other=e3))

    def test_union(self):
        e1 = Extent(ul=Location(x=0, y=0), size=Size(x=10, y=10))
        e2 = Extent(ul=Location(x=10, y=-10), size=Size(x=10, y=10))
        e3 = e1.union(other=e2)
        self.assertTrue(e3.equal(other=Extent(ul=Location(0, 0), size=Size(20, 20))))

    def test_within(self):
        e1 = Extent(ul=Location(x=0, y=0), size=Size(x=20, y=20))
        e2 = Extent(ul=Location(x=10, y=-10), size=Size(x=5, y=5))
        self.assertTrue(e2.within(other=e1))

    def test_intersection(self):
        e1 = Extent(ul=Location(x=0, y=0), size=Size(x=20, y=20))
        e2 = Extent(ul=Location(x=10, y=-10), size=Size(x=20, y=20))
        e3 = e1.intersection(other=e2)
        self.assertTrue(e3.equal(other=Extent(ul=Location(10, -10), size=Size(10, 10))))
