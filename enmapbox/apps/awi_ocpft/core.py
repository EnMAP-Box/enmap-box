from os import makedirs
from os.path import exists


def ocpft(
    inputfile: str,
    outputDirectory: str,
    sensor: str,
    model: int,
    ac: int,
    osize: int
) -> str:
    if not exists(outputDirectory):
        makedirs(outputDirectory)

    if sensor not in ['EnMAP', 'OLCI', 'MSI', 'DESIS']:
        # , "MERIS", "MSI", "EnMAP", "SeaWiFS_OCCCI", "DESIS"]
        raise ValueError('sensor must be in ["EnMAP", "OLCI", "MSI", "DESIS"]')

    if model not in [0, 1]:
        raise ValueError('model must be in [0, 1]')

    if ac not in [0, 1]:
        # 0 = EnPT ACwater, 1 = POLYMER
        raise ValueError('ac must be in [0, 1]: 0 = EnPT ACwater, 1 = POLYMER')

    if osize not in [0]:
        raise ValueError('osize must be in [0]')
        # 0 = standard product output (7 products + bitmask) (default)

    # cmd = r'python {script} {input} -od={output} -sensor=EnMAP -model=0 -adapt=0 -osize=0'
    # cmd = r'python ocpft_v01_20220526.py /home/alvarado/projects/typsynsat/data/
    # test_dataset/olci/S3A_OL_1_EFR____20200816T095809_20200816T100109_20200816T120938_0179_061_
    # 350_2160_MAR_O_NR_002.SEN3.nc -od=output/ -sensor=OLCI -adapt=0 -ac=1 -osize=0'

    # python = abspath(sys.executable)

    # cmd = r'{python} {script} {input} -od={output} -sensor={sensor} -model={model} -ac={ac} -osize={osize}'
    # script = join(dirname(__file__), 'ocpft_v01_20220526_enmapbox.py')

    # if not os.path.isfile(script):
    #     raise FileNotFoundError(script)
    # cmd = cmd.format(python=python, script=script, input=inputfile,
    # output=outputDirectory, sensor=sensor, model=model,
    #                  ac=ac, osize=osize)
    from .ocpft_v01_20260616_enmapbox import run_processor
    cmd = f'{inputfile} -od={outputDirectory} -sensor={sensor} -model={model} -ac={ac} -osize={osize}'
    print(f'call: ocpft {cmd}')

    run_processor(cmd)

    # try:
    #     process = subprocess.run(cmd,
    #                              check=True,
    #                              shell=True,
    #                              stdout=subprocess.PIPE,
    #                              stderr=subprocess.PIPE,
    #                              universal_newlines=True)
    #     output = str(process.stdout)
    # except subprocess.CalledProcessError as ex:
    #     output = ex.stderr
    # except Exception as ex2:
    #     output = str(ex2)
    #
    return cmd
