from osgeo import gdal

from tests.enmapboxtestdata import SensorProducts

qaFile = SensorProducts.Landsat.LC09_L2_MtlTxt.replace('MTL.txt', 'QA_PIXEL.TIF')
qaFileCopy = SensorProducts.Landsat.LC09_L2_MtlTxt.replace('MTL.txt', 'QA_PIXEL.vrt')

# STAC taken from GEE
bitmask_parts = [
    {
        "bit_count": 1,
        "description": "Fill",
        "first_bit": 0
    },
    {
        "bit_count": 1,
        "description": "Dilated Cloud",
        "first_bit": 1
    },
    {
        "bit_count": 1,
        "description": "Cirrus (high confidence)",
        "first_bit": 2
    },
    {
        "bit_count": 1,
        "description": "Cloud",
        "first_bit": 3
    },
    {
        "bit_count": 1,
        "description": "Cloud Shadow",
        "first_bit": 4
    },
    {
        "bit_count": 1,
        "description": "Snow",
        "first_bit": 5
    },
    {
        "bit_count": 1,
        "description": "Clear",
        "first_bit": 6,
        "values": [
            {
                "description": "Cloud or Dilated Cloud bits are set",
                "value": 0
            },
            {
                "description": "Cloud and Dilated Cloud bits are not set",
                "value": 1
            }
        ]
    },
    {
        "bit_count": 1,
        "description": "Water",
        "first_bit": 7
    },
    {
        "bit_count": 2,
        "description": "Cloud Confidence",
        "first_bit": 8,
        "values": [
            {
                "description": "None",
                "value": 0
            },
            {
                "description": "Low",
                "value": 1
            },
            {
                "description": "Medium",
                "value": 2
            },
            {
                "description": "High",
                "value": 3
            }
        ]
    },
    {
        "bit_count": 2,
        "description": "Cloud Shadow Confidence",
        "first_bit": 10,
        "values": [
            {
                "description": "None",
                "value": 0
            },
            {
                "description": "Low",
                "value": 1
            },
            {
                "description": "Medium",
                "value": 2
            },
            {
                "description": "High",
                "value": 3
            }
        ]
    },
    {
        "bit_count": 2,
        "description": "Snow/Ice Confidence",
        "first_bit": 12,
        "values": [
            {
                "description": "None",
                "value": 0
            },
            {
                "description": "Low",
                "value": 1
            },
            {
                "description": "Medium",
                "value": 2
            },
            {
                "description": "High",
                "value": 3
            }
        ]
    },
    {
        "bit_count": 2,
        "description": "Cirrus Confidence",
        "first_bit": 14,
        "values": [
            {
                "description": "None",
                "value": 0
            },
            {
                "description": "Low",
                "value": 1
            },
            {
                "description": "Medium",
                "value": 2
            },
            {
                "description": "High",
                "value": 3
            }
        ]
    }
]

ds: gdal.Dataset = gdal.Translate(qaFileCopy, qaFile)
rb: gdal.Band = ds.GetRasterBand(1)
rb.SetMetadataItem('bitmask_parts', str(bitmask_parts), 'STAC')
bitmask_parts2 = eval(rb.GetMetadataItem('bitmask_parts', 'STAC'))
assert bitmask_parts == bitmask_parts2
