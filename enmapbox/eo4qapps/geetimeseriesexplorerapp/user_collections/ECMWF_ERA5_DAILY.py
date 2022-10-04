# Code provided by Pedro Venancio
# Title: ERA5 Daily Aggregates - Latest Climate Reanalysis Produced by ECMWF / Copernicus Climate Change Service

import ee

bands = ee.List(
    ['mean_2m_air_temperature', 'minimum_2m_air_temperature', 'maximum_2m_air_temperature', 'dewpoint_2m_temperature',
     'total_precipitation', 'surface_pressure', 'mean_sea_level_pressure', 'u_component_of_wind_10m',
     'v_component_of_wind_10m'])
band_names = ee.List(
    ['Average air temperature at 2m K', 'Minimum air temperature at 2m K', 'Maximum air temperature at 2m K',
     'Dewpoint temperature at 2m K', 'Total precipitation m', 'Surface pressure Pa', 'Mean sea level pressure Pa',
     '10m u-wind ms', '10m v-wind ms'])

era5d = ee.ImageCollection('ECMWF/ERA5/DAILY').select(bands, band_names)

era5d = era5d.map(lambda image: image.addBands(
    image.expression("(b('Average air temperature at 2m K') - 273.15)").rename('Average air temperature at 2m DegC')))

era5d = era5d.map(lambda image: image.addBands(
    image.expression("(b('Minimum air temperature at 2m K') - 273.15)").rename('Minimum air temperature at 2m DegC')))

era5d = era5d.map(lambda image: image.addBands(
    image.expression("(b('Maximum air temperature at 2m K') - 273.15)").rename('Maximum air temperature at 2m DegC')))

era5d = era5d.map(lambda image: image.addBands(
    image.expression("(b('Dewpoint temperature at 2m K') - 273.15)").rename('Dewpoint temperature at 2m DegC')))

era5d = era5d.map(lambda image: image.addBands(
    image.expression("(b('Total precipitation m') * 1000)").rename('Total precipitation mm')))

era5d = era5d.map(
    lambda image: image.addBands(image.expression("(b('Surface pressure Pa') / 100)").rename('Surface pressure hPa')))

era5d = era5d.map(lambda image: image.addBands(
    image.expression("(b('Mean sea level pressure Pa') / 100)").rename('Mean sea level pressure hPa')))

era5d = era5d.map(lambda image: image.addBands(
    image.expression("(sqrt(b('10m u-wind ms')**2 + b('10m v-wind ms')**2)) * 3.6").rename('10m Wind Speed kph')))

era5d = era5d.map(lambda image: image.addBands(
    image.expression("180+(180/3.14159265358979)*atan2(b('10m v-wind ms'),(b('10m u-wind ms')))").rename(
        '10m Wind Direction Deg')))

bandColors = {
    'Average air temperature at 2m K': '#ff7f00',
    'Minimum air temperature at 2m K': '#27c9ff',
    'Maximum air temperature at 2m K': '#ff0400',
    'Dewpoint temperature at 2m K': '#00ff0c',
    'Total precipitation m': '#0026ff',
    'Surface pressure Pa': '#fdae61',
    'Mean sea level pressure Pa': '#fff301',
    '10m u-wind ms': '#ff01fb',
    '10m v-wind ms': '#c1c1c1',
    'Average air temperature at 2m DegC': '#ff7f00',
    'Minimum air temperature at 2m DegC': '#27c9ff',
    'Maximum air temperature at 2m DegC': '#ff0400',
    'Dewpoint temperature at 2m DegC': '#00ff0c',
    'Total precipitation mm': '#0026ff',
    'Surface pressure hPa': '#fdae61',
    'Mean sea level pressure hPa': '#fff301',
    '10m Wind Speed kph': '#abdda4',
    '10m Wind Direction Deg': '#93a9cf'
}

collection = era5d
