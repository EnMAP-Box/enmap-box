# -*- coding: utf-8 -*-
#
# Copyright © 2018 / Stéphane Guillaso
# Licensed under the terms of the 
# (see ../LICENSE.md for details)
import numpy as np
import os
import hys
import sys
import builtins
import csv

#
# Correspondance between idl and python
#
# byte           ->  1 -> np.uint8
# int            ->  2 -> np.int16
# long           ->  3 -> np.int32
# float          ->  4 -> np.float32
# double         ->  5 -> np.float64
# complex        ->  6 -> np.complex64
# double complex ->  9 -> np.complex128
# uint           -> 12 -> np.uint16
# ulong          -> 13 -> np.uint32
# long long      -> 14 -> np.int64
# u long lon     -> 15 -> np.uint64

class data:

    def __init__(self):
        self.fname = ''
        self.samples = 0
        self.lines = 0
        self.bands = 0
        self.bn = 0
        self.bs = None
        self.bp = None
        self.meta = None
    

    def reset(self):
        self.fname = ''
        self.samples = 0
        self.lines = 0
        self.bands = 0
        self.bn = 0
        self.bs = None
        self.bp = None
        self.meta = None
    

    def open(self, filename):
        msg = ""
        fname = filename
        bname = os.path.basename(fname)
        h1 = fname + ".hdr"
        h2 = (os.path.splitext(fname))[0] + ".hdr"
        
        # check if header exist
        if os.path.isfile(h1) is False and os.path.isfile(h2) is False:
            msg = bname + "\nhas no associated header file"
            return False, msg
        
        # header exist, check if the parsed file is not the header itself
        if os.path.isfile(h1): hname = h1
        else: hname = h2
        if fname == hname:
            msg = bname + "\nis a header file itself!"
            return False, msg

        # start with envi?
        f = builtins.open(hname, 'r')
        try:
            l = f.readline().strip().startswith('ENVI')
        except:
            f.close()
            msg = os.path.basename(hname) + \
                "\nis not a valid ENVI header file\n" + \
                "Check the input file!"
            return False, msg
        else:
            if not l:
                msg = os.path.basename(hname) + \
                    "\nis not an valid ENVI header file\n" + \
                    "(Missing 'ENVI' at the begining of the first line!"
                f.close()
                return False, msg

        # load the entire header
        meta = {}
        for l in f:
            if l.find('=') == -1: continue
            if l[0] == ';': continue # an IDL comment
            toto = l.strip().split(" = ", 1)
            if len(toto) != 2: continue
            key = toto[0]
            val = toto[1]
            key = key.strip().lower()
            val = val.strip()
            indLB = val.find("{")
            indRB = val.find("}")
            if indLB >= 0:
                if indRB < 0:
                    while True:
                        h = f.readline().strip()
                        if h[0] == ';': continue
                        val = val+h
                        indRB = val.find("}")
                        if indRB >= 0: break
                indLB = val.find("{")
                indRB = val.find("}")
                val = val[indLB+1:indRB].split(',')
                for k in range(len(val)): val[k] = val[k].strip()                
            meta[key] = val
        f.close()

        # check if spectral library
        ftype = meta.get('file type')
        if ftype != "ENVI Standard" and ftype != "ENVI Spectral Library" and ftype != "Spectral Library":
            msg = bname + "\ndoes not appear to be either a spectral library"+\
                " or a standard file\nCheck your file!"
            return False, msg
        
        # searching for the type of data
        # if ENVI Spectral Library: return SpectralLibrary
        # if ENVI Standard:
        #    1) If bands > 1 return cube
        #    2) If bands == 1 and data type == 2: return mask
        #    3) If bands == 1 and data type == 4: return SoilProduct
        if type(self) == hys.data:
            if ftype == "ENVI Spectral Library" or ftype == "Spectral Library":
                if meta.get('wavelength') is None:
                    msg = bname + "\nhas no 'wavelength' information\n\n" + \
                        "Check the header file"
                    return False, msg
                if len(meta.get('wavelength')) != int(meta.get('samples')):
                    msg = bname + \
                        "\nSize of wavelength is different of size of bands"+\
                        "\n\n Check your file"
                    return False, msg
                return True, hys.SpectralLibrary(fname, meta)
            
            # is it a cube?
            if int(meta.get('bands')) > 1:
                if meta.get('wavelength') is None:
                    msg = bname + "\nhas no 'wavelength' information\n\n" + \
                        "Check the header file"
                    return False, msg
                if len(meta.get('wavelength')) != int(meta.get('bands')):
                    msg = bname + \
                        "\nSize of wavelength is different of size of bands"+\
                        "\n\n Check your file"
                    return False, msg
                return True, hys.cube(fname, meta)
            
            # is it a mask ?
            if int(meta.get('data type')) == 2:
                return True, hys.mask(fname, meta)
            
            # is it a soil product
            if int(meta.get('data type')) == 4:
                return True, hys.product(fname, meta)
            
            msg = bname + "\ndoes not appear to be a valid file\n\n" + \
                "Check your input file!"
            return False, msg

        if ftype == "ENVI Spectral Library":
            if type(self) != hys.SpectralLibrary:
                msg = bname + "\nis not a spectral library!"
                return False, msg
            self.samples = 1
            self.lines = int(meta.get('lines'))
            self.bands = int(meta.get('samples'))
            self.fname = fname
            self.meta = meta
            return True, ''
        
        if type(self) == hys.SpectralLibrary:
            msg = bname + "\nis a spectral library!"
            return False, mgs
        
        bands = int(meta.get('bands'))
        if bands > 1:
            if type(self) != hys.cube:
                msg = bname + "\nis a hyperspectral image!"
                return False, msg
            if meta.get('wavelength') is None:
                msg = bname + "\nhas bands > 1 and has no 'wavelength' " + \
                    "information\n\nCheck the header file"
                return False, msg
            if len(meta.get('wavelength')) != int(meta.get('samples')):
                msg = bname + \
                    "\nSize of wavelength is different of size of bands"+\
                    "\n\n Check your file"
                return False, msg
        else:
            if type(self) == hys.cube:
                msg = bname + "\nis not a hyperspectral image!"
                return False, msg
            
        self.samples = int(meta.get('samples'))
        self.lines = int(meta.get('lines'))
        self.bands = int(meta.get('bands'))
        self.fname = fname
        self.meta = meta
        return True, ''


    def tile_data(self, block_size=512):
        self.bn = 1 # initialization
        if block_size > self.lines:
            block_size = self.lines
            block_size_last = self.lines
        else:
            pos = block_size
            while pos < self.lines:
                pos     += block_size
                self.bn += 1
                block_size_last = self.lines - (self.bn - 1) * block_size
        # define tile information
        self.bs = np.zeros(self.bn, dtype='i4') + block_size
        self.bs[-1] = block_size_last
        self.bp = np.arange(self.bn, dtype='i4') * block_size


    def read(self, BLOCK=None, tile=None):
        f = open(self.fname, 'rb')
        # get size corresponding to the type of the data
        if   self.meta.get('data type') ==  '1': tsize= 1; dtype=np.uint8
        elif self.meta.get('data type') ==  '2': tsize= 2; dtype=np.int16
        elif self.meta.get('data type') ==  '3': tsize= 4; dtype=np.int32
        elif self.meta.get('data type') ==  '4': tsize= 4; dtype=np.float32
        elif self.meta.get('data type') ==  '5': tsize= 8; dtype=np.float64
        elif self.meta.get('data type') ==  '6': tsize= 8; dtype=np.complex64
        elif self.meta.get('data type') ==  '9': tsize=16; dtype=np.complex128
        elif self.meta.get('data type') == '12': tsize= 2; dtype=np.uint16
        elif self.meta.get('data type') == '13': tsize= 4; dtype=np.uint32
        elif self.meta.get('data type') == '14': tsize= 8; dtype=np.int64
        elif self.meta.get('data type') == '15': tsize= 8; dtype=np.uint64
        else: tsize = 0
        tsize = np.int64(tsize)
        # initialize position variables
        xpos = 0
        xdim = self.samples
        ypos = 0
        ydim = self.lines
        # case tile
        if tile is not None:
            if self.bs is not None and self.bp is not None:
                ypos = self.bp[tile]
                ydim = self.bs[tile]
        elif BLOCK is not None:
            xpos = BLOCK[0]
            xdim = BLOCK[1] - BLOCK[0] + 1
            ypos = BLOCK[2]
            ydim = BLOCK[3] - BLOCK[2] + 1
        # define the pointer to start loading the data
        off = 0
        if self.meta.get('header offset'): 
            off = np.int64(self.meta['header offset'])
        pt = off + ypos * self.samples * self.bands * tsize
        # case interleave is 'bsq'
        if self.meta.get('interleave').upper() == 'BSQ':
            # im  = np.zeros((ydim, self.samples, self.bands), dtype=dtype)
            im = np.zeros((self.bands, ydim, self.samples), dtype=dtype)
            for k in range(self.bands):
                pt = off + \
                    tsize * (ypos*self.samples + k*self.lines*self.samples)
                f.seek(pt, 0)
                imk = np.fromfile(f, dtype=dtype, count=ydim*self.samples)
                # im[:,:,k] = np.reshape(imk, (ydim, self.samples))
                im[k, :, :] = np.reshape(imk, (ydim, self.samples))
            
        elif self.meta.get('interleave').upper() == 'BIL':
            f.seek(pt, 0)
            im = np.fromfile(f,dtype=dtype,count=ydim*self.samples*self.bands)
            im = np.reshape(im, (ydim, self.bands, self.samples))
            # im = np.swapaxes(im, 1, 2)
            im = np.swapaxes(im, 0, 1)
        elif self.meta.get('interleave').upper() == 'BIP':
            f.seek(pt, 0)
            im = np.fromfile(f,dtype=dtype,count=ydim*self.samples*self.bands)
            im = np.reshape(im, (ydim, self.samples, self.bands))
            im = np.swapaxes(im, 1, 2)
            im = np.swapaxes(im, 0, 1)
        f.close()
        # transform image
        if type(self) == hys.cube or type(self) == hys.SpectralLibrary:
            if   self.meta.get('data type') ==  '2': im=np.float32(im)/10000.
            elif self.meta.get('data type') == '12': im=np.float32(im)/100000.
            else: im = np.float32(im)
            ind = np.where(im < 0.0)
            if ind[0].shape[0] > 0: im[ind] = 0.0
            if type(self) == hys.SpectralLibrary:
                nx = im.shape[0]
                ny = im.shape[1]
                im = np.reshape(im, (ny, nx, 1))
                im = np.swapaxes(im, 0, 1)
        elif type(self) == hys.mask:
            ind = np.where(im != 0)
            if ind[0].shape[0] > 0: im[ind] = 1
            im = np.int32(im)
        if BLOCK is not None: im = im[:,:, xpos:xpos+xdim]
        # return the image
        return im


    def import_header(self, src):
        meta = {} # initialization of the meta dictionary
        meta["description"] = "File generated by Hysoma"
        if type(self) == hys.SpectralLibrary:
            meta["samples"]     = str(self.bands)
            meta["lines"]       = str(self.lines)
            meta["bands"]       = '1'
            meta["file type"]   = "ENVI Spectral Library"
            meta["data type"]   = '4'
        else:
            meta["samples"]     = str(self.samples)
            meta["lines"]       = str(self.lines)
            meta["bands"]       = str(self.bands)
            meta["file type"]   = "ENVI Standard"
            if type(self) == hys.mask: meta["data type"] = '2'
            else: meta["data type"] = '4'
        meta["header offset"] = '0'
        meta["interleave"]    = "bsq"
        meta["byte order"]    = '0'
        # define tags to be imported from a source file
        tags = ["sensor type", "x start", "y start", "map info", 
            "coordinate system string", "projection info"]
        # add specific tag if created file is a spectral library
        if type(self) == hys.SpectralLibrary:
            tags += ["wavelength units", "z plot titles", "band names", 
                "spectra names", "wavelength", "fwhm", "bbl", 
                "data gain values", "data offset values", "default bands"]
        # import the tag
        for tag in tags:
            txt = src.meta.get(tag)
            if txt: meta[tag] = src.meta.get(tag)
        self.meta = meta


    def write_header(self):
        f = builtins.open(self.fname + ".hdr", 'w')
        f.write('ENVI\n')
        # f.write('description = File generated by Hysoma\n')
        # write standard parameters
        tags = ['description', 'samples', 'lines', 'bands', 'header offset', 'file type', 
            'data type', 'interleave', 'sensor type', 'byte order', 'map info']
        for tag in tags:
            if tag in self.meta:
                val = self.meta[tag]
                if type(val) is list: 
                    val = '{%s}' % (', '.join(str(v) for v in val))
                f.write('%s = %s\n' % (tag, val))
        for tag in self.meta:
            if tag not in tags:
                val = self.meta[tag]
                if type(val) is list:
                    val = '{%s}' % (', '.join(str(v) for v in val))
                f.write('%s = %s\n' % (tag, val))
        f.close()


    def write(self, im, tile=None):
        if os.path.isfile(self.fname): f = open(self.fname, 'r+b')
        else: f = open(self.fname, 'wb')
        # get size corresponding to the type of the data
        if   self.meta.get('data type') ==  '1': tsize= 1; dtype=np.uint8
        elif self.meta.get('data type') ==  '2': tsize= 2; dtype=np.int16
        elif self.meta.get('data type') ==  '3': tsize= 4; dtype=np.int32
        elif self.meta.get('data type') ==  '4': tsize= 4; dtype=np.float32
        elif self.meta.get('data type') ==  '5': tsize= 8; dtype=np.float64
        elif self.meta.get('data type') ==  '6': tsize= 8; dtype=np.complex64
        elif self.meta.get('data type') ==  '9': tsize=16; dtype=np.complex128
        elif self.meta.get('data type') == '12': tsize= 2; dtype=np.uint16
        elif self.meta.get('data type') == '13': tsize= 4; dtype=np.uint32
        elif self.meta.get('data type') == '14': tsize= 8; dtype=np.int64
        elif self.meta.get('data type') == '15': tsize= 8; dtype=np.uint64
        else: tsize = 0
        tsize = np.int64(tsize)
        # initialize position variables
        ypos = 0
        ydim = self.lines
        # case tile
        if tile is not None:
            if self.bs is not None and self.bp is not None:
                ypos = self.bp[tile]
                ydim = self.bs[tile]
        pos = ypos * self.samples
        pt = tsize * pos
        f.seek(pt, 0)
        im.tofile(f)
        f.close()


    def select_bands(self, bands):
        
        # get number of input band
        bands = np.float32(bands)
        n = np.size(bands)

        # initialize output to -1
        out = np.zeros(n, dtype='i4') - 1
        
        # transform input bands into micrometer
        ind = np.where(bands > 100)
        if np.size(ind[0]) > 0: bands /= 1000.
        
        # get wavelength
        wvl = np.asarray(self.meta.get("wavelength"), dtype=np.float32)
        ind = np.where(wvl > 100)
        if np.size(ind[0]) > 0:
            wvl /= 1000.
        
        # get bbl
        bbl = self.meta.get("bbl")
        if bbl is not None: bbl = np.asarray(bbl, dtype=np.int)
        else: bbl = np.ones(self.bands, dtype=np.int)
        
        # get band indices
        bind = np.arange(self.bands, dtype=np.int)
        
        # remove bad band
        ind = np.where(bbl == 1)
        if np.size(ind[0]) == 0: 
            return out, False
        wvl = wvl[ind]
        bind = bind[ind]

        # look for the closest bands (nearest neighbour)
        for k in np.arange(np.size(bands)):
            tmp = np.abs(wvl - bands[k])
            ind = np.where(tmp  == tmp.min())
            if np.size(ind[0]) == 0: continue
            out[k] = bind[ind[0][0]]
        
        # check if search band failed
        ind = np.where(out == -1)
        if np.size(ind[0]) != 0:
            return out, False

        # check that we have unique band
        tmp = np.unique(out)
        if np.size(tmp) <= 1: 
            return out * 0 - 1, False

        # we pass all test, everything ok
        return out, True





