from _classic.hubdc.applier import Applier
from _classic.hubdc.applier import ApplierOperator

def script():

    shpfile = r'C:\output\LandCov_Vec_Berlin_Urban_Gradient_2009.shp'
    applier = Applier()
    applier.controls.setReferenceGridByVector(filename=shpfile, xRes=5, yRes=5)
    applier.setVector('vector', filename=r'C:\output\LandCov_Vec_Berlin_Urban_Gradient_2009.shp')
    applier.setOutputRaster('id_l1', filename=r'c:\output\id_l1.img')
    applier.apply(operatorType=SimpleIO)

class SimpleIO(ApplierOperator):

    def ufunc(self):

        overlap = 10
        #id_l1 = self.getVectorArray('vector', burnAttribute='ID_L1', overlap=overlap)
        #self.setArray('id_l1', array=id_l1, overlap=overlap)

        #id_l1 = self.getVectorCategoricalFractionArray('vector', burnAttribute='ID_L1', ids=[1, 2, 3], oversampling=10, overlap=overlap)
        #self.setArray('id_l1', array=id_l1, overlap=overlap)

        #id_l1 = self.getVectorCategoricalArray('vector', burnAttribute='ID_L1', ids=[1, 2, 3], oversampling=5,
        #                                       minOverallCoverage=0.9, minWinnerCoverage=0.5, noData=0, overlap=overlap)
        #self.setArray('id_l1', array=id_l1, overlap=overlap)

        id_l1 = self.getVectorProbabilityArray('vector', classes=4, burnAttribute='ID_L1', oversampling=5,
                                               minOverallCoverage=0.9, minWinnerCoverage=0.5, overlap=overlap)
        self.setArray('id_l1', array=id_l1, overlap=overlap)



if __name__ == '__main__':
    script()

