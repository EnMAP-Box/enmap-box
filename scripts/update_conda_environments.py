import datetime
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml

REPO_ROOT = Path(__file__).parents[1]
DIR_TMP = REPO_ROOT / 'tmp'
DIR_YAML = REPO_ROOT / '.env/conda'
os.makedirs(DIR_TMP, exist_ok=True)

# define how QGIS branches with be named in the yml file names
BRANCH_NAME_LOOKUP = {
    'stable': 'ltr',
    'latest': ''
}

# define packages to be installed in the different *.yml files
# only define root packages, the
DEPENDENCIES = {
    # define dependencies as: [<conda package name> | {<'conda'|'pip'>:<package name>, ...}, ...]
    # light = minimum requirements
    'light': ['python>=3.10', 'pip', 'scikit-learn>=1', 'matplotlib', 'enpt'],
    # full = all other packages to enjoy the full EnMAP-Box experience (on cost of disk space)
    'full': [{'conda': 'enpt', 'pip': 'enpt-enmapboxapp'}, 'xgboost', 'lightgbm', 'cdsapi', 'cython', 'netcdf4',
             'pygrib',
             'pyhdf', 'xarray', 'astropy', 'catboost', 'matplotlib', 'astropy', 'numba>=0.56.4',
             'sympy', 'pyopengl', 'h5py',
             # requirements by specdeepmap
             'opencv[build=headless*]', 'pandas=2.2.3',
             {'pip': ['torch==2.6.0',
                      'lightning==2.5.0.post0',
                      'tensorboard==2.19.0',
                      'torchvision==0.21.0',
                      'segmentation-models-pytorch==0.5.0']}
             ],
    # required by developers
    'dev': ['gitpython', 'git-lfs', 'pytest', 'pytest-cov', 'pytest-xdist', 'docutils',
            {'conda': 'flake8', 'pip': 'flake8-qgis'},
            ]
}

"""
  opencv[build=headless*]
  - pip:
      - flake8-qgis
      - torch==2.6.0
      - lightning==2.5.0.post0
      - tensorboard==2.19.0
      - torchvision==0.21.0
      - segmentation-models-pytorch==0.5.0
      - pandas==2.2.3

"""


def restructure_dependencies(d: dict) -> Dict[str, List[Dict[str, List[str]]]]:
    restructured = dict()
    for k, packages in d.items():
        assert isinstance(packages, list)
        packages2: List[Dict[str, List[str]]] = []
        for pkg in packages:
            if isinstance(pkg, str):
                pkg = {'conda': [pkg]}
            assert isinstance(pkg, dict)
            for repo in list(pkg.keys()):
                assert repo in ['conda', 'pip'], f'Unknown package repo: {repo}'
                repoPkgs = pkg[repo]
                if isinstance(repoPkgs, str):
                    repoPkgs = [repoPkgs]
                assert isinstance(repoPkgs, list)
                for v in repoPkgs:
                    assert isinstance(v, str)
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
    response = requests.get(base_url)
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


def get_conda_qgis_versions() -> dict:
    path_repodata = DIR_TMP / f'condaforge-repodata-{str(datetime.date.today())}.json'

    if not path_repodata.is_file():
        # osx-64
        base_url = 'https://conda.anaconda.org/conda-forge/win-64/repodata.json'
        print(f'Download {base_url}')
        response = requests.get(base_url)
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
                ltr_version: Optional[str] = None,
                all_deps: bool = False):
    variant = 'full' if all_deps else 'light'

    name = f'enmapbox_{variant}'

    if ltr_version:
        name += '_ltr'

    path_yml = dir_yaml / f'{name}.yml'

    header = f"""# EnMAP-Box conda environment (generated {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
# run to install: conda env create -n {name} --file={path_yml.name}
# run to update : conda env update -n {name} --file={path_yml.name} --prune
# run to delete : conda env remove -n {name}
# see https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file
# created with scripts/update_conda_environments.py (MANUAL CHANGES WILL BE OVERWRITTEN!)
"""
    DEPS = DEPENDENCIES['light'].copy()
    if all_deps:
        DEPS.extend(DEPENDENCIES['full'])
    DEPS.extend(DEPENDENCIES['dev'])

    variables = {
        'QT_MAC_WANTS_LAYER': 1,
        'PYQTGRAPH_QT_LIB': 'PyQt5'
    }

    deps_conda = []
    deps_pip = []

    for d in DEPS:
        d: dict
        if 'conda' in d:
            deps_conda.extend(d['conda'])

        if 'pip' in d:
            deps_pip.extend(d['pip'])

    deps_conda += sorted(set(deps_conda))
    deps_pip = sorted(set(deps_pip))

    if ltr_version:
        deps_conda.insert(0, f'qgis={ltr_version}')
    else:
        deps_conda.insert(0, 'qgis')

    environment = {
        'name': name,
        'channels': ['conda-forge'],
        'dependencies': deps_conda
    }
    if len(deps_pip) > 0:
        environment['dependencies'].append({'pip': deps_pip})

    environment['variables'] = variables

    if path_yml.is_file():
        with open(path_yml, 'r') as f:
            old_lines = f.read()
            env_old = yaml.safe_load(old_lines)
        rxVersion = re.compile(r'qgis[><=]+(?P<version>\d+\.\d+).*')
        qgis_old = None
        for d in env_old['dependencies']:
            if isinstance(d, str) and (m := rxVersion.match(d)):
                qgis_old = m.group('version')
        if qgis_old:
            archive_name = f'enmapbox_{variant}_{qgis_old}'
            old_lines = old_lines.replace(env_old['name'], archive_name)
            old_lines = old_lines.replace('qgis>=', 'qgis=')

            archive_path = dir_yaml / f'{archive_name}.yml'
            with open(archive_path, 'w') as f:
                f.write(old_lines)

    lines = yaml.dump(environment, indent=2, default_flow_style=False)

    lines = header + '\n' + lines

    with open(path_yml, 'w') as f:
        f.write(lines)


def update_yamls():
    current_versions = get_current_qgis_versions()
    conda_versions = get_conda_qgis_versions()
    s = ""

    for branch, (current_version, latest_fix) in current_versions.items():
        latest_version_fix = sorted(conda_versions, key=lambda k: [int(v) for v in k.split('.')])[-1]
        # latest_version_fix = max([v for v in conda_versions if v.startswith(current_version)])

        branch_name = BRANCH_NAME_LOOKUP.get(branch, branch)

        if branch_name == 'ltr':
            # skip the hotfix version, just use the major.minor part to
            # set the LTR version.
            ltr_version = current_version
        else:
            ltr_version = None

        update_yaml(DIR_YAML, ltr_version=ltr_version, all_deps=True)
        update_yaml(DIR_YAML, ltr_version=ltr_version, all_deps=False)


def generate_environment_file(lr_version, ltr_version):
    """
    Generates an environment.yml file to install QGIS + EnMAP-Box dependencies in a Conda environment.

    Args:
    lr_version (str): The latest version of QGIS LR.
    ltr_version (str): The latest version of QGIS LTR.

    Returns:
    str: The content of the environment.yml file as a string.
    """
    environment = {
        'name': 'qgis_env',
        'channels': ['conda-forge'],
        'dependencies': [
            'qgis=' + lr_version,
            'qgis-ltr=' + ltr_version
        ]
    }

    return yaml.dump(environment, default_flow_style=False)


if __name__ == '__main__':
    update_yamls()
