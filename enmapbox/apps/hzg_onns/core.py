import subprocess
from os.path import join, dirname, exists, abspath
from os import makedirs

def onns(inputfile, outputDirectory, sensor, adapt, ac, osize):

    if not exists(outputDirectory):
        makedirs(outputDirectory)

    assert sensor in ['OLCI']#, "MERIS", "VIIRS", "MODIS", "EnMAP", "GOCI2", "OCM2", "PACE", "SeaWiFS", "SeaWiFS_OCCCI", "SGLI"]
    assert adapt in [0, 1, 2] # 0 = no band adaptation (default), 1 = only band 400nm is adapted (replaced), 2 = all bands are adapted (replaced) from MERIS input')
    assert ac in [1, 2 ,3] # 0 = InSitu (no AC applied, txt data), 1 = C2R (default), 2 = POLYMER, 3 = IPF, 4 = FUB'
    assert osize in [0, 1, 2] # 0 = standard product output (12 products + uncertainty) (default), 1 = extended processor output (+ Rrs, total IOPs, Dominance, etc), 2 = excessive processor output incl. OWT details'

    # cmd = r'python {script} {input} -od={output} -sensor=OLCI -adapt=0 -osize=0'
    # cmd = r'python ONNS_v09_20190611_for_EnMAP_Box.py S3A_OL_2_WFRC8R_20160720T093421_20160720T093621_20171002T063739_0119_006_307______MR1_R_NT_002_sylt.nc -od=output/ -sensor=OLCI -adapt=0 -ac=1 -osize=1 -txt_header=1 -txt_ID=1 -txt_columns 1'

    import os
    python = abspath(join(dirname(os.__file__), '..', 'python'))

    cmd = r'{python} {script} {input} -od={output} -sensor={sensor} -adapt={adapt} -ac={ac} -osize={osize} -txt_header=1 -txt_ID=1 -txt_columns 1'
    script = join(dirname(__file__), 'ONNS_v091_20200212_for_EnMAP_Box.py')
    assert exists(script)
    cmd = cmd.format(python=python, script=script, input=inputfile, output=outputDirectory, sensor=sensor, adapt=adapt, ac=ac, osize=osize)

    try:
        process = subprocess.run(cmd,
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True)
        output = str(process.stdout)
    except subprocess.CalledProcessError as ex:
        output = ex.stderr
    except Exception as ex2:
        output = str(ex2)

    return cmd, output
