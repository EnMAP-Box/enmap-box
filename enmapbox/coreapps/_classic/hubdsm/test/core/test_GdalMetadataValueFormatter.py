from unittest import TestCase

from _classic.hubdsm.core.gdalmetadatavalueformatter import GdalMetadataValueFormatter


class TestGdalMetadataValueFormatter(TestCase):

    def test(self):
        self.assertEqual(GdalMetadataValueFormatter.stringToValue(string='a', dtype=str), 'a')
        self.assertEqual(GdalMetadataValueFormatter.stringToValue(string='1.5', dtype=str), '1.5')
        self.assertEqual(GdalMetadataValueFormatter.stringToValue(string='1.5', dtype=float), 1.5)
        self.assertEqual(GdalMetadataValueFormatter.stringToValue(string='{a, b}', dtype=str), ['a', 'b'])
        self.assertEqual(GdalMetadataValueFormatter.stringToValue(string='{1.5, 2.5}', dtype=float), [1.5, 2.5])

        self.assertEqual(GdalMetadataValueFormatter.valueToString(value='a'), 'a')
        self.assertEqual(GdalMetadataValueFormatter.valueToString(value='1.5'), '1.5')
        self.assertEqual(GdalMetadataValueFormatter.valueToString(value=1.5), '1.5')
        self.assertEqual(GdalMetadataValueFormatter.valueToString(value=['a', 'b']), '{a, b}')
        self.assertEqual(GdalMetadataValueFormatter.valueToString(value=[1.5, 2.5]), '{1.5, 2.5}')


