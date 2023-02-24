import itertools

import ee


# ------------------------------------------------------------
# functions
# ------------------------------------------------------------
def add_s2_cld_prb(img):
    cld_prb = ee.Image(img.get('s2cloudless')).select('probability').rename('probability')
    b10 = ee.Image(img.get('TOA')).select('B10').rename('B10')
    return img.addBands([cld_prb, b10]).copyProperties(source=img).set('system:time_start',
                                                                       img.get('system:time_start'))


def add_mask_s2_qa(img):
    qa = img.select('QA60')
    cloudBitMask = ee.Number(2).pow(10).int()
    cirrusBitMask = ee.Number(2).pow(11).int()
    mask = (qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0)))
    mask = mask.Not().rename('qa')
    return img.addBands(mask).copyProperties(source=img).set('system:time_start', img.get('system:time_start'))


'''
OLD VERSION, see below
def add_mask_s2_scl(img):
    scl = img.select('SCL')
    mask = (scl.neq(3).And(scl.neq(7)).And(
            scl.neq(8)).And(
            scl.neq(9)).And(
            scl.neq(10)).And(
            scl.neq(11))).rename('scl')
    return img.addBands(mask).copyProperties(source=img).set('system:time_start', img.get('system:time_start'))
'''


def add_mask_s2_scl(img):
    scl = img.select('SCL')
    mask = (scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10)).rename('scl')  # 1 = cloud, 0 = other
    return img.addBands(mask).copyProperties(source=img).set('system:time_start', img.get('system:time_start'))


def add_mask_s2_cdi(cdi=-0.5, cirrus=True, img_scale=1e4):
    def wrap(img):
        img_cdi = ee.Algorithms.Sentinel2.CDI(img)
        cld = img_cdi.lt(cdi)
        if cirrus:
            cir = img.select('B10').gt(0.01 * img_scale)
            cld = cld.add(cir)
        cld = cld.rename("cdi")
        return img.addBands(cld).copyProperties(source=img).set('system:time_start', img.get('system:time_start'))

    return wrap


def add_mask_s2_prb(thresh_cld_prb=25):
    def wrap(img):
        cld_prb = ee.Image(img.select('probability'))
        cld = cld_prb.gt(thresh_cld_prb).rename('prob')
        return img.addBands(cld).copyProperties(source=img).set('system:time_start', img.get('system:time_start'))

    return wrap


def create_mask(l_masks=['qa', 'scl', 'cdi', 'prob'], erode_dilate=True,
                nir_drk_thresh=0.2, cld_prj_dst=5, img_scale=1e4):
    def wrap(img):
        # 1) create combined mask
        masks = ee.Image(img.select(l_masks))
        # create maskname from input bands
        maskname = 'MASK_' + '_'.join(l_masks)

        any_cloud = masks.reduce(
            'max')  # will contain > 0 (cdi can return 2 due to cirrus) if any mask detected cloud, 0 otherwise

        # 2) create shadow mask from combined mask
        # identify water pixels from the SCL band.
        not_water = img.select('SCL').neq(6)

        # identify dark NIR pixels that are not water (initial potential cloud shadow pixels).
        dark_pixels = img.select('B8').lt(nir_drk_thresh * img_scale).multiply(not_water).rename('dark_pixels')

        # determine the direction to project cloud shadow from clouds (assumes UTM projection).
        shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')))

        # Project shadows from clouds for the "maximum distance (km) to search for cloud shadows from cloud edges"
        # first, convert maximum distance from km to pixels based on scale
        cld_prj_dst_px = round((cld_prj_dst * 1000) / 120)
        cld_prj = (any_cloud.directionalDistanceTransform(shadow_azimuth, cld_prj_dst_px)
                   .reproject(**{'crs': img.select(0).projection(), 'scale': 120})
                   .select('distance')
                   .mask()
                   .rename('cld_transform'))
        # identify the intersection of dark pixels with cloud shadow projection.
        shadows = cld_prj.multiply(dark_pixels)

        # combine cloud and shadow mask
        mask = (any_cloud.add(shadows).gt(0))

        # apply erosion + dilation
        if erode_dilate:
            kernel_min = ee.Kernel.circle(radius=2)
            kernel_max = ee.Kernel.circle(radius=5)
            scale = 20
            mask = (mask.focalMin(kernel=kernel_min).focalMax(kernel=kernel_max)
                    .reproject(**{'crs': mask
                               .projection(), 'scale': scale})
                    .rename(maskname))

        return img.addBands(mask) \
            .copyProperties(source=img).set('system:time_start', img.get('system:time_start'))

    return wrap


# ------------------------------------------------------------
# apply
# ------------------------------------------------------------
# read in ImageCollections
s2_toa = ee.ImageCollection("COPERNICUS/S2_HARMONIZED")  # needed for CDI
s2_boa = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
s2_cloud = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')

# Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
collection = ee.ImageCollection(ee.Join.saveFirst('TOA').apply(**{
    'primary': s2_boa,
    'secondary': s2_toa,
    'condition': ee.Filter.equals(**{
        'leftField': 'system:index',
        'rightField': 'system:index'
    })
}))

# Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
collection = ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
    'primary': collection,
    'secondary': s2_cloud,
    'condition': ee.Filter.equals(**{
        'leftField': 'system:index',
        'rightField': 'system:index'
    })
}))

# add cloud prob layer to collection
collection = collection.map(add_s2_cld_prb)

# add different cloud masks to collection
collection = collection.map(add_mask_s2_qa)  # QA
collection = collection.map(add_mask_s2_scl)  # SCL
collection = collection.map(add_mask_s2_cdi(cdi=-0.8))  # CDI
collection = collection.map(add_mask_s2_prb(thresh_cld_prb=25))  # s2cloudless

# retrieve various combinations of masks to add as bands ...
l_masks = ['qa', 'scl', 'cdi', 'prob']
combinations = []
for i in range(1, len(l_masks) + 1):
    ele = [list(x) for x in itertools.combinations(l_masks, i)]
    combinations += ele
# ... and add bands to collection
for c in combinations:
    collection = collection.map(create_mask(l_masks=c, erode_dilate=True,
                                            nir_drk_thresh=0.2, cld_prj_dst=5, img_scale=1e4))

# default colors for bands and spectral indices
bandColors = {
    'B1': '55bbff', 'B2': '#003fbd', 'B3': '#008700', 'B4': '#c50003', 'B5': '#af54ff', 'B6': '#ffaf25',
    'B7': '#b87e1a', 'B8': '#af54ff', 'B8A': '#803ebe', 'B11': '#ffaf25', 'B12': '#b87e1a',
    # vegetation
    'NDVI': '#aaff00', 'EVI': '#007d00', 'ARVI': '#007d00', 'SAVI': '#007d00', 'SARVI': '#007d00', 'NDMI': '#007d00',
    # burn
    'NBR': '#997700',
    # water
    'NDWI': '#0000ff', 'MNDWI': '#0000ff',
    # snow
    'NDSI': '#ffeedd',
    # soil
    'NDTI': '#eebb22',
    # urban
    'NDBI': '#ff0000',
    # other
    'TCB': '#ff0000', 'TCG': '#00ff00', 'TCW': '#0000ff', 'TCDI': '#ffff00'
}

# mapping from spectral index formular identifiers to image bands
wavebandMapping = {
    'A': 'B1', 'B': 'B2', 'G': 'B3', 'R': 'B4', 'RE1': 'B5', 'RE2': 'B6', 'RE3': 'B7', 'RE4': 'B8A',
    'N': 'B8', 'S1': 'B11', 'S2': 'B12'
}

# EOF
