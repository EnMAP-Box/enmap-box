import hzg_onns_testdata
from hzg_onns.core import onns

# onns(inputfile=r'C:\Users\Hieronym\Documents\Martin\Talks_Travel\2019_02_Berlin_EnMAP_Box\ONNSv08\Baltic_20160720_C2R_subset.nc',
#     outputfile=r'C:\Users\Hieronym\Documents\Martin\Talks_Travel\2019_02_Berlin_EnMAP_Box\ONNSv08\output\\')

onns(inputfile=hzg_onns_testdata.sylt_C1R,
     outputDirectory=r'C:\test\ONNS\test_output\\',
     sensor='OLCI',
     adapt=0,
     ac=1,
     osize=1)

#r'python C:\source\onns_for_enmap-box\hzg_onns\ONNS_v091_20190809_for_EnMAP_Box.py C:\source\onns_for_enmap-box\hzg_onns_testdata\S3A_OL_2_WFRC1R_20160720T093421_20160720T093621_20171002T063739_0119_006_307______MR1_R_NT_002_sylt.nc -od=c:\test\onns -sensor=OLCI -adapt=0 -ac=1 -osize=1 -txt_header=1 -txt_ID=1 -txt_columns 1