###############################################################################
###############################################################################
###############################################################################





class cube(data):

    def __init__(self, fname, meta):
        data.__init__(self)
        self.fname = fname
        self.meta = meta
        self.samples = int(self.meta.get('samples'))
        self.lines   = int(self.meta.get('lines'))
        self.bands   = int(self.meta.get('bands'))
    
    def get_info(self):
        txt = 'Hyperspectral Image (Samples: ' + str(self.samples) + \
            ', Lines: ' + str(self.lines) + ', Bands: ' + str(self.bands) + ')'
        return txt





###############################################################################
###############################################################################
###############################################################################





class SpectralLibrary(data):

    def __init__(self, fname=None, meta=None):
        data.__init__(self)
        if fname: self.fname = fname
        if meta: 
            self.meta = meta
            self.samples = 1
            self.lines   = int(self.meta.get('lines'))
            self.bands   = int(self.meta.get('samples'))


    def get_info(self):
        txt = 'Hyperspectral Spectral Library (Lines: ' + \
            str(self.lines) + ', Bands: ' + str(self.bands) + ')'
        return txt


    def tile_data(self):
        self.bn = 1
        self.bs = np.asarray([self.lines], dtype='i4')
        self.bp = np.zeros(1, dtype='i4')
        return




###############################################################################
###############################################################################
###############################################################################





