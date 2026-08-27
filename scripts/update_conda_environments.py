import datetime
import json
import os
import re
from pathlib import Path
from typing import Dict, List

import requests
import yaml

REPO_ROOT = Path(__file__).parents[1]
DIR_TMP = REPO_ROOT / 'tmp'
DIR_YAML = REPO_ROOT / '.env/conda'
os.makedirs(DIR_TMP, exist_ok=True)

# QGIS conda versions that are known to have problems
# e.g., https://github.com/conda-forge/qgis-feedstock/issues/570
EXCLUDED_QGIS_VERSIONS = []

# define packages to be installed in the different *.yml files
# compare with .env/requirements.csv
# only define root packages, the
DEPENDENCIES = {
    # define dependencies as: [<conda package name> | {<'conda'|'pip'>:<package name>, ...}, ...]
    # light = minimum requirements
    'base': ['qgis<=3.99',
             'python>=3.12',
             'pip',
             'scikit-learn>=1.4',
             'skops',
             'matplotlib-base',
             'defusedxml',
             'pyqtgraph',
             'colorama'],
    # full = all other packages to enjoy the full EnMAP-Box experience (on cost of disk space)
    'full': ['enpt>=1.2.1',
             'enpt_enmapboxapp>=1.0.2',
             'enfrosp',
             'enfrosp_enmapboxapp',
             'xgboost',
             'lightgbm',

             # 'cdsapi', 'cython', 'pyhdf', 'xarray', 'pygrib',
             'netcdf4',
             'catboost',
             'astropy-base',
             'numba>=0.56.4',
             'sympy', 'pyopengl', 'h5py',
             # requirements by specdeepmap
             'opencv[build=headless*]', 'pandas',
             # requirements by specdeepmap
             'lightning',
             'pytorch',
             'tensorboard',
             'torchvision',
             'segmentation-models-pytorch',
             'setuptools<=81',  # due to https://github.com/tensorflow/tensorboard/issues/7003
             'pyvista',  # required by Spectral Surface Plotting
             'pyvistaqt'  # required by Spectral Surface Plotting

             # {'pip': ['torch==2.6.0',
             #         'lightning==2.5.0.post0',
             #         'tensorboard==2.19.0',
             #         'torchvision==0.21.0',
             #         'segmentation-models-pytorch==0.5.0']}
             ],
    # required by developers
    'dev': ['gitpython', 'git-lfs', 'pytest', 'pytest-cov', 'pytest-xdist', 'docutils',
            'flake8',
            'bandit',
            {'pip': 'flake8-qgis'},
            ]
}


def restructure_dependencies(d: dict) -> Dict[str, List[Dict[str, List[str]]]]:
    restructured = dict()
    for k, packages in d.items():
        packages2: List[Dict[str, List[str]]] = []
        for pkg in packages:
            if isinstance(pkg, str):
                pkg = {'conda': [pkg]}
            if not isinstance(pkg, dict):
                raise ValueError(f'Invalid package dict: {pkg}')
            for repo in list(pkg.keys()):
                if repo not in ['conda', 'pip']:
                    raise ValueError(f'Package repo must be conda or pip: {repo}')
                repoPkgs = pkg[repo]
                if isinstance(repoPkgs, str):
                    repoPkgs = [repoPkgs]
                if not isinstance(repoPkgs, list):
                    raise ValueError(f'Invalid package list: {repoPkgs}')
                for v in repoPkgs:
                    if not isinstance(v, str):
                        raise ValueError(f'Invalid package: {v}')
                pkg[repo] = repoPkgs
            packages2.append(pkg)
        restructured[k] = packages2
    return restructured


DEPENDENCIES = restructure_dependencies(DEPENDENCIES)


def get_current_qgis_versions() -> dict:
    """
    Reads from qgis.org the version numbers of the current LTR and LR releases.
    """
    base_url = 'https://qgis.org/resources/roadmap'
    response = requests.get(base_url, timeout=10)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch data from {base_url}")

    html = response.text
    rxVersions = re.compile(
        r'<span class=(?P<branch>latest|stable)>Current: (?P<version>\d+\.\d+)\.(?P<bugfix>\d+)</span>')

    VERSIONS = dict()
    for m in rxVersions.findall(html):
        branch, version, bugfix = m
        VERSIONS[branch] = (version, bugfix)
    return VERSIONS


def get_conda_qgis_versions() -> List[str]:
    path_repodata = DIR_TMP / f'condaforge-repodata-{str(datetime.date.today())}.json'

    if not path_repodata.is_file():
        # osx-64
        base_url = 'https://conda.anaconda.org/conda-forge/win-64/repodata.json'
        print(f'Download {base_url}')
        response = requests.get(base_url, timeout=5)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch data from {base_url}")

        # Parse the JSON response to get all package data
        repodata = response.json()
        with open(path_repodata, 'w') as f:
            json.dump(repodata, f)

    print(f'Read {path_repodata}')
    with open(path_repodata, 'r') as f:
        repodata = json.load(f)
    # qgis-3.36.0-py310h6577e97_1.conda
    rxPkg = re.compile(r'qgis-\d+\.\d+\.\d+-.+')
    qgis_builds = []
    qgis_builds += [v for k, v in repodata['packages'].items() if rxPkg.match(k)]
    qgis_builds += [v for k, v in repodata['packages.conda'].items() if rxPkg.match(k)]
    qgis_versions = sorted(set([build['version'] for build in qgis_builds]))

    return qgis_versions


def update_yaml(dir_yaml,
                name: str,
                dependencies: List[str]):
    path_yml = dir_yaml / f'{name}.yml'

    header = f"""# EnMAP-Box conda environment (generated {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
# run to install: conda env create -n {name} --file={path_yml.name}
# run to update: conda env update -n {name} --file={path_yml.name} --prune
# run to delete: conda env remove -n {name}
# see https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#
# creating-an-environment-from-an-environment-yml-file
# created with scripts/update_conda_environments.py (MANUAL CHANGES WILL BE OVERWRITTEN!)
"""
    DEPS = []
    for d in dependencies:
        DEPS.extend(DEPENDENCIES[d])

    deps_conda = []
    deps_pip = []

    for d in DEPS:
        d: dict
        if 'conda' in d:
            deps_conda.extend(d['conda'])

        if 'pip' in d:
            deps_pip.extend(d['pip'])

    deps_conda = list(sorted(set(deps_conda)))
    deps_pip = list(sorted(set(deps_pip)))

    environment = {
        'name': name,
        'channels': ['conda-forge'],
        'dependencies': deps_conda
    }
    if len(deps_pip) > 0:
        environment['dependencies'].append({'pip': deps_pip})

    QT_LIB = 'PyQt6'
    for d in environment['dependencies']:
        if isinstance(d, str) and re.search(r'qgis[<>=]+3\..*', d):
            QT_LIB = 'PyQt5'

    variables = {
        'QT_MAC_WANTS_LAYER': 1,
        'PYQTGRAPH_QT_LIB': QT_LIB
    }
    environment['variables'] = variables

    lines = yaml.dump(environment, indent=2, default_flow_style=False)

    lines = header + '\n' + lines

    with open(path_yml, 'w') as f:
        f.write(lines)


def update_yamls():
    current_versions = get_current_qgis_versions()
    conda_versions = get_conda_qgis_versions()
    print(current_versions, conda_versions)
    update_yaml(DIR_YAML, 'enmapbox-base', dependencies=['base', 'dev'])
    update_yaml(DIR_YAML, 'enmapbox-full', dependencies=['base', 'full', 'dev'])


if __name__ == '__main__':
    update_yamls()
