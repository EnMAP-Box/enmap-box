from os import makedirs
from os.path import exists, dirname
from typing import List

from enmapboxprocessing.rasterreader import RasterReader
from typeguard import typechecked


@typechecked
class GdalUtils(object):

    @staticmethod
    def stackVrtBands(filename: str, filenames: List[str], bandNumbers: List[int]):
        """
        Stack a list of VRT bands, given by filenames and bandNumbers, together.
        The resulting VRT stack will not dependent on the source VRT files (those may be deleted afterwards).

        It is assumed, that:
        1. all pixel grids match
        2. all source files and the destination path are located in the same folder
        """

        reader = RasterReader(filenames[0])
        extent = reader.extent()
        width = reader.width()
        height = reader.height()

        # make sure all VRTs have the same pixel grid
        for fname in filenames:
            reader = RasterReader(fname)
            if not all([
                extent == reader.extent(), width == reader.width(), height == reader.height(),
                reader.gdalDataset.GetDriver().ShortName == 'VRT'
            ]):
                raise ValueError('VRT input rasters not matching')

        # make sure all source files are located inside the same directory
        for fname in filenames:
            if dirname(fname) != dirname(filenames[0]):
                raise ValueError('all input files must be located in the same directory')

        # make sure that the destination file is located inside the same directory
        if dirname(filename) != dirname(filenames[0]):
            raise ValueError('destination file must be located in the same directory as the input files')

        # extract all VRTRasterBand blocks
        vrtRasterBands = dict()
        for fname in set(filenames):
            with open(fname) as file2:
                text = file2.read()
            text = text[text.index('<VRTRasterBand'):]
            key = '</VRTRasterBand>'
            items = text.split(key)
            items.pop(-1)
            for bandNo, item in enumerate(items, 1):
                vrtRasterBands[fname, bandNo] = item + key + '\n  '

        # write VRT stack manually
        if not exists(dirname(filename)):
            makedirs(dirname(filename))

        with open(filename, 'w') as file:
            # copy first part from first VRT
            with open(filenames[0]) as file2:
                text = file2.read()
                key = '<VRTRasterBand'
                text = text[: text.index(key)]
                text = text.split('<Metadata>')[0]  # remove all dataset-level metadata
                file.write(text)
                file.write('\n  ')

            # paste VRTRasterBand blocks
            for dstBandNo, (fname, srcBandNo) in enumerate(zip(filenames, bandNumbers), 1):
                text = vrtRasterBands[fname, srcBandNo]
                text = text.replace(f'band="{srcBandNo}"', f'band="{dstBandNo}"', )
                file.write(text)

            file.writelines(['\n</VRTDataset>'])
