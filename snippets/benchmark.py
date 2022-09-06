import numpy as np


def ufunc():
    # generate result arrays
    ysize = 2000
    xsize = 2000
    nbands = 5
    nfiles = 5
    arrays = list()
    for i in range(nfiles):
        array = np.random.rand(nbands, ysize, xsize) * 42
        arrays.append(array)
    return arrays


t0 = np.datetime64('now')


def callbackTest():
    global t0
    from multiprocessing import Pool

    def checkpoint(msg):
        global t0
        dt = np.datetime64('now') - t0
        print('{}:{}'.format(msg, dt.astype(str)))
        t0 = np.datetime64('now')

    def callback(*args):
        print('callback called')
        # print(args)

    checkpoint('Start')
    ufunc()
    checkpoint('duration single ufunc')

    n = 10
    p = 5
    pool = Pool(p)
    for i in range(n):
        pool.apply_async(ufunc)
    pool.close()
    pool.join()
    checkpoint('duration {}x ufunc without callback')

    pool = Pool(p)
    for i in range(n):
        pool.apply_async(ufunc, callback=callback)
    pool.close()
    pool.join()
    checkpoint('duration {}x ufunc with callback')


if __name__ == '__main__':
    callbackTest()
