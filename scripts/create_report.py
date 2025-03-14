"""
This scripts generates some reports stats related to the EnMAP-Box repository
"""
import argparse
import datetime
import inspect
import json
import os
import pathlib
import re
import unittest
import urllib.request
import xml.etree.ElementTree as etree
from typing import List, Dict

import pandas as pd
import requests
from qgis.PyQt.QtWidgets import QMenu
from qgis.core import QgsProcessing, QgsProcessingParameterRasterLayer, QgsProcessingParameterRasterDestination, \
    QgsProcessingOutputVectorLayer, QgsProcessingParameterFeatureSink, QgsProcessingParameterFeatureSource, \
    QgsProcessingOutputRasterLayer, QgsProcessingParameterVectorLayer, QgsProcessingParameterVectorDestination, \
    QgsProcessingParameterMapLayer, QgsProcessingParameterMultipleLayers, QgsProcessingParameterFile, \
    QgsProcessingOutputFile, QgsProcessingParameterFolderDestination, QgsProcessingOutputFolder, \
    QgsProcessingParameterFileDestination, QgsProcessingOutputHtml, QgsProcessingParameterEnum, \
    QgsProcessingParameterBoolean, QgsProcessingAlgorithm

from enmapbox import DIR_REPO_TMP
from enmapbox import initAll
from enmapbox.algorithmprovider import EnMAPBoxProcessingProvider
from enmapbox.gui.applications import ApplicationWrapper, EnMAPBoxApplication
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app


def linesOfCode(path) -> int:
    path = pathlib.Path(path)
    lines = 0
    if path.is_dir():
        for e in os.scandir(path):
            if e.is_dir():
                lines += linesOfCode(e.path)
            elif e.is_file and e.name.endswith('.py'):
                with open(e.path, 'r', encoding='utf-8') as f:
                    lines += len(f.readlines())
    return lines


