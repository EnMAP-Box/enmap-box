import subprocess
from os.path import join, dirname, exists, abspath
from os import makedirs

def ocpft(inputfile, outputDirectory, sensor, model, ac, osize):

    if not exists(outputDirectory):
        makedirs(outputDirectory)

    assert sensor in ['EnMAP', 'OLCI', 'MSI', 'DESIS']#, "MERIS", "MSI", "EnMAP", "SeaWiFS_OCCCI", "DESIS"]
    assert model in [0, 1]
    assert ac in [0, 1], f'ac={ac}' # 0 = EnPT ACwater, 1 = POLYMER
    assert osize in [0] # 0 = standard product output (7 products + bitmask) (default)

    # cmd = r'python {script} {input} -od={output} -sensor=EnMAP -model=0 -adapt=0 -osize=0'
    # cmd = r'python ONNS_v09_20190611_for_EnMAP_Box.py S3A_OL_2_WFRC8R_20160720T093421_20160720T093621_20171002T063739_0119_006_307______MR1_R_NT_002_sylt.nc -od=output/ -sensor=OLCI -adapt=0 -ac=1 -osize=1 -txt_header=1 -txt_ID=1 -txt_columns 1'

    import os
    python = abspath(join(dirname(os.__file__), '..', 'python'))

    cmd = r'{python} {script} {input} -od={output} -sensor={sensor} -model={model} -ac={ac} -osize={osize}'
    script = join(dirname(__file__), 'ocpft_v01_20220526_enmapbox.py')
    assert exists(script)
    cmd = cmd.format(python=python, script=script, input=inputfile, output=outputDirectory, sensor=sensor, model=model, ac=ac, osize=osize)

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

