from unittest.case import TestCase

import numpy as np

from _classic.hubdsm.core.extent import Extent
from _classic.hubdsm.core.geotransform import GeoTransform
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.pixellocation import PixelLocation
from _classic.hubdsm.core.projection import Projection, WGS84_PROJECTION
from _classic.hubdsm.core.resolution import Resolution
from _classic.hubdsm.core.shape import GridShape
from _classic.hubdsm.core.size import Size


class TestGrid(TestCase):

    def test(self):
        grid = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=10, y=20)),
            resolution=Resolution(x=1, y=2),
            projection=WGS84_PROJECTION
        )
        self.assertEqual(grid.withResolution(resolution=Resolution(2, 2)).resolution, Resolution(2, 2))
        self.assertEqual(grid.shape, GridShape(y=10, x=10))
        self.assertEqual(grid.geoTransform, GeoTransform(ul=Location(x=0, y=0), resolution=Resolution(x=1, y=2)))
        gridCopy = Grid.fromGeoTransform(geoTransform=grid.geoTransform, shape=grid.shape, projection=grid.projection)
        self.assertTrue(grid.equal(other=gridCopy))

    def test_pseudoGrid(self):
        grid = Grid.makePseudoGridFromShape(shape=GridShape(y=3600, x=3600))
        gold = Grid(extent=Extent(ul=Location(x=0, y=1.0), size=Size(x=1.0, y=1.0)),
            resolution=Resolution(x=0.0002777777777777778, y=0.0002777777777777778), projection=Projection(
                wkt='GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST],AUTHORITY["EPSG","4326"]]'))
        self.assertTrue(grid.equal(other=gold))

    def test_pixelLocation(self):
        grid = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=10, y=20)),
            resolution=Resolution(x=1, y=1),
            projection=WGS84_PROJECTION
        )
        self.assertTrue(grid.pixelLocation(location=grid.extent.ul), PixelLocation(x=0.0, y=0.0))
        self.assertTrue(grid.pixelLocation(location=grid.extent.lr), PixelLocation(x=10.0, y=20.0))

    def test_location(self):
        grid = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=10, y=20)),
            resolution=Resolution(x=1, y=1),
            projection=WGS84_PROJECTION
        )
        self.assertTrue(grid.location(pixelLocation=PixelLocation(x=0.0, y=0.0)), grid.extent.ul)
        self.assertTrue(grid.location(pixelLocation=PixelLocation(x=10.0, y=20.0)), grid.extent.lr)

    def test_equal(self):
        grid = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=10, y=20)),
            resolution=Resolution(x=1, y=1),
            projection=WGS84_PROJECTION
        )
        self.assertFalse(grid.equal(grid.withExtent(extent=Extent(ul=Location(x=0, y=0), size=Size(x=1, y=1)))))
        self.assertFalse(grid.equal(grid.withResolution(resolution=Resolution(2, 2))))
        self.assertFalse(grid.equal(grid.withProjection(projection=Projection.fromEpsg(32633))))

    def test_coordinates(self):
        grid = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=10, y=6)),
            resolution=Resolution(x=2, y=2),
            projection=WGS84_PROJECTION
        )

        # test full grid
        self.assertListEqual(grid.xPixelCoordinates(), [0, 1, 2, 3, 4])
        self.assertListEqual(grid.yPixelCoordinates(), [0, 1, 2])
        self.assertListEqual(grid.xMapCoordinates(), [1.0, 3.0, 5.0, 7.0, 9.0])
        self.assertListEqual(grid.yMapCoordinates(), [-1.0, -3.0, -5.0])
        self.assertTrue(np.all(np.equal(
            grid.xPixelCoordinatesArray(),
            [[0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [0, 1, 2, 3, 4]]
        )))
        self.assertTrue(np.all(np.equal(
            grid.yPixelCoordinatesArray(),
            [[0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2]]
        )))
        self.assertTrue(np.all(np.equal(
            grid.xMapCoordinatesArray(),
            [[1.0, 3.0, 5.0, 7.0, 9.0], [1.0, 3.0, 5.0, 7.0, 9.0], [1.0, 3.0, 5.0, 7.0, 9.0]]
        )))
        self.assertTrue(np.all(np.equal(
            grid.yMapCoordinatesArray(),
            [[-1.0, -1.0, -1.0, -1.0, -1.0], [-3.0, -3.0, -3.0, -3.0, -3.0], [-5.0, -5.0, -5.0, -5.0, -5.0]]
        )))

        # test subgrid
        subgrid = grid.subgrid(offset=PixelLocation(x=2, y=1), shape=GridShape(x=2, y=2))
        self.assertListEqual(subgrid.xPixelCoordinates(grid=grid), [2, 3])
        self.assertListEqual(subgrid.yPixelCoordinates(grid=grid), [1, 2])
        self.assertListEqual(subgrid.xMapCoordinates(), [5.0, 7.0])
        self.assertListEqual(subgrid.yMapCoordinates(), [-3.0, -5.0])


    def test_subgrids(self):
        grid = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=5, y=4)),
            resolution=Resolution(x=1, y=1),
            projection=WGS84_PROJECTION
        )
        leads = [g.extent for g in grid.subgrids(shape=GridShape(y=2, x=2))]
        golds = [
            Extent(ul=Location(x=0.0, y=0.0), size=Size(x=2.0, y=2.0)),
            Extent(ul=Location(x=2.0, y=0.0), size=Size(x=2.0, y=2.0)),
            Extent(ul=Location(x=4.0, y=0.0), size=Size(x=1.0, y=2.0)),
            Extent(ul=Location(x=0.0, y=-2.0), size=Size(x=2.0, y=2.0)),
            Extent(ul=Location(x=2.0, y=-2.0), size=Size(x=2.0, y=2.0)),
            Extent(ul=Location(x=4.0, y=-2.0), size=Size(x=1.0, y=2.0))
        ]
        for gold, lead in zip(golds, leads):
            self.assertTrue(gold.equal(other=lead))
