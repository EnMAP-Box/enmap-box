import os
import re
import unittest

from osgeo import gdal

from _classic.hubflow.core import Classification, Color, ClassDefinition

try:
    from reclassifyapp.reclassify import ReclassifyTableView, ReclassifyTableModel, ReclassifyTableViewDelegate, \
        reclassify
except ModuleNotFoundError as ex:
    if ex.name == 'reclassifyapp':
        raise unittest.SkipTest('Failed to import reclassifyapp')
    else:
        raise ex
from enmapbox.qgispluginsupport.qps.classification.classificationscheme import ClassificationScheme
from enmapbox.testing import TestObjects, EnMAPBoxTestCase
from qgis.PyQt.QtCore import QSortFilterProxyModel
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QTableView
from qgis.core import QgsProject


class TestReclassify(EnMAPBoxTestCase):

    def test_hubflow_reclassify(self):

        from enmapbox.testing import TestObjects
        dsSrc = TestObjects.createRasterDataset(10, 20, nc=5)
        self.assertIsInstance(dsSrc, gdal.Dataset)
        classNamesOld = ['Unclassified', 'Class 1', 'Class 2', 'Class 3', 'Class 4']
        self.assertEqual(dsSrc.GetRasterBand(1).GetCategoryNames(), classNamesOld)
        pathSrc = dsSrc.GetFileList()[0]
        self.assertTrue(pathSrc.startswith('/vsimem/'))

        pathResultFiles = []
        tmpDir = self.tempDir('test_reclassifyapp', cleanup=True)

        for i, ext in enumerate(['bsq', 'BSQ', 'bil', 'BIL', 'bip', 'BIP', 'tif', 'TIF', 'tiff', 'TIFF']):

            pathDst = tmpDir / 'testclasstiff{}.{}'.format(i, ext)
            pathDst = pathDst.as_posix()
            classification = Classification(pathSrc)
            oldDef = classification.classDefinition()
            self.assertEqual(oldDef.names(), classNamesOld[1:])

            newNames = ['No Class', 'Class B', 'Class D']
            newColors = [QColor('black'), QColor('yellow'), QColor('brown')]

            # this works
            c = Color(QColor('black'))

            # but this doesn't
            # newDef = _classic.hubflow.core.ClassDefinition(names=newNames[1:], colors=newColors[1:])

            newDef = ClassDefinition(names=newNames[1:], colors=[c.name() for c in newColors[1:]])
            newDef.setNoDataNameAndColor(newNames[0], QColor('yellow'))

            # driver = guessRasterDriver(pathDst)
            classification.reclassify(filename=pathDst,
                                      classDefinition=newDef,
                                      mapping={0: 0, 1: 1, 2: 1})  # ,
            # outclassificationDriver=driver)

            ds = gdal.Open(pathDst)

            self.assertIsInstance(ds, gdal.Dataset)
            if re.search(r'\.(bsq|bil|bip)$', pathDst, re.I):
                self.assertTrue(ds.GetDriver().ShortName == 'ENVI',
                                msg='Not opened with ENVI driver, but {}: {}'.format(ds.GetDriver().ShortName, pathDst))
            elif re.search(r'\.tiff?$', pathDst, re.I):
                self.assertTrue(ds.GetDriver().ShortName == 'GTiff',
                                msg='Not opened with GTiff driver, but {}: {}'.format(ds.GetDriver().ShortName,
                                                                                      pathDst))
            elif re.search(r'\.vrt$', pathDst, re.I):
                self.assertTrue(ds.GetDriver().ShortName == 'VRT',
                                msg='Not opened with VRT driver, but {}: {}'.format(ds.GetDriver().ShortName, pathDst))
            else:
                self.fail('Unknown extension {}'.format(pathDst))
            pathResultFiles.append(pathDst)

        for pathDst in pathResultFiles:
            ds = gdal.Open(pathDst)
            # files = ds.GetFileList()
            band = ds.GetRasterBand(1)
            ds.GetFileList()
            classnames = band.GetCategoryNames()
            if not isinstance(classnames, list):
                ct = band.GetColorTable()
                if isinstance(ct, gdal.ColorTable):
                    n = ct.GetCount()
                    if n > 0:
                        classnames2 = band.GetCategoryNames()
                        print(f'Before getColorTable {classnames}')
                        print(f'After getColorTable {classnames2}')
                        if classnames != classnames2:
                            classnames = classnames2
                s = ""
            self.assertIsInstance(classnames, list, msg='Failed to set any category names to "{}"'.format(pathDst))
            self.assertEqual(newNames, classnames, msg='Failed to set all category names to "{}"'.format(pathDst))
            print('Success: created {}'.format(pathDst))
            del ds

        QgsProject.instance().removeAllMapLayers()

    def test_reclassify(self):
        # test is deprecated
        return

        csDst = ClassificationScheme.create(2)
        csDst[0].setName('Not specified')
        csDst[1].setName('Test Class')

        LUT = {0: 0, 1: 1, 2: 1}
        classA = TestObjects.createRasterDataset()
        self.assertIsInstance(classA, gdal.Dataset)
        pathSrc = classA.GetFileList()[0]
        pathDst = '/vsimem/testresult.bsq'
        print('src path: {}'.format(pathSrc))
        print('src dims (nb, nl, ns) = ({},{},{})'.format(
            classA.RasterCount, classA.RasterYSize, classA.RasterXSize))
        print('src geotransform: {}'.format(classA.GetGeoTransform()))
        print('src projection: {}'.format(classA.GetProjectionRef()))
        print('src classes: {}'.format(classA.GetRasterBand(1).GetCategoryNames()))
        print('dst path: {}'.format(pathDst))
        print('dst classes: {}'.format(csDst.classNames()))
        dsDst = reclassify(pathSrc, csDst, LUT, output_classification=pathDst)
        csDst2 = ClassificationScheme.fromRasterImage(dsDst)
        self.assertIsInstance(csDst2, ClassificationScheme)
        self.assertEqual(csDst, csDst2)

        enmapBox.close()
        QgsProject.instance().removeAllMapLayers()

    def test_transformation_table(self):

        tv = ReclassifyTableView()
        self.assertIsInstance(tv, QTableView)

        model = ReclassifyTableModel()
        pm = QSortFilterProxyModel()
        pm.setSourceModel(model)
        tv.setModel(pm)

        viewDelegate = ReclassifyTableViewDelegate(tv)
        viewDelegate.setItemDelegates(tv)
        model.setSource(ClassificationScheme.create(2))
        model.setDestination(ClassificationScheme.create(25))

        test_dir = self.tempDir('reclassify', cleanup=True)
        os.makedirs(test_dir, exist_ok=True)
        pathCsv = test_dir / 'classmapping.csv'
        model.writeCSV(pathCsv)

        model.readCSV(pathCsv)

        self.showGui(tv)

        QgsProject.instance().removeAllMapLayers()


if __name__ == "__main__":
    unittest.main(buffer=False)
