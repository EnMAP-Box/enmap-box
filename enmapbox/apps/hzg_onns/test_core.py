import hzg_onns_testdata

from hzg_onns.core import onns

onns(inputfile=hzg_onns_testdata.sylt_C1R,
     outputDirectory=r'C:\test\ONNS\test_output\\',
     sensor='OLCI',
     adapt=0,
     ac=1,
     osize=1)
