import pathlib
import re
import site

site.addsitedir(pathlib.Path(__file__).parents[1])

from enmapbox.gui import file_search


def create_runtests():
    DIR_SCRIPTS = pathlib.Path(__file__).resolve().parent
    DIR_REPO = DIR_SCRIPTS.parent

    TEST_DIRECTORIES = [
        DIR_REPO / 'tests',
        DIR_REPO / 'enmapboxprocessing' / 'test',
    ]

    assert DIR_REPO.is_dir()
    assert (DIR_REPO / '.git').is_dir()

    PATH_RUNTESTS_BAT = DIR_SCRIPTS / 'runtests.bat'
    PATH_RUNTESTS_SH = DIR_SCRIPTS / 'runtests.sh'
    PATH_YAML = DIR_REPO / 'bitbucket-pipelines.yml'

    PREFACE_BAT = """
:: use this script to run unit tests locally
::
@echo off
set CI=True
set PYTHONPATH=%~dp0/..;%PYTHONPATH%
set PYTHONPATH
set PYTHON=python
::WHERE python3 >nul 2>&1 && (
::    echo Found "python3" command
::    set PYTHON=python3
::) || (
::    echo Did not found "python3" command. use "python" instead
::    set PYTHON=python
::)

::start %PYTHON% scripts/setup_repository.py
"""

    PREFACE_SH = r"""#!/bin/bash
QT_QPA_PLATFORM=offscreen
export QT_QPA_PLATFORM
CI=True
export CI

find . -name "*.pyc" -exec rm -f {} \;
export PYTHONPATH="${PYTHONPATH}:$(pwd):/usr/share/qgis/python/plugins"
# python3 scripts/setup_repository.py
"""

    # dirOut = 'test-reports/today'
    linesBat = [PREFACE_BAT]
    linesSh = [PREFACE_SH]
    linesYAML = []
    # linesBat.append('mkdir {}'.format(dirOut.replace('/', '\\')))
    # linesSh.append('mkdir {}'.format(dirOut))

    n = 0
    if True:
        for DIR_TESTS in TEST_DIRECTORIES:
            for i, file in enumerate(file_search(DIR_TESTS, 'test_*.py', recursive=True)):
                file = pathlib.Path(file)
                do_append = '' if n == 0 else '--append'
                pathTest = file.relative_to(DIR_REPO).as_posix()
                lineBat = '%PYTHON% -m coverage run --rcfile=.coveragec {}  {}'.format(do_append, pathTest)
                lineSh = 'python3 -m coverage run --rcfile=.coveragec {}  {}'.format(do_append, pathTest)
                linesBat.append(lineBat)
                linesSh.append(lineSh)
                linesYAML.append(lineSh)
                n += 1
    else:
        lineBat = '%PYTHON% -m coverage run -m unittest discover -s enmapboxtesting'
        lineSh = 'python3 -m coverage run -m unittest discover -s enmapboxtesting'
        linesBat.append(lineBat)
        linesSh.append(lineSh)
        linesYAML.append(lineSh)

    linesBat.append('%PYTHON% -m coverage report')
    linesSh.append('python3 -m coverage report')
    linesYAML.append('python3 -m coverage report')

    print('Write {}...'.format(PATH_RUNTESTS_BAT))
    with open(PATH_RUNTESTS_BAT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linesBat))

    print('Write {}...'.format(PATH_RUNTESTS_SH))
    with open(PATH_RUNTESTS_SH, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(linesSh))

    yamlLines = ['- {}\n'.format(line) for line in linesYAML]
    print(''.join(yamlLines))

    if False:
        assert PATH_YAML.is_file()
        with open(PATH_YAML, 'r') as f:
            linesYAML = f.readlines()

        startLines = []
        endLines = []

        for i, line in enumerate(linesYAML):
            if re.search(r'\W*# START UNITTESTS', line):
                startLines.insert(0, i)
            if re.search(r'\W*# END UNITTESTS', line):
                endLines.insert(0, i)

        assert len(startLines) == len(endLines)

        for (i0, ie) in zip(startLines, endLines):
            prefix = re.search(r'^.*(?=# START UNITTESTS)', linesYAML[i0]).group()
            inplace = ['{}- {}\n'.format(prefix, line) for line in linesYAML]
            linesYAML[i0 + 1:ie - 1] = inplace
        print('Update {}...'.format(PATH_YAML))
        with open(PATH_YAML, 'w', encoding='utf-8', newline='\n') as f:
            f.write(''.join(linesYAML))


if __name__ == "__main__":
    create_runtests()
    exit(0)
