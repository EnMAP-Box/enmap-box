from unittest import TestCase

from osgeo import gdal

from _classic.hubdsm.algorithm.importenmapl1b import importEnmapL1B, isEnmapL1BProduct


class TestImportEnmapL1B(TestCase):

    def test_isEnmapL1BProduct(self):
        filenameMetadataXml = r'C:\Users\janzandr\Downloads\L1B_Alps_1\ENMAP01-____L1B-DT000326721_20170626T102020Z_001_V000204_20200406T154119Z-METADATA.XML'
        self.assertTrue(isEnmapL1BProduct(filenameMetadataXml=filenameMetadataXml))
        self.assertFalse(isEnmapL1BProduct(filenameMetadataXml=''))

    def test(self):
        dsVnir, dsSwir = importEnmapL1B(
            filenameMetadataXml=r'C:\Users\janzandr\Downloads\L1B_Alps_1\ENMAP01-____L1B-DT000326721_20170626T102020Z_001_V000204_20200406T154119Z-METADATA.XML')

        assert dsVnir.GetGeoTransform()[-1] == -1.0
        assert dsSwir.GetGeoTransform()[-1] == -1.0

        self.assertEqual(
            dsVnir.GetMetadataItem('wavelength', 'ENVI'),
            '{423.03, 428.8, 434.29, 439.58, 444.72, 449.75, 454.7, 459.59, 464.43, 469.25, 474.05, 478.84, 483.63, 488.42, 493.23, 498.05, 502.9, 507.77, 512.67, 517.6, 522.57, 527.58, 532.63, 537.72, 542.87, 548.06, 553.3, 558.6, 563.95, 569.36, 574.83, 580.36, 585.95, 591.6, 597.32, 603.1, 608.95, 614.86, 620.84, 626.9, 633.02, 639.21, 645.47, 651.8, 658.2, 664.67, 671.21, 677.83, 684.51, 691.26, 698.08, 704.97, 711.92, 718.95, 726.03, 733.19, 740.4, 747.68, 755.01, 762.41, 769.86, 777.37, 784.93, 792.54, 800.2, 807.91, 815.67, 823.46, 831.3, 839.18, 847.1, 855.05, 863.03, 871.05, 879.09, 887.16, 895.25, 903.36, 911.49, 919.64, 927.8, 935.98, 944.17, 952.37, 960.57, 968.78, 976.99, 985.21}'
        )
        self.assertEqual(
            dsSwir.GetMetadataItem('wavelength', 'ENVI'),
            '{904.78, 914.44, 924.23, 934.16, 944.23, 954.42, 964.74, 975.17, 985.73, 996.4, 1007.2, 1018.1, 1029.1, 1040.2, 1051.3, 1062.6, 1074.0, 1085.4, 1096.9, 1108.5, 1120.1, 1131.8, 1143.5, 1155.3, 1167.1, 1179.0, 1190.9, 1202.8, 1214.8, 1226.7, 1238.7, 1250.7, 1262.7, 1274.7, 1286.7, 1298.7, 1310.7, 1322.7, 1334.7, 1346.6, 1358.5, 1370.4, 1382.3, 1487.8, 1499.4, 1510.9, 1522.3, 1533.7, 1545.1, 1556.4, 1567.7, 1578.9, 1590.1, 1601.2, 1612.3, 1623.3, 1634.3, 1645.3, 1656.2, 1667.0, 1677.8, 1688.5, 1699.2, 1709.9, 1720.5, 1731.0, 1741.5, 1752.0, 1762.4, 1772.7, 1941.5, 1951.0, 1960.5, 1969.9, 1979.3, 1988.7, 1998.0, 2007.2, 2016.4, 2025.6, 2034.8, 2043.9, 2052.9, 2061.9, 2070.9, 2079.9, 2088.8, 2097.6, 2106.4, 2115.2, 2124.0, 2132.7, 2141.3, 2150.0, 2158.6, 2167.1, 2175.7, 2184.2, 2192.6, 2201.0, 2209.4, 2217.8, 2226.1, 2234.4, 2242.6, 2250.8, 2259.0, 2267.2, 2275.3, 2283.4, 2291.4, 2299.4, 2307.4, 2315.4, 2323.3, 2331.2, 2339.1, 2346.9, 2354.7, 2362.5, 2370.2, 2377.9, 2385.6, 2393.3, 2400.9, 2408.5, 2416.1, 2423.6, 2431.1, 2438.6}'
        )

        profile = list(dsVnir.ReadAsArray(0, 0, 1, 1).flatten())
        profileScaled = [round(v * dsVnir.GetRasterBand(i + 1).GetScale() + dsVnir.GetRasterBand(i + 1).GetOffset(), 4)
                         for i, v in enumerate(profile)]
        self.assertListEqual(
            profile,

            [4817, 4946, 4593, 4631, 4694, 4475, 4439, 4241, 4158, 4215, 4080, 4127, 4119, 3997, 3930, 3792, 3875, 4018,
             4200, 4352, 4181, 4701, 4683, 4991, 4929, 4913, 4948, 5007, 4746, 4750, 4661, 4628, 4572, 4369, 4353, 4357,
             4310, 4237, 4107, 4017, 3951, 3861, 3730, 3631, 3538, 3465, 3513, 3759, 4362, 5613, 6785, 8143, 9436,
             10889, 12666, 14023, 15513, 16553, 17376, 18529, 19100, 19283, 19594, 20074, 20140, 20359, 20820, 21038,
             21145, 21455, 22012, 22040, 21867, 22212, 22306, 22609, 22952, 22844, 22897, 22865, 23390, 23824, 24216,
             23128, 23189, 23206, 23392, 23142]
        )
        self.assertListEqual(
            profileScaled,
            [0.0593, 0.0544, 0.0515, 0.0552, 0.0573, 0.0593, 0.0593, 0.0577, 0.0571, 0.0564, 0.055, 0.0543, 0.0522,
             0.048, 0.0484, 0.0475, 0.045, 0.0457, 0.0454, 0.0432, 0.0432, 0.0456, 0.0454, 0.0459, 0.0446, 0.0448,
             0.0445, 0.043, 0.0411, 0.0404, 0.0393, 0.0395, 0.0384, 0.0352, 0.0358, 0.0362, 0.0355, 0.0345, 0.0333,
             0.0321, 0.0317, 0.0315, 0.0301, 0.0287, 0.0282, 0.0285, 0.0288, 0.0301, 0.0314, 0.0352, 0.0429, 0.0511,
             0.0579, 0.0558, 0.0616, 0.0755, 0.0922, 0.1014, 0.0979, 0.0677, 0.099, 0.1112, 0.1095, 0.106, 0.1037,
             0.1002, 0.0837, 0.0823, 0.0883, 0.0969, 0.1003, 0.0973, 0.0966, 0.0966, 0.0956, 0.0931, 0.0772, 0.0663,
             0.0598, 0.0623, 0.048, 0.0209, 0.0232, 0.0251, 0.0343, 0.0513, 0.0577, 0.0672]
        )
