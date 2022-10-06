import pathlib
import re
import site

site.addsitedir(pathlib.Path(__file__).parents[1])

from enmapbox.gui import file_search


def create_runtests():
    DIR_SCRIPTS = pathlib.Path(__file__).resolve().parent
    DIR_REPO = DIR_SCRIPTS.parent

    # these test should be run first (fail fast)
    rxRunFirst = re.compile(r'(.*test_exampledata\.py)')

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
    test_files = []
    for DIR_TESTS in TEST_DIRECTORIES:
        for i, file in enumerate(file_search(DIR_TESTS, 'test_*.py', recursive=True)):
            file = pathlib.Path(file)
            pathTest = file.relative_to(DIR_REPO)
            test_files.append(pathTest.as_posix())
            n += 1

    test_files = sorted(test_files, key=lambda file: not rxRunFirst.search(file))

    for pathTest in test_files:
        lineSh = f'python3 -m unittest {pathTest}'
        linesSh.append(lineSh)

    # linesSh.append('python3 -m coverage report')

    print('Write {}...'.format(PATH_RUNTESTS_SH))
    with open(PATH_RUNTESTS_SH, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(linesSh))


if __name__ == "__main__":
    create_runtests()
