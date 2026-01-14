# import matplotlib
# matplotlib.use('QT5Agg')
# from matplotlib import pyplot
#
# from tempfile import gettempdir
# from os.path import join, exists, basename, dirname
# import numpy
# from unittest import TestCase
#
# from _classic.hubdc.core import *
# from _classic.hubdc.testdata import LT51940232010189KIS01, LT51940242010189KIS01, BrandenburgDistricts, root
#
# outdir = join('output_core')
# raster = openRasterDataset(LT51940232010189KIS01.cfmask)
# nir = openRasterDataset(LT51940232010189KIS01.nir)
# swir1 = openRasterDataset(LT51940232010189KIS01.swir1)
# red = openRasterDataset(LT51940232010189KIS01.red)
# vector = openVectorDataset(filename=BrandenburgDistricts.shp)
# grid = openRasterDataset(LT51940232010189KIS01.cfmask).grid()
#
#
# class Test(TestCase):
#     def test_Open(self):
#         self.assertIsInstance(obj=openRasterDataset(filename=LT51940232010189KIS01.cfmask), cls=RasterDataset)
#         with self.assertRaises(errors.FileNotExistError):
#             openRasterDataset(filename='not a valid file')
#
#     def test_OpenLayer(self):
#         self.assertIsInstance(obj=openVectorDataset(filename=BrandenburgDistricts.shp), cls=VectorDataset)
#         with self.assertRaises(errors.FileNotExistError):
#             openRasterDataset(filename='not a valid file')
#
#     def test_repr(self):
#         print(RasterDriver(name='MEM'))
#         print(MemDriver())
#         print(EnviDriver())
#         print(ErdasDriver())
#         print(GTiffDriver())
#         print(grid.extent())
#         print(Resolution(x=30, y=30))
#         print(Projection.wgs84())
#         print(Projection.wgs84WebMercator())
#         print(Projection.utm(zone=33))
#         print(Projection.utm(zone=33, north=False))
#         print(Pixel(x=0, y=0))
#         print(grid.extent().geometry())
#         print(Point(x=0, y=0, projection=Projection.wgs84()))
#         print(RasterSize(x=10, y=20))
#         print(grid)
#         print(raster)
#         print(raster.band(index=0))
#         print(vector)
#
#
# class TestRasterDriver(TestCase):
#     def test_Driver(self):
#         self.assertIsInstance(obj=RasterDriver(name='ENVI').gdalDriver(), cls=gdal.Driver)
#         with self.assertRaises(errors.InvalidGDALDriverError):
#             RasterDriver(name='not a valid driver name')
#
#     def test___str__(self):
#         print(RasterDriver(name='ENVI'))
#         print(MemDriver())
#         print(VrtDriver())
#         print(EnviDriver())
#         print(GTiffDriver())
#         print(ErdasDriver())
#
#     #def test_prepareCreation(self):
#         #relativeFilename = 'test_output/test.bsq'
#         #absoluteFilename = EnviDriver().prepareCreation(filename=relativeFilename)
#         #assert abspath(relativeFilename) == absoluteFilename
#         #assert '' == EnviDriver().prepareCreation(filename=None)
#         #EnviDriver().prepareCreation(filename='test_output/test.bsq')
#
#     def test_equal(self):
#         d1 = EnviDriver()
#         d2 = GTiffDriver()
#         d3 = RasterDriver('ENVI')
#         self.assertTrue(d1.equal(d3))
#         self.assertFalse(d1.equal(d2))
#
#     def test_create(self):
#         self.assertIsInstance(obj=MemDriver().create(grid=grid), cls=RasterDataset)
#         try:
#             MemDriver().create(grid=grid, filename='abc')
#         except Exception as error:
#             print(error)
#
#     def test_fromFilename(self):
#         for ext in ['bsq', 'bip', 'bil', 'tif', 'img', 'vrt']:
#             filename = join(outdir, 'file.' + ext)
#             driver = RasterDriver.fromFilename(filename=filename)
#             print(driver)
#
#         assert RasterDriver.fromFilename(filename='file.xyz').equal(other=EnviDriver())
#
#     def prepareCreation(self):
#         print(RasterDriver().prepareCreation('raster.bsq'))
#         print(MemDriver().prepareCreation(''))
#
#
# class TestVectorDriver(TestCase):
#     def test_Driver(self):
#         self.assertIsInstance(obj=VectorDriver(name='ESRI Shapefile').ogrDriver(), cls=ogr.Driver)
#         with self.assertRaises(errors.InvalidOGRDriverError):
#             VectorDriver(name='not a valid driver name')
#
#     def test___str__(self):
#         print(VectorDriver(name='ESRI Shapefile'))
#         print(ESRIShapefileDriver())
#         print(GeoPackageDriver())
#         print(MemoryDriver())
#
#     def test_equal(self):
#         d1 = ESRIShapefileDriver()
#         d2 = GeoPackageDriver()
#         d3 = VectorDriver(name='ESRI Shapefile')
#         self.assertTrue(d1.equal(d3))
#         self.assertFalse(d1.equal(d2))
#
#     def test_create(self):
#         pass
#         # todo
#         #self.assertIsInstance(obj=VectorDriver('MEM').create(grid=grid), cls=RasterDataset)
#
#     def test_fromFilename(self):
#         for ext in ['shp', 'gpkg']:
#             filename = join(outdir, 'file.' + ext)
#             driver = VectorDriver.fromFilename(filename=filename)
#             print(driver)
#         print(VectorDriver.fromFilename(filename=''))
#
#
#         try:
#             VectorDriver.fromFilename(filename='file.xyz')
#         except errors.InvalidOGRDriverError as error:
#             print(str(error))
#
#     def test_prepareCreation(self):
#         filename = join(tempfile.gettempdir(), 'prepareCreation', 'vector.shp')
#         print(filename)
#         driver = ESRIShapefileDriver()
#         points = [Point(x, y, Projection.wgs84()) for x, y in ((-1, -1), (1, 1))]
#         ds = VectorDataset.fromPoints(points=points, filename=filename, driver=driver)
#         ds.close()
#         driver.prepareCreation(filename=filename)
#         assert not exists(filename)
#
#     def test_delete(self):
#         driver = ESRIShapefileDriver()
#         points = [Point(x, y, Projection.wgs84()) for x, y in ((-1, -1), (1, 1))]
#
#         #filename = 'test_data/VectorDriver.delete.shp'
#         #ds = VectorDataset.fromPoints(points=points, filename=filename, driver=driver)
#         #ds.close()
#         #driver.delete(filename=filename)
#         #assert not exists(filename)
#
#         filename = '/vsimem/VectorDriver.delete.shp'
#         ds = VectorDataset.fromPoints(points=points, filename=filename, driver=driver)
#         ds.close()
#         driver.delete(filename=filename)
#
#
# class TestRasterBand(TestCase):
#
#     def test(self):
#         band = raster.band(0)
#         band.gdalBand()
#         try:
#             raster.band(-1)
#         except errors.IndexError as error:
#             print(error)
#
#     def test_array(self):
#         ds = openRasterDataset(LT51940232010189KIS01.cfmask)
#         ds.band(0).array()
#         ds.band(0).array(grid=Grid(extent=ds.extent().reproject(Projection.wgs84()), resolution=0.01))
#
#     def test_readAsArray(self):
#         ds = openRasterDataset(LT51940232010189KIS01.cfmask)
#         band = ds.band(0)
#         self.assertIsInstance(obj=band, cls=RasterBandDataset)
#         self.assertIsInstance(obj=band.readAsArray(), cls=numpy.ndarray)
#         self.assertIsInstance(
#             obj=band.readAsArray(grid=ds.grid().subset(offset=Pixel(x=0, y=0), size=RasterSize(x=10, y=10), trim=True)),
#             cls=numpy.ndarray)
#         with self.assertRaises(errors.AccessGridOutOfRangeError):
#             band.readAsArray(grid=ds.grid().subset(offset=Pixel(x=-1, y=-1), size=RasterSize(x=10, y=10)))
# #        with self.assertRaises(errors.AccessGridOutOfRangeError):
# #            band.readAsArray(grid=ds.grid().subset(offset=Pixel(x=-10, y=-10), size=RasterSize(x=10, y=10)))
#         a = band.readAsArray()
#         b = band.readAsArray(grid=ds.grid().subset(offset=Pixel(x=0, y=0), size=ds.grid().size()))
#         self.assertTrue(numpy.all(a == b))
#
#     def test_writeArray(self):
#         ds = MemDriver().create(grid=grid)
#         band = ds.band(index=0)
#         array2d = numpy.full(shape=grid.shape(), fill_value=42)
#         array3d = numpy.full(shape=grid.shape(), fill_value=42)
#         band.writeArray(array=array2d)
#         band.writeArray(array=array3d)
#         band.writeArray(array=array3d, grid=grid)
#         with self.assertRaises(errors.ArrayShapeMismatchError):
#             band.writeArray(array=array2d[:10, :10])
#         band.writeArray(array=array2d[:10, :10], grid=grid.subset(offset=Pixel(x=0, y=0), size=RasterSize(x=10, y=10)))
#         #band.writeArray(array=array2d[:10, :10], grid=grid.subset(offset=Pixel(x=-5, y=-5), size=RasterSize(x=10, y=10)))
#         band.writeArray(array=array2d[:10, :10], grid=grid.subset(offset=Pixel(x=0, y=0), size=RasterSize(x=10, y=10)))
#         band.writeArray(array=array2d[:10, :10][None], grid=grid.subset(offset=Pixel(x=0, y=0), size=RasterSize(x=10, y=10)))
#
#         with self.assertRaises(errors.AccessGridOutOfRangeError):
#             band.writeArray(array=array2d, grid=grid.subset(offset=Pixel(x=10, y=10), size=grid.size()))
#
#     def test_setGetMetadataItem(self):
#         ds = MemDriver().create(grid=grid)
#         band = ds.band(index=0)
#         band.setMetadataItem(key='my key', value=42, domain='ENVI')
#         self.assertEqual(band.metadataItem(key='my key', domain='ENVI', dtype=int), 42)
#         band.metadataItem(key='my key')
#         band.metadataItem(key='not a key')
#         try:
#             band.metadataItem(key='not a key', required=True)
#         except errors.MissingMetadataItemError as error:
#             print(error)
#         band.setMetadataItem(key='my key', value=None)
#         band.metadataDomain(domain='ENVI')
#         band.metadataDict()
#
#     def test_copyMetadata(self):
#         ds = MemDriver().create(grid=grid)
#         ds2 = MemDriver().create(grid=grid)
#         band = ds.band(index=0)
#         band2 = ds2.band(index=0)
#         band.setMetadataItem(key='my key', value=42, domain='ENVI')
#         band2.copyMetadata(other=band)
#         self.assertEqual(band2.metadataItem(key='my key', domain='ENVI', dtype=int), 42)
#
#     def test_setGetNoDataValue(self):
#         ds = MemDriver().create(grid=grid)
#         band = ds.band(index=0)
#         self.assertIsNone(band.noDataValue())
#         try:
#             band.noDataValue(required=True)
#         except errors.MissingNoDataValueError as error:
#             print(error)
#
#         self.assertEqual(band.noDataValue(default=123), 123)
#         band.setNoDataValue(value=42)
#         self.assertEqual(band.noDataValue(default=123), 42)
#
#
#     def test_setDescription(self):
#         ds = MemDriver().create(grid=grid)
#         band = ds.band(index=0)
#         band.setDescription(value='Hello')
#         self.assertEqual(band.description(), 'Hello')
#
#     def test_description(self):
#         self.test_setDescription()
#
#     def test_metadataDomainList(self):
#         ds = MemDriver().create(grid=grid)
#         band = ds.band(index=0)
#         band.setMetadataItem(key='my key', value=42, domain='ENVI')
#         band.setMetadataItem(key='my key', value=42, domain='xyz')
#         gold = {'ENVI', 'xyz'}
#         lead = set(band.metadataDomainList())
#         self.assertSetEqual(gold, lead)
#
#     def test_fill(self):
#         ds = MemDriver().create(grid=grid)
#         band = ds.band(index=0)
#         band.fill(value=42)
#         array = band.readAsArray()
#         self.assertTrue(numpy.all(array == 42))
#
#
# class TestRasterDataset(TestCase):
#
#     def test_debug(self):
#         ds1 = openRasterDataset(filename='C:\\source\\enmap-box-testdata\\enmapboxtestdata\\enmap_berlin.bsq')
#         grid = Grid(extent=Extent(xmin=382857.97, xmax=385737.97, ymin=5808396.35, ymax=5820366.35, projection=Projection.utm(zone=33)),
#                     resolution=Resolution(x=30.0, y=119.7))
#         c1 = ds1.translate(grid=grid)
#         assert c1.grid().equal(grid)
#
#     def test_filename(self):
#         assert openRasterDataset(LT51940232010189KIS01.green).filename() == LT51940232010189KIS01.green
#         vrtFilename = '/vsimem/green.vrt'
#         rasterDataset = createVRTDataset([LT51940232010189KIS01.green, LT51940242010189KIS01.green], filename=vrtFilename)
#         assert rasterDataset.filename() == vrtFilename
#
#     def test_translate(self):
#         grid = Grid(extent=Extent(xmin=0, xmax=2, ymin=0, ymax=1, projection=Projection.wgs84()), resolution=1)
#         subgrid = Grid(extent=Extent(xmin=0, xmax=1, ymin=0, ymax=1, projection=Projection.wgs84()), resolution=1)
#         array = np.array([[[1,2]]])
#         gold = np.array([[[1]]])
#         rasterdataset = RasterDataset.fromArray(array=array, grid=grid)
#         assert rasterdataset.translate(grid=subgrid).readAsArray() == gold
#
#     def test_translateResampleAlgs(self):
#         ds = RasterDataset.fromArray(array=[[1, -1, -1, -1, -1, -1],
#                                             [-1, 2, -1, -1, -1, -1],
#                                             [-1, -1, 3, -1, -1, -1],
#                                             [-1, -1, -1, 4, -1, -1],
#                                             [-1, -1, -1, -1, 5, -1],
#                                             [-1, -1, -1, -1, -1, 6]])
#         ds.setNoDataValue(-1)
#         grid = ds.grid().atResolution(resolution=ds.grid().resolution() * 3)
#
#         for resampleAlg in ResampleAlgHandler.translateResampleAlgorithms():
#             print(resampleAlg)
#             print(ds.translate(grid=grid, resampleAlg=resampleAlg).readAsArray())
#
#     def test_translate_withSubpixelShift(self):
#         array = np.array([[[0, 100, 200]]])
#         grid = Grid(extent=Extent(xmin=0, xmax=3, ymin=0, ymax=1, projection=Projection.wgs84()), resolution=1)
#         rasterdataset = RasterDataset.fromArray(array=array, grid=grid)
#         rasterdataset.setNoDataValue(-1)
#         shift = 0.1
#         gridShifted = Grid(extent=Extent(xmin=0-shift, xmax=3-shift, ymin=0, ymax=1, projection=Projection.wgs84()), resolution=1)
#
#         for name in dir(gdal):
#             if not name.startswith('GRA_'): continue
#             if name in ['GRA_Med', 'GRA_Max', 'GRA_Min', 'GRA_Q1', 'GRA_Q3']: continue
#             resampleAlg = getattr(gdal, name)
#
#             print(name, resampleAlg)
#             translated = rasterdataset.translate(grid=gridShifted, resampleAlg=resampleAlg)
#             assert translated.grid().equal(gridShifted), name
#             #warped = rasterdataset.warp(grid=gridShifted, resampleAlg=resampleAlg)
#             #assert warped.grid().equal(gridShifted), name
#
#     def test_warpResampleAlgs(self):
#
#         ds = RasterDataset.fromArray(array=[[1, -1, -1, -1, -1, -1],
#                                             [-1, 2, -1, -1, -1, -1],
#                                             [-1, -1, 3, -1, -1, -1],
#                                             [-1, -1, -1, 4, -1, -1],
#                                             [-1, -1, -1, -1, 5, -1],
#                                             [-1, -1, -1, -1, -1, 6]])
#         ds.setNoDataValue(-1)
#         grid = ds.grid().atResolution(resolution=ds.grid().resolution() * 3)
#
#         for resampleAlg in ResampleAlgHandler.warpResampleAlgorithms():
#             print(resampleAlg)
#             print(ds.warp(grid=grid, resampleAlg=resampleAlg).readAsArray())
#
#     def test(self):
#         self.assertIsInstance(obj=raster.grid(), cls=Grid)
#         for band in raster.bands():
#             self.assertIsInstance(obj=band, cls=RasterBandDataset)
#         self.assertIsInstance(raster.driver(), RasterDriver)
#         self.assertIsInstance(raster.readAsArray(), np.ndarray)
#         self.assertIsInstance(raster.readAsArray(grid=grid), np.ndarray)
#
#
#         raster2 = RasterDataset.fromArray(grid=grid, array=np.ones(shape=grid.shape()))
#         raster2 = RasterDataset.fromArray(grid=grid, array=[np.ones(shape=grid.shape(), dtype=np.bool)],
#                                           filename='/vsimem/raster.bsq', driver=EnviDriver())
#         raster2.setNoDataValue(value=-9999)
#         raster2.noDataValue()
#         MemDriver().create(grid=grid).noDataValue(default=-9999)
#         raster2.projection()
#         raster2.extent()
#
#
#         raster2.setDescription(value='Hello')
#         raster2.description()
#         raster2.copyMetadata(other=raster)
#         raster2.setMetadataItem(key='a', value=42, domain='my domain')
#         raster2.setMetadataItem(key='a', value=None, domain='my domain')
#         raster2.setMetadataItem(key='file_compression', value=1, domain='ENVI')
#         raster2.setMetadataItem(key='b', value=[1, 2, 3], domain='my domain')
#         raster2.metadataItem(key='a', domain='my domain')
#         raster2.metadataItem(key='b', domain='my domain')
#         raster2.metadataItem(key='not a key', required=False)
#         try:
#             raster2.metadataItem(key='not a key', required=True)
#         except errors.MissingMetadataItemError as error:
#             print(error)
#         raster2.setMetadataDict(metadataDict=raster2.metadataDict())
#         import datetime
#         raster2.setAcquisitionTime(acquisitionTime=datetime.datetime(2010, 12, 31))
#         print(raster2.acquisitionTime())
#
#
#         raster2.warp()
#         raster2.translate()
#         grid2 = Grid(extent=grid.extent(), resolution=Resolution(x=400, y=400))
#         raster2.translate(grid=grid2)
#         raster2.array()
#         raster2.array()
#
#         grid2 = Grid(extent=grid.extent().reproject(projection=Projection.utm(zone=33)),
#                      resolution=grid.resolution())
#         raster2.array(grid=grid2)
#         raster.zprofile(pixel=Pixel(0, 0))
#         raster.xprofile(row=Row(0, 0))
#         raster.yprofile(column=Column(0, 0))
#
#         raster2.dtype()
#         raster2.flushCache()
#         raster2.close()
#
#         raster2 = RasterDataset.fromArray(grid=grid, array=[np.ones(shape=grid.shape(), dtype=np.bool)],
#                                                filename=join(outdir, 'zeros.tif'), driver=GTiffDriver())
#
#         raster2 = RasterDataset.fromArray(grid=grid, array=[np.ones(shape=grid.shape(), dtype=np.bool)],
#                                                filename=join(outdir, 'zeros.img'), driver=EnviDriver())
#
#         raster.filename()
#         raster.filenames()
#
#         raster3 = RasterDataset.fromArray(array=np.zeros(shape=(2,10,10)))
#         raster3.setNoDataValues(values=[1,2])
#         try:
#             raster3.noDataValue()
#         except errors.HubDcError as error:
#             print(error)
#
#
#     def test_categoryNamesAndLookup(self):
#         raster2 = RasterDataset.fromArray(grid=grid, array=np.ones(shape=grid.shape()))
#         band = raster2.band(0)
#         names=['a', 'b', 'c']
#         colors = [(1,1,1,255), (10,10,10,255), (100,100,100,255)]
#         band.setCategoryNames(names=names)
#         band.setCategoryColors(colors=colors)
#         self.assertListEqual(names, band.categoryNames())
#         self.assertListEqual(colors, band.categoryColors())
#
#
#     def test_createVRT(self):
#         createVRTDataset(filename=join(outdir, 'stack1.vrt'), rasterDatasetsOrFilenames=[raster, raster])
#         createVRTDataset(filename=join(outdir, 'stack2.vrt'), rasterDatasetsOrFilenames=[LT51940232010189KIS01.cfmask] * 2)
#
#     def test_buildOverviews(self):
#         filename = join(outdir, 'rasterWithOverviews.bsq')
#         RasterDataset.fromArray(array=np.zeros(shape=[1, 1000, 1000]), filename=filename, driver=EnviDriver()).close()
#         buildOverviews(filename=filename, minsize=128)
#         buildOverviews(filename=filename, minsize=1280)
#
#     def test_plots(self):
#         import enmapboxtestdata
#         enmap = openRasterDataset(filename=enmapboxtestdata.enmap)
#         enmap.plotZProfile(pixel=Pixel(x=0, y=0)).win.close()
#         enmap.plotZProfile(pixel=Pixel(x=0, y=0), spectral=True).win.close()
#         enmap.plotXProfile(row=Row(0, 0)).win.close()
#         enmap.plotYProfile(column=Column(0, 0)).win.close()
#
#         #enmap.plotSinglebandGrey()  # , vmin=0, vmax=9000)
#         #enmap.plotSinglebandGrey(index=0, pmin=2, pmax=98)
#         #enmap.plotMultibandColor()
#
#         #raster.
#         #raster = Raster.fromSample(filename=join(outdir, 'RasterFromSample.bsq'), sample=enmapClassificationSample)
#         #print(raster)
#         #raster.dataset().plotPixel(pixel=Pixel(x=0, y=0))
#         #pyplot.plot(raster.dataset().array()[:,0,0])
#
#
# class TestVectorDataset(TestCase):
#     def test(self):
#         gridSameProjection = Grid(extent=vector.extent(), resolution=Resolution(x=1, y=1))
#         vector.rasterize(grid=grid)
#         vector.rasterize(grid=gridSameProjection, noDataValue=-9999)
#         vector.featureCount()
#         vector.fieldCount()
#         vector.fieldNames()
#         vector.fieldTypeNames()
#         vector.filename()
#         openVectorDataset(filename=BrandenburgDistricts.shp).close()
#         try:
#             openVectorDataset(filename=BrandenburgDistricts.shp, layerNameOrIndex=-1)
#         except errors.InvalidOGRLayerError as error:
#             print(error)
#         try:
#             ds = openVectorDataset(filename=BrandenburgDistricts.shp, layerNameOrIndex=dict())
#         except errors.ObjectParserError as error:
#             print(error)
#
#     def test_rasterize(self):
#         import enmapboxtestdata
#         points = openVectorDataset(filename=enmapboxtestdata.landcover_points)
#         grid = points.grid(resolution=30)
#         raster = points.rasterize(grid=grid)
#         print(raster)
#
#     def test_rasterizeOnGridWithDifferentProjection(self):
#         import enmapboxtestdata
#         points = openVectorDataset(filename=enmapboxtestdata.landcover_points)
#         grid = Grid(extent=points.extent().reproject(projection=Projection.wgs84WebMercator()),
#                     resolution=30)
#         raster = points.rasterize(grid=grid)
#         print(raster)
#
#     def test_createFidDataset(self):
#         import enmapboxtestdata
#         points = openVectorDataset(filename=enmapboxtestdata.landcover_points)
#         fid = points.createFidDataset(filename=join(outdir, 'createFidDataset2.gpkg'))
#         grid = openRasterDataset(enmapboxtestdata.enmap).grid()
#         raster = fid.rasterize(grid=grid, filename=join(outdir, 'rastered2.bsq'), initValue=-1, burnAttribute=fid.fieldNames()[0])
#         self.assertListEqual(list(np.unique(raster.readAsArray())), [-1.,  0.,  1.,  2.,  3.,  4.])
#
#     def test_extractPixel(self):
#         import enmapboxtestdata
#         points = openVectorDataset(filename=enmapboxtestdata.landcover_points)
#         rasterValues, vectorValues, fids = points.extractPixel(rasterDataset=openRasterDataset(enmapboxtestdata.enmap))
#         print(rasterValues)
#         print(vectorValues)
#
#     def test_reproject(self):
#         import enmapboxtestdata
#         points = openVectorDataset(filename=enmapboxtestdata.landcover_points)
# #        points = openVectorDataset(filename=r'C:\Users\janzandr\Desktop\regions.gpkg')
#         reprojected = points.reproject(projection=Projection.wgs84())
#         print(reprojected)
#
#     def test_attributeTable(self):
#         print(vector.attributeTable())
#
# class TestExtent(TestCase):
#     def test(self):
#         extent = grid.extent()
#         Extent.fromGeometry(geometry=extent.geometry())
#         extent.upperLeft()
#         extent.upperRight()
#         extent.lowerLeft()
#         extent.lowerRight()
#         extent.reproject(projection=Projection.wgs84())
#         extent.intersects(other=extent)
#         extent.intersection(other=extent)
#         extent.union(other=extent)
#         extent.centroid()
#
#
# class TestGeometry(TestCase):
#     def test(self):
#         geometry = grid.extent().geometry()
#         print(geometry.intersects(other=geometry))
#         print(geometry.union(other=geometry))
#         print(geometry.intersection(other=geometry))
#         print(geometry.within(other=geometry))
#
#
# class TestResolution(TestCase):
#     def test(self):
#         resolution = Resolution(x=30, y=30)
#         print(Resolution.parse(resolution))
#         print(Resolution.parse(30))
#         print(Resolution.parse('30'))
#         print(Resolution.parse((30, 30)))
#
#         try:
#             print(Resolution.parse(dict()))
#         except errors.ObjectParserError as error:
#             print(error)
#
#         self.assertTrue(resolution.equal(other=Resolution(x=30, y=30)))
#         self.assertFalse(resolution.equal(other=Resolution(x=10, y=10)))
#         assert (resolution / 2).equal(other=Resolution(15, 15))
#         print(resolution / (1, 1))
#         print(resolution / '1')
#         try:
#             print(resolution / dict())
#         except errors.TypeError as error:
#             print(error)
#         assert (resolution * 2).equal(other=Resolution(60, 60))
#         print(resolution * (1, 1))
#         print(resolution * '1')
#         try:
#             print(resolution * dict())
#         except errors.TypeError as error:
#             print(error)
#
#
# class TestGrid(TestCase):
#
#     def test(self):
#         Grid(extent=grid.extent(), resolution=grid.resolution())
#         grid.equal(other=grid)
#         #grid.reproject(other=grid)
#         grid.pixelBuffer(buffer=1)
#         grid.subgrids(size=RasterSize(x=256, y=256))
#         grid.atResolution(resolution=10)
#         grid.anchor(point=Point(x=0, y=0, projection=Projection.wgs84WebMercator()))
#
#     def test_coordinates(self):
#         grid = Grid(extent=Extent(xmin=0, xmax=3, ymin=0, ymax=2, projection=Projection.wgs84()),
#                     resolution=Resolution(x=1, y=1))
#         xgold = np.array([[0.5, 1.5, 2.5], [0.5, 1.5, 2.5]])
#         ygold = np.array([[1.5, 1.5, 1.5], [0.5, 0.5, 0.5]])
#         self.assertTrue(np.all(grid.xMapCoordinatesArray() == xgold))
#         self.assertTrue(np.all(grid.yMapCoordinatesArray() == ygold))
#
#         xgold = np.array([[0, 1, 2], [0, 1, 2]])
#         ygold = np.array([[0, 0, 0], [1, 1, 1]])
#
#         self.assertTrue(np.all(grid.xPixelCoordinatesArray() == xgold))
#         self.assertTrue(np.all(grid.yPixelCoordinatesArray() == ygold))
#
#         subgrid = grid.subset(offset=Pixel(x=1, y=1), size=RasterSize(x=2, y=1))
#         subxgold = xgold[1:, 1:]
#         subygold = ygold[1:, 1:]
#
#         print(subgrid.xPixelCoordinatesArray())
#         print(subgrid.yPixelCoordinatesArray())
#
#         self.assertTrue(np.all(np.equal(subgrid.xPixelCoordinatesArray(offset=1), subxgold)))
#         self.assertTrue(np.all(np.equal(subgrid.yPixelCoordinatesArray(offset=1), subygold)))
#
# class TestPixel(TestCase):
#     def test(self):
#         p = Pixel(x=0, y=1)
#         Pixel.parse(p)
#         Pixel.parse((0, 1))
#         try:
#             Pixel.parse(dict())
#         except errors.ObjectParserError as error:
#             print(error)
#
#
# class TestPoint(TestCase):
#     def test(self):
#
#         p = Point(x=0, y=1, projection=Projection.wgs84())
#         assert p.x() == 0
#         assert p.y() == 1
#         assert p.projection().equal(Projection.wgs84())
#
# class TestRasterSize(TestCase):
#     def test(self):
#
#         s = RasterSize(x=1, y=1)
#         print(s)
#         self.assertIsInstance(RasterSize.parse(s), RasterSize)
#         self.assertIsInstance(RasterSize.parse((1, 1)), RasterSize)
#         try: RasterSize.parse(dict())
#         except errors.ObjectParserError as error: print(error)
#         try: RasterSize(0, 1)
#         except errors.InvalidRasterSize as error: print(error)
#         try: RasterSize(1, 0)
#         except errors.InvalidRasterSize as error: print(error)
#
#
# class TestENVI(TestCase):
#     def test(self):
#         print(ENVI.gdalType(enviType=4))
#         print(ENVI.numpyType(enviType=4))
#         print(ENVI.typeSize(enviType=4))
#         ds = RasterDataset.fromArray(array=np.zeros(shape=(3, 100, 100)), filename=join(outdir, 'raster.bsq'), driver=EnviDriver())
#         filenameHeader = ENVI.findHeader(filenameBinary=ds.filename(), ext='.hdr')
#         assert ENVI.findHeader(filenameBinary='not a file') is None
#         metadata = ENVI.readHeader(filenameHeader=filenameHeader)
#         ENVI.writeHeader(filenameHeader=join(outdir, 'raster.txt'), metadata=metadata)
#
# class TestProjection(TestCase):
#     def test(self):
#         print(Projection.fromEpsg(3035))
#         print(Projection.wgs84().wkt())
#         print(Projection.wgs84())
#         print(Projection.utm(zone=33, north=True))
#         print(Projection.utm(zone=33, north=False))
#         print(Projection.wgs84WebMercator())
#         print(Projection.wgs84().equal(other=Projection.wgs84WebMercator()))
#
# class TestAuxClasses(TestCase):
#     def test(self):
#         print(Column(x=0, z=0))
#         print(Row(y=0, z=0))
#         print(Pixel(x=0, y=0))
#
# class TestMapViewer(TestCase):
#     def test(self):
#         import enmapboxtestdata
#         ds = openRasterDataset(enmapboxtestdata.enmap)
#         print(ds.grid().extent().reproject(Projection.wgs84()))
#         viewer = MapViewer()
#         viewer.addLayer(ds.mapLayer())
#         #viewer._printExtent = True
#         viewer.setProjection(Projection.wgs84())
#         viewer.setExtent(Extent(xmin=13.29, xmax=13.32, ymin=52.47, ymax=52.49, projection=Projection.wgs84()))
#         #viewer.show()
#         #viewer.save(filename=join(outdir, 'viewer.png'))
