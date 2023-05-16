# -*- coding: utf-8 -*-

import os
from lmuvegetationapps.Resources.Spec2Sensor.Spec2Sensor_core import *

def build_srf():
    # s2s = Spec2Sensor(sensor=None, nodat=-999)

    basepath = r'E:\Repositories\Zeugs_SRF\EnMAP/EnMAP_true/'
    #basepath = 'E:\Repositories\Zeugs_SRF\desis_rsp_60b/'
    #files = os.listdir(basepath)[1:-1]  # EnMAP Temp
    files = os.listdir(basepath)[:-1]
    print(files)
    files = [basepath + i for i in files]
    wl_file = basepath + "wavelengths.rsp"
    out_file = r"E:\Repositories\Zeugs_SRF/EnMAP_L2A_224_Bands.npz"
    # out_file = r"D:\python\EnMAPBox\enmap-box-lmu-vegetation-apps\lmuvegetationapps\srf/Sentinel2.npz"

    build_srf = BuildTrueSRF(srf_files=files, wl_file=wl_file, out_file=out_file, nodat=-999)
    return_flag, srf_list = build_srf.dframe_from_txt()

    if not return_flag:
        print(srf_list)

    _, sensor_name = build_srf.srf_from_dframe(srf_list=srf_list)

    # file_path = r'D:\python\EnMAPBox\enmap-box-lmu-vegetation-apps\lmuvegetationapps\srf\save/Fake_Sensor2.txt'
    # s2s.srf_from_txt(file_path=file_path)

def run_srf_spectra():
    # s2s = Spec2Sensor(sensor=None, nodat=-999)
    pass

def convert_image():

    in_file = r"E:\Halabuk\Preprocessed_Imagery\EnMAP\20220728_water_delete_nodat_smooth_9.bsq"
    out_file = r"E:\Halabuk\Preprocessed_Imagery\EnMAP\20220728_water_delete_nodat_smooth_9_EnMAP_resampled_noWaterV.bsq"

    s2s = Spec2Sensor(nodat=-9999, sensor='EnMAP_noWaterV_generic')
    s2s.init_sensor()
    s2s.convert_image(in_file=in_file, out_file=out_file, nodat=-9999)


if __name__ == '__main__':
    build_srf()
    # run_srf_spectra()
    # convert_image()