def report_downloads() -> pd.DataFrame:
    url = r'https://plugins.qgis.org/plugins/enmapboxplugin'

    hdr = {'User-agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=hdr)
    response = urllib.request.urlopen(req)

    html = response.read().decode('utf-8')

    html = re.search(r'<table .*</table>', re.sub('\n', ' ', html)).group()
    html = re.sub(r'&nbsp;', '', html)
    html = re.sub(r'xmlns=".*"', '', html)
    html = re.sub(r'>&times;<', '><', html)
    tree = etree.fromstring(html)
    table = tree
    #  table = tree.find('.//table[@class="table table-striped plugins"]')
    DATA = {k: [] for k in ['version', 'minQGIS', 'experimental', 'downloads', 'uploader', 'datetime']}
    for tr in table.findall('.//tbody/tr'):
        tds = list(tr.findall('td'))
        """
        <td><a title="Version details" href="/plugins/enmapboxplugin/version/3.11.0/">3.11.0</a></td>
        <td>no</td>
        <td>3.24.0</td>
        <td>1668</td>
        <td><a href="/plugins/user/janzandr/admin">janzandr</a></td>
        <td><span class="user-timezone">2022-10-09T22:36:01.698509+00:00</span></td>
        """
        s = ""
        versionEMB = tds[0].find('.//a').text
        versionQGIS = tds[2].text
        experimental = tds[1].text.lower() == 'yes'
        downloads = int(tds[3].text)
        uploader = tds[4].find('a').text
        datetime = tds[5].find('span').text
        DATA['version'].append(versionEMB)
        DATA['minQGIS'].append(versionQGIS)
        DATA['experimental'].append(experimental)
        DATA['downloads'].append(downloads)
        DATA['datetime'].append(datetime)
        DATA['uploader'].append(uploader)

    df = pd.DataFrame.from_dict(DATA)

    df = df.query('experimental == False')
    df.sort_values(by=['datetime'], inplace=True, ascending=False)
    return df


def toDate(text, format: str = '%Y-%m-%dT%H:%M:%SZ') -> datetime.datetime:
    if isinstance(text, datetime.datetime):
        return text
    else:
        return datetime.datetime.strptime(text, format)


def report_github_issues_QGIS(authors=['jakimowb', 'janzandr'], start_date='2020-01-01',
                              end_date='2023-12-31') -> pd.DataFrame:
    """

    is:issue created:2022-07-01..2022-12-31
    is:issue closed:2022-07-01..2022-12-31
    """

    # GitHub repository owner and name
    owner = 'qgis'
    repo = 'QGIS'

    # Define the date range
    start_date = toDate(start_date, '%Y-%m-%d')
    end_date = toDate(end_date, '%Y-%m-%d')

    today = datetime.datetime.now().isoformat().split('T')[0]

    PATH_GH_JSON = pathlib.Path(__file__).parents[1] / 'tmp' / f'githubissues.{today}.QGIS.json'

    if not PATH_GH_JSON.is_file():
        os.makedirs(PATH_GH_JSON.parent, exist_ok=True)
        # Your GitHub personal access token
        assert 'GITHUB_TOKEN' in os.environ, 'GITHUB_TOKEN is not set. ' \
                                             'Read https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens for details.'
        token = os.environ['GITHUB_TOKEN']

        # Create a session and set the authorization header
        session = requests.Session()
        session.headers.update({'Authorization': f'token {token}'})

        # Get the list of issues from the GitHub API
        issues_url = f'https://api.github.com/repos/{owner}/{repo}/issues'
        params = {
            'state': 'all',  # 'all' includes open and closed issues
            'per_page': 100,  # Adjust as needed
            'creator': ','.join(authors),
        }
        all_issues = []

        n_pages = 1
        while True:
            print(f'Read page {n_pages}...')
            response = session.get(issues_url, params=params)

            response.raise_for_status()
            all_issues.extend(response.json())

            # Check if there are more pages of issues
            link_header = response.headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

            rx = re.compile(r'<(.[^>]+)>; *rel="next"')

            # Extract the URL for the next page
            link = [l.strip() for l in link_header.split(',') if 'rel="next"' in l]
            if len(link) > 0:
                link = link[0]
                issues_url = rx.match(link).group(1)
            else:
                response.close()
                break
            n_pages += 1
        with open(PATH_GH_JSON, 'w') as f:
            json.dump(all_issues, f)

    with open(PATH_GH_JSON, 'r') as f:
        all_issues = json.load(f)

    # filter by authors

    pull_requests = [i for i in all_issues if 'pull_request' in i]
    issues = [i for i in all_issues if 'pull_request' not in i]
    if True:
        for i in issues:
            if i['closed_at'] and toDate(i['closed_at']) > end_date:
                i['closed_at'] = None
            else:
                s = ""

    # Filter issues within the date range

    created_in_report_period = [i for i in issues if start_date <= toDate(i['created_at']) <= end_date]
    created_before_but_touched = [i for i in issues if toDate(i['created_at']) < start_date
                                  and start_date <= toDate(i['updated_at']) <= end_date]

    def printInfos(issues: List[dict], labels=['duplicate', 'wontfix']):
        is_closed = []
        is_open = []

        issues_by_label: Dict[str, List[dict]] = dict()
        for i in issues:
            if i['closed_at'] is None:
                is_open.append(i)
            else:
                is_closed.append(i)

            for label in i['labels']:
                n = label['name']
                issues_by_label[n] = issues_by_label.get(n, []) + [i]

        n_t = len(issues)
        print(' Total: {:3}'.format(n_t))
        if n_t > 0:
            n_o = len(is_open)
            n_c = len(is_closed)

            print('  Open: {:3} {:0.2f}%'.format(n_o, n_o / n_t * 100))
            print('Closed: {:3} {:0.2f}%'.format(n_c, n_c / n_t * 100))
            for label in labels:
                print(f' {label}: {len(issues_by_label.get(label, []))}')

    print(f'By today: {today}')
    print(f'Issues created in reporting period: {start_date} to {end_date}:')
    printInfos(created_in_report_period)

    print(f'Issues created before {start_date} but handled in reporting period:')
    printInfos(created_before_but_touched)

    print('Total:')
    printInfos(created_before_but_touched + created_in_report_period)
    return None


def report_github_issues_EnMAPBox(start_date='2020-01-01', end_date='2023-12-31') -> pd.DataFrame:
    """

    is:issue created:2022-07-01..2022-12-31
    is:issue closed:2022-07-01..2022-12-31
    """

    # GitHub repository owner and name
    owner = 'EnMAP-Box'
    repo = 'enmap-box'

    # Define the date range
    start_date = toDate(start_date, '%Y-%m-%d')
    end_date = toDate(end_date, '%Y-%m-%d')

    today = datetime.date.today()

    PATH_GH_JSON = pathlib.Path(__file__).parents[1] / 'tmp' / f'githubissues.{today.isoformat()}.json'

    if not PATH_GH_JSON.is_file():
        os.makedirs(PATH_GH_JSON.parent, exist_ok=True)
        # Your GitHub personal access token
        assert 'GITHUB_TOKEN' in os.environ, 'GITHUB_TOKEN is not set. ' \
                                             'Read https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens for details.'
        token = os.environ['GITHUB_TOKEN']

        # Create a session and set the authorization header
        session = requests.Session()
        session.headers.update({'Authorization': f'token {token}'})

        # Get the list of issues from the GitHub API
        issues_url = f'https://api.github.com/repos/{owner}/{repo}/issues'
        params = {
            'state': 'all',  # 'all' includes open and closed issues
            'per_page': 100,  # Adjust as needed
        }
        all_issues = []

        while True:
            response = session.get(issues_url, params=params)

            response.raise_for_status()
            all_issues.extend(response.json())

            # Check if there are more pages of issues
            link_header = response.headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

            rx = re.compile(r'<(.[^>]+)>; *rel="next"')

            # Extract the URL for the next page
            link = [l.strip() for l in link_header.split(',') if 'rel="next"' in l]
            if len(link) > 0:
                link = link[0]
                issues_url = rx.match(link).group(1)
            else:
                response.close()
                break
        with open(PATH_GH_JSON, 'w') as f:
            json.dump(all_issues, f)

    with open(PATH_GH_JSON, 'r') as f:
        all_issues = json.load(f)
    pull_requests = [i for i in all_issues if 'pull_request' in i]
    issues = [i for i in all_issues if 'pull_request' not in i]
    if True:
        for i in issues:
            if i['closed_at'] and toDate(i['closed_at']) > end_date:
                i['closed_at'] = None
            else:
                s = ""

    # Filter issues within the date range

    created_in_report_period = [i for i in issues if start_date <= toDate(i['created_at']) <= end_date]
    created_before_but_touched = [i for i in issues if toDate(i['created_at']) < start_date
                                  and start_date <= toDate(i['updated_at']) <= end_date]

    s = ""

    def countIssues(issues: List[dict], labels=['duplicate', 'wontfix']) -> Dict[str, int]:
        is_closed = []
        is_open = []

        issues_by_label: Dict[str, List[dict]] = dict()
        for i in issues:
            if i['closed_at'] is None:
                is_open.append(i)
            else:
                is_closed.append(i)

            for label in i['labels']:
                n = label['name']
                issues_by_label[n] = issues_by_label.get(n, []) + [i]

        infos = {'total': len(issues),
                 'open': len(is_open),
                 'closed': len(is_closed)}
        for label in labels:
            infos[label] = len(issues_by_label.get(label, []))
        return infos

    def printInfos(issues: List[dict], labels=['duplicate', 'wontfix']):
        is_closed = []
        is_open = []

        issues_by_label: Dict[str, List[dict]] = dict()
        for i in issues:
            if i['closed_at'] is None:
                is_open.append(i)
            else:
                is_closed.append(i)

            for label in i['labels']:
                n = label['name']
                issues_by_label[n] = issues_by_label.get(n, []) + [i]

        n_t = len(issues)
        n_o = len(is_open)
        n_c = len(is_closed)
        print(' Total: {:3}'.format(n_t))
        if n_t > 0:
            print('  Open: {:3} {:0.2f}%'.format(n_o, n_o / n_t * 100))
            print('Closed: {:3} {:0.2f}%'.format(n_c, n_c / n_t * 100))
            for label in labels:
                print(f' {label}: {len(issues_by_label.get(label, []))}')
        else:
            s = ""

    print(f'By today: {today}')
    print(f'Issues created in reporting period: {start_date} to {end_date}:')
    printInfos(created_in_report_period)

    print(f'Issues created before {start_date} but handled in reporting period:')
    printInfos(created_before_but_touched)

    print('Total:')
    printInfos(created_before_but_touched + created_in_report_period)

    cntP = countIssues(created_in_report_period)
    cntB = countIssues(created_before_but_touched)
    cntA = countIssues(created_in_report_period + created_before_but_touched)

    s_start_date = start_date.strftime('%d.%m.%Y')
    s_zeitraum = f"{s_start_date} - {end_date.strftime('%d.%m.%Y')}"
    LaTeX = fr"""# LaTeX CODE:
\begin{{table}}[h]
    \centering
    \begin{{tabular}}{{rc|cc|cc}}
         \multicolumn{{2}}{{c|}}{{Erstellung}} & Offen & Geschlossen & Duplikat & Ungültig/nicht behebbar \\
         \hline
        {s_zeitraum} & {cntP['total']} & {cntP['open']} & {cntP['closed']} & {cntP['duplicate']} & {cntP['wontfix']} \\
         vor {s_start_date} & {cntB['total']} & {cntB['open']} & {cntB['closed']} & {cntB['duplicate']} & {cntB['wontfix']} \\
         \hline
         Gesamt      & {cntA['total']} & {cntA['open']} & {cntA['closed']} & {cntA['duplicate']} & {cntA['wontfix']} \\
    \end{{tabular}}
    \caption{{Zusammenfassung \EnMAPBox Issue-Tracker (\url{{https://github.com/EnMAP-Box/enmap-box/issues}}), Stand {today.strftime("%d.%m.%Y")} }}
    \label{{tab:enmapbox_issues}}
\end{{table}}
"""
    print(LaTeX)
    return None


def report_EnMAPBoxApplications() -> pd.DataFrame:
    app = start_app()
    initAll()
    emb = EnMAPBox()

    DATA = {'name': [],
            'version': [],
            # 'title':[],
            'locode': [],
            'license': [],
            }

    for a in emb.applicationRegistry.applicationWrapper():
        parentMenu = QMenu()
        a: ApplicationWrapper
        app: EnMAPBoxApplication = a.app

        path = pathlib.Path(inspect.getfile(app.__class__))
        app_dir = path.parent
        # loc1 = inspect.getsourcelines(app.__class__)
        loc = linesOfCode(app_dir)
        DATA['locode'].append(loc)
        DATA['name'].append(app.name)
        DATA['version'].append(app.version)
        DATA['license'].append(app.licence)
        # DATA['title'].append(a..title())

        menu = app.menu(parentMenu)
        s = ""
    df = pd.DataFrame.from_dict(DATA)
    df.sort_values(by=['name'], inplace=True)
    return df


def report_processingalgorithms() -> pd.DataFrame:
    emb = EnMAPBox.instance()
    if not isinstance(emb, EnMAPBox):
        emb = EnMAPBox()
    provider: EnMAPBoxProcessingProvider = emb.processingProvider()

    DATA = {k: [] for k in ['group', 'name', 'in', 'out', 'id', 'description', 'help']}

    NOT_HANDLED = set()
    LUT_LAYERTYPE = {QgsProcessing.SourceType.TypeMapLayer: ['R', 'V'],
                     QgsProcessing.SourceType.TypeFile: ['F'],
                     QgsProcessing.SourceType.TypeRaster: ['R'],
                     }
    for t in [QgsProcessing.SourceType.TypeVector, QgsProcessing.SourceType.TypeVectorAnyGeometry,
              QgsProcessing.SourceType.TypeVectorPoint,
              QgsProcessing.SourceType.TypeVectorLine,
              QgsProcessing.SourceType.TypeVectorPolygon]:
        LUT_LAYERTYPE[t] = ['V']

    def dataString(parameters) -> str:
        data_sources = set()
        for p in parameters:
            if isinstance(p, (QgsProcessingParameterRasterLayer, QgsProcessingParameterRasterDestination,
                              QgsProcessingOutputRasterLayer)):
                data_sources.add('R')
            elif isinstance(p, (QgsProcessingParameterVectorLayer, QgsProcessingOutputVectorLayer,
                                QgsProcessingParameterVectorDestination,
                                QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink)):
                data_sources.add('V')
            elif isinstance(p, QgsProcessingParameterMapLayer):
                data_sources.add('V')
                data_sources.add('R')
            elif isinstance(p, QgsProcessingParameterMultipleLayers):
                t = p.layerType()
                if t in LUT_LAYERTYPE.keys():
                    data_sources.update(LUT_LAYERTYPE[t])

            elif isinstance(p, (QgsProcessingParameterFile, QgsProcessingParameterFileDestination,
                                QgsProcessingOutputFile,
                                QgsProcessingParameterFolderDestination, QgsProcessingOutputFolder)):
                data_sources.add('F')
            elif isinstance(p, (QgsProcessingOutputHtml,)):
                data_sources.add('H')
            elif isinstance(p, (QgsProcessingParameterEnum, QgsProcessingParameterBoolean)):
                pass
            else:
                NOT_HANDLED.add(p.__class__.__name__)
        return ''.join(sorted(data_sources))

    for a in provider.algorithms():
        a: QgsProcessingAlgorithm
        DATA['id'].append(a.id())
        DATA['name'].append(a.name())
        DATA['group'].append(a.group())
        DATA['description'].append(re.sub('\n', ' ', a.shortDescription()))
        DATA['help'].append(a.shortHelpString())
        DATA['in'].append(dataString(a.parameterDefinitions()))
        DATA['out'].append(dataString(a.outputDefinitions()))

    df = pd.DataFrame.from_records(DATA)
    column_order = ['group', 'name', 'in', 'out', 'description', 'id', 'help']
    df = df.reindex(columns=column_order)

    df.sort_values(by=['group', 'name'], inplace=True)

    return df


class TestCases(unittest.TestCase):

    def test_github_EnMAPBox(self):
        report_github_issues_EnMAPBox(start_date='2024-07-01', end_date='2024-12-31')

    def test_github_QGIS(self):
        report_github_issues_QGIS(authors=['jakimowb'], start_date='2024-07-01', end_date='2024-12-31')

    def test_report_downloads(self):
        df = report_downloads()
        print(df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create an EnMAP-Box report',
                                     formatter_class=argparse.RawTextHelpFormatter)
    path_xlsx = pathlib.Path(DIR_REPO_TMP) / 'enmapbox_report.xlsx'
    parser.add_argument('-f', '--filename',
                        required=False,
                        default=path_xlsx.as_posix(),
                        help=f'Filename of XLSX file to save the report. Defaults to {path_xlsx}',
                        action='store_true')

    args = parser.parse_args()
    path_xlsx = pathlib.Path(args.filename)

    app = start_app(cleanup=False)
    initAll()

    os.makedirs(path_xlsx.parent, exist_ok=True)
    with pd.ExcelWriter(path_xlsx.as_posix()) as writer:
        dfDownloads = report_downloads()
        dfDownloads.to_excel(writer, sheet_name='Downloads')

        dfApp = report_EnMAPBoxApplications()
        dfApp.to_excel(writer, sheet_name='Apps')

        dfPAs = report_processingalgorithms()
        dfPAs.to_excel(writer, sheet_name='PAs')
