from os.path import dirname, join

root = dirname(__file__)


class SpectralSensors():
    class Desis():
        responseFunctionFile = join(root, 'desis.csv')
        shortname = 'DESIS'
        longname = 'DLR Earth Sensing Imaging Spectrometer Mission'
        website = 'https://www.dlr.de/en/images/institutes-1/institute-of-optical-sensor-systems/os-desis'

    class Emit():
        responseFunctionFile = join(root, 'emit.csv')
        shortname = 'EMIT'
        longname = 'Earth Surface Mineral Dust Source Investigation'
        website = 'https://earth.jpl.nasa.gov/emit/'

    class Enmap():
        responseFunctionFile = join(root, 'enmap.csv')
        shortname = 'EnMAP'
        longname = 'Environmental Mapping and Analysis Program'
        website = 'https://www.enmap.org/'

    class LandsatOli():
        responseFunctionFile = join(root, 'landsat_oli.geojson')
        shortname = 'Landsat 8/9 OLI'
        longname = 'Landsat 8/9 Operational Land Imager'
        website = 'https://www.usgs.gov/core-science-systems/nli/landsat/landsat-satellite-missions'

    class LandsatEtm():
        responseFunctionFile = join(root, 'landsat_etm.geojson')
        shortname = 'Landsat 7 ETM+'
        longname = 'Landsat 7 Enhanced Thematic Mapper Plus'
        website = 'https://www.usgs.gov/core-science-systems/nli/landsat/landsat-satellite-missions'

    class LandsatTm():
        responseFunctionFile = join(root, 'landsat_tm.geojson')
        shortname = 'Landsat 4/5 TM'
        longname = 'Landsat 4/5 Thematic Mapper'
        website = 'https://www.usgs.gov/core-science-systems/nli/landsat/landsat-satellite-missions'

    class Prisma():
        responseFunctionFile = join(root, 'prisma.csv')
        shortname = 'PRISMA'
        longname = 'Hyperspectral Precursor of the Application Mission'
        website = 'https://www.asi.it/en/earth-science/prisma/'

    class Sentinel2a():
        responseFunctionFile = join(root, 'sentinel2a_msi.geojson')
        shortname = 'Sentinel-2A MSI'
        longname = 'Sentinel-2A MultiSpectral Instrument (MSI)'
        website = 'https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2'

    class Sentinel2b():
        responseFunctionFile = join(root, 'sentinel2b_msi.geojson')
        shortname = 'Sentinel-2B MSI'
        longname = 'Sentinel-2B MultiSpectral Instrument (MSI)'
        website = 'https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2'
