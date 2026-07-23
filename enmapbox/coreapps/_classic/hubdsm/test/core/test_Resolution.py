from unittest import TestCase

from _classic.hubdsm.core.resolution import Resolution


class TestResolution(TestCase):
    def test_equal(self):
        resolution = Resolution(x=10, y=20)
        self.assertTrue(resolution.equal(other=Resolution(x=10, y=20)))
