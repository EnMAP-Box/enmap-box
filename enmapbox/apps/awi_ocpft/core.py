import subprocess
from os.path import join, dirname, exists, abspath
from os import makedirs

def ocpft(inputfile, outputDirectory, sensor, model, ac, osize):

    if not exists(outputDirectory):
        makedirs(outputDirectory)

    assert sensor in ['EnMAP', 'OLCI', 'MSI', 'DESIS']#, "MERIS", "MSI", "EnMAP", "SeaWiFS_OCCCI", "DESIS"]
    assert model in [0, 1]
    assert ac in [0, 1] # 0 = EnPT ACwater, 1 = POLYMER
    assert osize in [0] # 0 = standard product output (7 products + bitmask) (default)

    # cmd = r'python {script} {input} -od={output} -sensor=EnMAP -model=0 -adapt=0 -osize=0'
    #cmd = r'python ocpft_v01_20220526.py /home/alvarado/projects/typsynsat/data/test_dataset/olci/S3A_OL_1_EFR____20200816T095809_20200816T100109_20200816T120938_0179_061_350_2160_MAR_O_NR_002.SEN3.nc -od=output/ -sensor=OLCI -adapt=0 -ac=1 -osize=0'

    import sys
    python = abspath(sys.executable)

    cmd = r'{python} {script} {input} -od={output} -sensor={sensor} -model={model} -ac={ac} -osize={osize}'
    script = join(dirname(__file__), 'ocpft_v01_20220526_enmapbox.py')

    assert exists(script)
    cmd = cmd.format(python=python, script=script, input=inputfile, output=outputDirectory, sensor=sensor, model=model, ac=ac, osize=osize)
    print(cmd)
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

