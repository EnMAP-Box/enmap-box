from unittest import TestCase

from _classic.hubdsm.algorithm.processingoptions import ProcessingOptions
from _classic.hubdsm.core.shape import GridShape


class TestProcessingOptions(TestCase):

    def test_getShape(self):
        po = ProcessingOptions()
        gold = GridShape(y=10, x=20)
        lead = po.getShape(default=gold)
        self.assertEqual(gold, lead)

        po = ProcessingOptions(shape=gold)
        lead = po.shape
        self.assertEqual(gold, lead)