class mask(data):

    def __init__(self, fname=None, meta=None, src=None, tile=False):
        data.__init__(self)
        if fname: self.fname = fname
        if meta: 
            self.meta = meta
            self.samples = int(self.meta.get('samples'))
            self.lines   = int(self.meta.get('lines'))
            self.bands   = int(self.meta.get('bands'))
        if src:
            self.samples = int(src.meta.get('samples'))
            self.lines   = int(src.meta.get('lines'))
            self.bands   = 1
            self.import_header(src=src)
            if self.fname != '': self.write_header()
            if tile: self.tile_data()
            return





###############################################################################
###############################################################################
###############################################################################





class product(data):

    def __init__(self, fname=None, meta=None, src=None, tile=False):
        data.__init__(self)
        if fname: self.fname = fname
        if meta: 
            self.meta = meta
            self.samples = int(self.meta.get('samples'))
            self.lines   = int(self.meta.get('lines'))
            self.bands   = int(self.meta.get('bands'))
        if src:
            self.samples = int(src.samples)
            self.lines   = int(src.lines)
            # self.samples = int(src.meta.get('samples'))
            # self.lines   = int(src.meta.get('lines'))
            self.bands   = 1
            self.import_header(src=src)
            self.meta['data ignore value'] = '-9999.0'
            if self.fname != '': self.write_header()
            if tile: self.tile_data()
            return
    
    def get_info(self):
        txt = 'Soil product (Samples: ' + str(self.samples) + ', Lines: ' + str(self.lines) +  ')'
        return txt



