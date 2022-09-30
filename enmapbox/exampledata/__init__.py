from os.path import dirname, join

enmap = join(dirname(__file__), 'enmap_berlin.bsq')
hires = join(dirname(__file__), 'hires_berlin.bsq')
landcover_polygon = join(dirname(__file__), 'landcover_berlin_polygon.gpkg')
landcover_point = join(dirname(__file__), 'landcover_berlin_point.gpkg')
vegetationcover_point = join(dirname(__file__), 'veg-cover-fraction_berlin_point.gpkg')


library_sli = join(dirname(__file__), 'library_berlin.sli')
library_gpkg = join(dirname(__file__), 'library_berlin.gpkg')

enmap_srf_library = join(dirname(__file__), 'enmap_srf_library.gpkg')

google_maps = 'type=xyz&url=https://mt1.google.com/vt/lyrs%3Dm%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
