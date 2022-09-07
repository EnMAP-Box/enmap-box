import csv
import datetime
import json
import os
import pathlib
import re

from xlsxwriter.workbook import Workbook

# import pandas as pd
"""
Syntax github issue request:
https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests

author:jakimowb type:issue created:>=2022-07-01 created:<=2022-12-31

"""
# 1. open bitbucket,
# goto repository settings -> issues -> Import & export
# 2. export issues, extract zip file and copy db-2.0.json to JSON_DIR (defaults to <repo>/tmp)
# 3. set report period with start_date / end_date
JSON_DIR = pathlib.Path(__file__).parents[1] / 'tmp'
start_date = datetime.date(2022, 1, 1)
end_date = datetime.date(2022, 6, 30)

PATH_DB_JSON = JSON_DIR / 'db-2.0.json'
PATH_CSV_REPORT = JSON_DIR / f'issue_report_{start_date}_{end_date}.csv'
assert PATH_DB_JSON.is_file(), 'No db-2.0.json, no stats!'
assert start_date < end_date


def csv2xlsx(path_csv):
    path_csv = pathlib.Path(path_csv)
    path_xlsx = path_csv.parent / f'{os.path.splitext(path_csv.name)[0]}.xlsx'
    workbook = Workbook(path_xlsx)
    # float_format = workbook.add_format({'num_format': ''})
    worksheet = workbook.add_worksheet()
    rxIsInt = re.compile(r'^\d+$')
    rxIsFloat = re.compile(r'^\d+([.,]\d*)?$')
    with open(path_csv, 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                if rxIsInt.match(col):
                    col = int(col)
                elif rxIsFloat.match(col):
                    col = float(col)
                worksheet.write(r, c, col)
    workbook.close()


with open(PATH_DB_JSON, 'r', encoding='utf-8') as f:
    DB = json.load(f)

# DS = pd.read_json(PATH_DB_JSON.as_posix())
ISSUES = DB['issues']

CREATED_ISSUES = [i for i in ISSUES if start_date
                  <= datetime.datetime.fromisoformat(i['created_on']).date()
                  <= end_date]
UPDATED_ISSUES = [i for i in ISSUES if start_date
                  <= datetime.datetime.fromisoformat(i['updated_on']).date()
                  <= end_date]


def byKey(ISSUES: list, key: str) -> dict:
    R = dict()
    for issue in ISSUES:
        k = issue[key]
        L = R.get(k, [])
        L.append(issue)
        R[k] = L
    return R


CREATED_BY_STATUS = byKey(CREATED_ISSUES, 'status')
UPDATED_BY_STATUS = byKey(UPDATED_ISSUES, 'status')

print(f'Created: {len(CREATED_ISSUES)}')
for k in sorted(CREATED_BY_STATUS.keys()):
    print(f'\t{k}: {len(CREATED_BY_STATUS[k])}')

print(f'Updated: {len(UPDATED_ISSUES)}')
for k in sorted(UPDATED_BY_STATUS.keys()):
    print(f'\t{k}: {len(UPDATED_BY_STATUS[k])}')

with open(PATH_CSV_REPORT, 'w', encoding='utf-8', newline='') as f:
    states = ['new', 'open', 'on hold', 'resolved', 'closed', 'duplicate', 'wontfix', 'invalid']
    fieldnames = ['action', 'total'] + states
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    total_created = total_updated = 0
    ROW1 = {'action': 'created'}
    ROW2 = {'action': 'updated'}

    for s in states:
        total_created += len(CREATED_BY_STATUS.get(s, []))
        total_updated += len(UPDATED_BY_STATUS.get(s, []))
        ROW1[s] = len(CREATED_BY_STATUS.get(s, []))
        ROW2[s] = len(UPDATED_BY_STATUS.get(s, []))
    ROW1['total'] = total_created
    ROW2['total'] = total_updated
    writer.writerow(ROW1)
    writer.writerow(ROW2)

csv2xlsx(PATH_CSV_REPORT)
