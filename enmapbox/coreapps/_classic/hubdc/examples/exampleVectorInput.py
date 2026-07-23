from _classic.hubdc import Applier, ApplierOperator

def script():

    vector = r'C:\Work\data\EnMAPUrbanGradient2009\test\bug2009.shp'
    raster = r'C:\Work\data\EnMAPUrbanGradient2009\01_image_products\EnMAP01_Berlin_Urban_Gradient_2009.bsq'

    applier = Applier()
    applier.controls.setReferenceGridByImage(filename=raster)
    applier.setVector('vector', filename=vector)
    applier.setOutputRaster('out', filename=r'c:\output\out.img', format='ENVI')
    applier.apply(operatorType=SimpleIO)

class SimpleIO(ApplierOperator):

    def ufunc(self):
        #self.setArray('out', array=self.getVectorRasterization('vector', initValue=0, burnAttribute='ID_L1'))
        self.setArray('out', array=self.getVectorRasterization('vector', initValue=0, burnValue=1, filter="Level_1 = 'Vegetation'"))


if __name__ == '__main__':
    script()
