import json
from collections import defaultdict
from os.path import abspath, join

currentDevVersion = '3.15'
skipDevVersion = True

releaseHeader = {
    '3.14': 'This release was tested under QGIS 3.34 (LTR) and 3.36 (latest release).',
    '3.13': 'This release was tested under QGIS 3.28 (LTR), 3.32 and 3.34 (latest release).',
    '3.12': 'This release was tested under QGIS 3.28 (LTR).',
    '3.11': 'This release was tested under QGIS 3.26.'
}

with open('fetch_releases.txt') as file:
    releases = json.loads(file.read())

with open('fetch_issues.txt') as file:
    issues = [json.loads(line) for line in file.readlines() if line.startswith('{')]

featuresByVersion = defaultdict(list)
fixesByVersion = defaultdict(list)
for issue in issues:
    if not issue['closed']:
        continue
    if issue['milestone'] is None:
        continue
    milestone = issue['milestone']['title']

    try:
        major, minor, *_ = milestone.split('.')
        minor, *_ = minor.split(' ')
    except ValueError:
        continue
    version = major + '.' + minor

    for label in issue['labels']:
        if label['name'] == 'bug':
            fixesByVersion[version].append(issue)
        elif label['name'] == 'feature request':
            featuresByVersion[version].append(issue)
        else:
            pass

filename = abspath(join(__file__, '../../..', 'CHANGELOG.md'))
with open(filename, 'w') as file:
    file.write('# CHANGELOG\n')
    for version in sorted(featuresByVersion, reverse=True):
        if version == currentDevVersion:
            if skipDevVersion:
                continue
            file.write(f'## Version {version} (DEV)\n')
        else:
            releaseDate = None
            for release in releases:
                if release['tagName'] == 'v' + version + '.0':
                    releaseDate = release['publishedAt'][:10]
            assert releaseDate is not None
            file.write(f'## Version {version} ({releaseDate})\n')
        file.write(f'_{releaseHeader[version]}_\n')
        file.write('### New Features\n')

        appFeatures = list()
        ciFeatures = list()
        dataFeatures = list()
        guiFeatures = list()
        qpaFeatures = list()
        miscFeatures = list()

        for issue in featuresByVersion[version]:
            labels = [label['name'] for label in issue['labels']]
            if 'application' in labels or 'eo4q' in labels:
                appFeatures.append(issue)
            elif 'ci' in labels:
                ciFeatures.append(issue)
            elif 'data/metadata' in labels:
                dataFeatures.append(issue)
            elif 'gui' in labels:
                guiFeatures.append(issue)
            elif 'qpa' in labels:
                qpaFeatures.append(issue)
            else:
                miscFeatures.append(issue)

        if len(appFeatures) > 0:
            file.write('#### Applications\n')
            for issue in appFeatures:
                file.write(f'* {issue["title"]} [#{issue["number"]}]({issue["url"]})\n')
        if len(ciFeatures) > 0:
            file.write('#### Continuous Integration\n')
            for issue in ciFeatures:
                file.write(f'* {issue["title"]} [#{issue["number"]}]({issue["url"]})\n')
        if len(dataFeatures) > 0:
            file.write('#### Data / Metadata Model\n')
            for issue in dataFeatures:
                file.write(f'* {issue["title"]} [#{issue["number"]}]({issue["url"]})\n')
        if len(guiFeatures) > 0:
            file.write('#### GUI\n')
            for issue in guiFeatures:
                file.write(f'* {issue["title"]} [#{issue["number"]}]({issue["url"]})\n')
        if len(qpaFeatures) > 0:
            file.write('#### Processing Algorithms\n')
            for issue in qpaFeatures:
                file.write(f'* {issue["title"]} [#{issue["number"]}]({issue["url"]})\n')
        if len(miscFeatures) > 0:
            file.write('#### Miscellaneous\n')
            for issue in miscFeatures:
                file.write(f'* {issue["title"]} [#{issue["number"]}]({issue["url"]})\n')

        file.write('### Fixed Bugs\n')
        file.write('<details><summary>Show all</summary>\n\n')
        for issue in fixesByVersion[version]:
            file.write(f'* {issue["title"]} [#{issue["number"]}]({issue["url"]})\n')
        file.write('</details>\n\n')

print('done!')
