from _classic.hubdc import PixelGrid, Applier, ApplierOperator

def script():

    # use grid from input file, but enlarge the resolution to 300 meter
    xsize = ysize = 1000
    grid = PixelGrid(projection='EPSG:3035', xRes=1, yRes=1, xMin=0, xMax=xsize, yMin=0, yMax=ysize)
    applier = Applier(grid=grid, ufuncClass=IdleOperator, nworker=2, nwriter=1, windowxsize=256, windowysize=256)
    applier.run()

class IdleOperator(ApplierOperator):

    def ufunc(self):
        from time import sleep
        sleep(0.)

if __name__ == '__main__':
    script()