class CSV_DATA(object):

    def __init__(self):
        self.fname = None
        self.delimiter = ','
        self.rows = []
        self.hrows = []
        self.n_header = 0
        self.n_rows = None
        self.n_cols = None
        self.coordinates = 1 # geographical (False is image)
    
    def load(self, filename=None):
        if filename is not None:
            self.fname = filename
        if self.fname == None:
            return
        self.rows = []
        self.hrows = []
        with open (self.fname, newline='') as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            kk = 0
            # for k in range(self.n_header):
            #     next(reader)
            for row in reader:
                if kk < self.n_header:
                    self.hrows = row
                else:
                    self.rows.append(row)
                kk = kk + 1
        f.close()
        self.n_rows = len(self.rows)
        self.n_cols = len(self.rows[0])
    
    def copy_from(self, src):
        self.fname       = src.fname
        self.delimiter   = src.delimiter
        self.rows        = src.rows
        self.hrows       = src.hrows
        self.n_header    = src.n_header
        self.n_rows      = src.n_rows
        self.n_cols      = src.n_cols
        self.coordinates = src.coordinates


    def reset(self):
        self.fname       = None
        self.delimiter   = ','
        self.rows        = []
        self.hrows       = []
        self.n_header    = 0
        self.n_rows      = None
        self.n_cols      = None
        self.coordinates = 1
    
    def set_delimiter(self, delimiter):
        self.delimiter = delimiter
    
    def set_n_header(self, val):
        self.n_header = val
    
    def set_coordinates(self, val):
        self.coordinates = val





