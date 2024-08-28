import json
from os.path import abspath, join

startDate = '2024-01-01'  # inclusive
endDate = '2024-07-01'  # exclusive

with open('fetch_releases.txt') as file:
    releases = json.loads(file.read())

with open('fetch_issues.txt') as file:
    issues = [json.loads(line) for line in file.readlines() if line.startswith('{')]

features = list()
fixes = list()

for issue in issues:
    if not issue['closed']:
        continue
    if issue['closedAt'][:10] < startDate:
        continue
    if issue['closedAt'][:10] >= endDate:
        continue

    for label in issue['labels']:
        if label['name'] == 'bug':
            fixes.append(issue)
        elif label['name'] == 'feature request':
            features.append(issue)
        else:
            pass

filename = abspath(join(__file__, '../../..', 'CHANGELOG.md'))
with open('ISSUES.md', 'w') as file:
    file.write('# CHANGELOG\n')
    file.write(f'{startDate} <= closedAt < {endDate}\n')
    file.write('## New Features\n')
    for issue in features:
        file.write(f'* {issue["title"]} [#{issue["number"]}]({issue["url"]}) ({issue["closedAt"].split("T")[0]}) \n')
    file.write('## Fixed Bugs\n')
    for issue in fixes:
        file.write(f'* {issue["title"]} [#{issue["number"]}]({issue["url"]})\n')

print('done!')
