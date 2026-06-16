import os
import subprocess
from os import makedirs
from os.path import join, dirname, exists, abspath


def onns(inputfile, outputDirectory, sensor, adapt, ac, osize):
    if not exists(outputDirectory):
        makedirs(outputDirectory)

    # "MERIS", "VIIRS", "MODIS", "EnMAP", "GOCI2", "OCM2", "PACE", "SeaWiFS", "SeaWiFS_OCCCI", "SGLI"]
    assert sensor in ['OLCI']
    # 0 = no band adaptation (default), 1 = only band 400nm is adapted (replaced), 2 = all bands are adapted
    # (replaced) from MERIS input')
    assert adapt in [0, 1, 2]
    # 0 = InSitu (no AC applied, txt data), 1 = C2R (default), 2 = POLYMER, 3 = IPF, 4 = FUB'
    assert ac in [1, 2, 3]
    # 0 = standard product output (12 products + uncertainty) (default), 1 = extended processor output
    # (+ Rrs, total IOPs, Dominance, etc), 2 = excessive processor output incl. OWT details'
    assert osize in [0, 1, 2]

    python = abspath(join(dirname(os.__file__), '..', 'python'))

    cmd = (r'{python} {script} {input} -od={output} -sensor={sensor} -adapt={adapt} -ac={ac} -osize={osize} '
           r'-txt_header=1 -txt_ID=1 -txt_columns 1')
    script = join(dirname(__file__), 'ONNS_v091_20200212_for_EnMAP_Box.py')
    assert exists(script)
    cmd = cmd.format(python=python, script=script, input=inputfile, output=outputDirectory, sensor=sensor, adapt=adapt,
                     ac=ac, osize=osize)

    try:
        process = subprocess.run(
            cmd,
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        output = str(process.stdout)
    except subprocess.CalledProcessError as ex:
        output = ex.stderr
    except Exception as ex2:
        output = str(ex2)

    return cmd, output
