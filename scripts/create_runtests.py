import pathlib
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

    PATH_RUNTESTS_SH = DIR_SCRIPTS / 'runtests.sh'

    PREFACE_SH = r"""#!/bin/bash
QT_QPA_PLATFORM=offscreen
export QT_QPA_PLATFORM
CI=True
export CI

find . -name "*.pyc" -exec rm -f {} \;
export PYTHONPATH="${PYTHONPATH}:$(pwd):/usr/share/qgis/python/plugins"
# python3 scripts/setup_repository.py
"""

    linesSh = [PREFACE_SH]

    n = 0
    if True:
        for DIR_TESTS in TEST_DIRECTORIES:
            for i, file in enumerate(file_search(DIR_TESTS, 'test_*.py', recursive=True)):
                file = pathlib.Path(file)
                do_append = '' if n == 0 else '--append'
                pathTest = file.relative_to(DIR_REPO).as_posix()
                # lineSh = 'python3 -m coverage run --rcfile=.coveragec {}  {}'.format(do_append, pathTest)
                lineSh = f'python3 -m {pathTest}'
                linesSh.append(lineSh)
                n += 1
    else:
        lineSh = 'python3 -m coverage run -m unittest discover -s enmapboxtesting'
        linesSh.append(lineSh)

    linesSh.append('python3 -m coverage report')

    print('Write {}...'.format(PATH_RUNTESTS_SH))
    with open(PATH_RUNTESTS_SH, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(linesSh))


if __name__ == "__main__":
    create_runtests()
    exit(0)
