import os.path
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.importsentinel2l2aalgorithm import ImportSentinel2L2AAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import sensorProductsRoot, SensorProducts

product_root = sensorProductsRoot()
skip_tests = not (isinstance(product_root, str) and os.path.isdir(product_root))


class TestImportSentinel2L2AAlgorithm(TestCase):

    @unittest.skipIf(skip_tests,
                     'Sensor test data is missing. Use ENMAPBOX_SENSOR_PRODUCT_ROOT to define its location.')
    def test(self):
        alg = ImportSentinel2L2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Sentinel2.S2B_L2A_MsiL2AXml,
            alg.P_OUTPUT_RASTER: self.filename('sentinel2L2A.vrt'),
        }
        self.runalg(alg, parameters)

    @unittest.skipIf(skip_tests,
                     'Sensor test data is missing. Use ENMAPBOX_SENSOR_PRODUCT_ROOT to define its location.')
    def test_import_l2a_with_offset(self):

        # check if offsets are correctly applied according
        # to https://sentiwiki.copernicus.eu/web/s2-products
        # "starting with the Processing Baseline (PB) 04.00 (25th January 2022),
        # the dynamic range of the Level-2A products is shifted by a band-dependent constant".

        p1 = SensorProducts.Sentinel2.S2B_L2A_N0214_XML
        p2 = SensorProducts.Sentinel2.S2B_L2A_N0500_ZIP
        ds1: gdal.Dataset = gdal.Open(p1)
        ds_box: gdal.Dataset = gdal.Open(p2)

        xml1 = ds1.GetMetadata_Dict('xml:SENTINEL2')
        xml2 = ds_box.GetMetadata_Dict('xml:SENTINEL2')

        xml1 = ET.fromstring('<?xml version=' + xml1['<?xml version'])
        xml2 = ET.fromstring('<?xml version=' + xml2['<?xml version'])

        # Sentinel-2 L2A namespace
        # ns = {'n1': 'https://psd-14.sentinel2.eo.esa.int/PSD/User_Product_Level-2A.xsd'}
        # Use XPath with namespace prefix
        bl1 = xml1.find('.//PROCESSING_BASELINE').text
        bl2 = xml2.find('.//PROCESSING_BASELINE').text

        # ensure that we have the right test data
        self.assertTrue(bl1 < '04.00')
        self.assertTrue(bl2 > '04.00')

        def get_xml(ds: gdal.Dataset) -> str:
            d = ds.GetMetadata_Dict('xml:SENTINEL2')
            return '<?xml version=' + d['<?xml version']

        alg = ImportSentinel2L2AAlgorithm()

        for p in [p1, p2]:
            self.assertTrue(os.path.exists(str(p)))
            ds = gdal.Open(str(p))
            xml_string = get_xml(ds)
            xml = ET.fromstring(xml_string)
            baseline = xml.find('.//PROCESSING_BASELINE').text

            BAND_INFO_XML = {}

            band_offsets = {e.attrib['band_id']: float(e.text) for e in xml.findall('.//BOA_ADD_OFFSET')}
            boa_quantification_value = float(xml.find('.//BOA_QUANTIFICATION_VALUE').text)

            for e in xml.findall('.//Spectral_Information'):
                bid = e.attrib['bandId']
                physicalBand = e.attrib['physicalBand']
                offset = float(band_offsets.get(bid, 0))
                scale = boa_quantification_value
                info = {'bandId': bid,
                        'physicalBand': physicalBand,
                        'wl_min': float(e.find('Wavelength/MIN').text),
                        'wl_max': float(e.find('Wavelength/MAX').text),
                        'wl_center': float(e.find('Wavelength/CENTRAL').text),
                        'wlu': e.find('Wavelength/CENTRAL').attrib['unit'],
                        'scale': scale,
                        'offset': offset,
                        }

                BAND_INFO_XML[bid] = info
                BAND_INFO_XML[physicalBand] = info

            for path_sub, name_sub in ds.GetSubDatasets():
                if not name_sub.startswith('Bands'):
                    continue
                ds_sub = gdal.Open(path_sub)
                SUB_BANDINFO = {}
                alg_band_list = []
                for b in range(ds_sub.RasterCount):
                    n_gdal = ds_sub.GetRasterBand(b + 1).GetDescription()
                    prefix = n_gdal.split(',')[0]
                    SUB_BANDINFO[prefix] = b

                    # collect the bands that can be imported into EnMAP-Box
                    for j, n_box in enumerate(alg.O_BAND_LIST):
                        if n_box.startswith(prefix + ','):
                            alg_band_list.append(j)
                            break

                p_result = self.filename(f's2_l2a_baseline{baseline}.vrt')
                parameters = {
                    alg.P_FILE: str(p),
                    alg.P_BAND_LIST: alg_band_list,
                    alg.P_OUTPUT_RASTER: p_result,
                }

                results = self.runalg(alg, parameters)
                ds_box: gdal.Dataset = gdal.Open(p_result)
                px_x, px_y = int(0.5 * ds_sub.RasterXSize), int(0.5 * ds_sub.RasterYSize)
                profile_sub = ds_sub.ReadAsArray(px_x, px_y, 1, 1).flatten()
                profile_box = ds_box.ReadAsArray(px_x, px_y, 1, 1).flatten()

                sub_bands = []
                box_names = []
                for b in range(ds_box.RasterCount):
                    band: gdal.Band = ds_box.GetRasterBand(b + 1)
                    name = band.GetDescription()
                    prefix = name.split(',')[0]
                    assert prefix in SUB_BANDINFO, f'Band {name} not found in sub-dataset {path_sub}'

                    band_info = BAND_INFO_XML[prefix]

                    box_names.append(name)
                    b_sub = SUB_BANDINFO[prefix]
                    sub_bands.append(b_sub)

                    wl_um = float(band.GetMetadataItem('CENTRAL_WAVELENGTH_UM', 'IMAGERY'))
                    wl_nm = wl_um * 1000
                    self.assertAlmostEqual(wl_nm, band_info['wl_center'], places=2)

                profile_sub = profile_sub[sub_bands]
                self.assertTrue(np.array_equal(profile_sub, profile_box))

    @unittest.skipIf(skip_tests,
                     'Sensor test data is missing. Use ENMAPBOX_SENSOR_PRODUCT_ROOT to define its location.')
    def test_gdal_reader(self):

        p1 = Path(SensorProducts.Sentinel2.S2A_L2A) / 'MTD_MSIL2A.xml'
        p2 = Path(SensorProducts.Sentinel2.S2B_L2A) / 'MTD_MSIL2A.xml'

        for p in [p1, p2]:
            self.assertTrue(p.is_file())

        def get_baseline(xml_input):
            if isinstance(xml_input, (str, Path)) and str(xml_input).startswith('<?xml'):
                root = ET.fromstring(xml_input)
            else:
                tree = ET.parse(xml_input)
                root = tree.getroot()
            # The PROCESSING_BASELINE might be in a namespace
            # Let's try to find it regardless of namespace
            for elem in root.iter():
                if elem.tag.endswith('PROCESSING_BASELINE'):
                    return elem.text
            return None

        pb1 = get_baseline(p1)
        pb2 = get_baseline(p2)
        self.assertTrue(pb1 < '04.00')
        self.assertTrue(pb2 > '04.00')

        ds1 = gdal.Open(str(p1))
        sub1 = [p for p, _ in ds1.GetSubDatasets() if ':10m:' in p][0]
        ds1: gdal.Dataset = gdal.Open(sub1)
        ds2 = gdal.Open(str(p2))
        sub2 = [p for p, _ in ds2.GetSubDatasets() if ':10m:' in p][0]
        ds2: gdal.Dataset = gdal.Open(sub2)

        b1_1: gdal.Band = ds1.GetRasterBand(1)
        b1_2: gdal.Band = ds2.GetRasterBand(1)
        s = ""

    @unittest.skipIf(skip_tests,
                     'Sensor test data is missing. Use ENMAPBOX_SENSOR_PRODUCT_ROOT to define its location.')
    def test_saveAsTif(self):
        alg = ImportSentinel2L2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Sentinel2.S2B_L2A_MsiL2AXml,
            alg.P_OUTPUT_RASTER: self.filename('sentinel2L2A.tif'),
        }
        self.runalg(alg, parameters)

    @unittest.skipIf(skip_tests,
                     'Sensor test data is missing. Use ENMAPBOX_SENSOR_PRODUCT_ROOT to define its location.')
    def test_zip(self):
        alg = ImportSentinel2L2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Sentinel2.S2B_L2A_N0500_ZIP,
            alg.P_OUTPUT_RASTER: self.filename('sentinel2L2A.vrt'),
        }
        self.runalg(alg, parameters)
