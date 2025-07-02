import json
import warnings
from collections import defaultdict
from os.path import abspath, join

currentDevVersion = '3.17'
currentDevReleaseDate = '2024-03-21'
skipDevVersion = True

releaseHeader = {}

with open('fetch_releases.txt') as file:
    releases = json.loads(file.read())

with open('fetch_issues.txt') as file:
    issues = [json.loads(line) for line in file.readlines() if line.startswith('{')]

for issue in issues:
    issue['markdown'] = f'* {issue["title"]} [#{issue["number"]}]({issue["url"]})\n'

with open('MANUAL_EDITS.md') as file:
    text = file.read()
currentVersion = None
currentGroup = None
ApplicationGroup, AlgorithmGroup, BugGroup, MiscGroup, DataGroup, GuiGroup, CiGroup = range(7)
editedIssues = list()
for edit in text.split('\n\n'):
    lines = edit.split('\n')
    if lines[0].startswith('# Version'):
        currentVersion = lines[0].split()[-1]
        if lines[1] != '':
            releaseHeader[currentVersion] = '\n'.join(lines[1:])
        continue

    if not lines[0].startswith('* '):
        if lines[0].startswith('## New Features'):
            pass
        elif lines[0].startswith('### Applications'):
            currentGroup = ApplicationGroup
        elif lines[0].startswith('### Processing Algorithms'):
            currentGroup = AlgorithmGroup
        elif lines[0].startswith('## Fixed Bugs'):
            currentGroup = BugGroup
        elif lines[0].startswith('### Miscellaneous'):
            currentGroup = MiscGroup
        elif lines[0].startswith('### Data / Metadata Model'):
            currentGroup = DataGroup
        elif lines[0].startswith('### GUI'):
            currentGroup = GuiGroup
        elif lines[0].startswith('### Continuous Integration'):
            currentGroup = CiGroup
        else:
            raise ValueError(lines[0])
        continue

    edits2 = '\n' + '\n'.join(lines)
    for edit2 in ('\n' + edits2).split('\n* '):
        if edit2.strip() == '':
            continue
        lines = edit2.split('\n')
        title = lines[0]
        issueNumbers = [int(s[1:]) for s in title.split(' ') if s.startswith('#') and s[1:].isnumeric()]
        title = ' '.join([s for s in title.split(' ') if not (s.startswith('#') and s[1:].isnumeric())])
        if title == '$TITLE':
            assert len(issueNumbers) > 0
            for issue in issues:
                if issue.get('number') == issueNumbers[0]:
                    title = issue['title']
                    break
        editedIssues.extend(issueNumbers)
        markdownText = '* ' + title
        for number in issueNumbers:
            if number == 0:
                continue
            markdownText += f' [#{number}](https://github.com/EnMAP-Box/enmap-box/issues/{number})'
        markdownText += '\n' + '\n'.join(lines[1:]) + '\n'
        issue = {
            'title': title,
            'closed': True,
            'group': currentGroup,
            'milestone': {'title': currentVersion},
            'markdown': markdownText,
            'labels': []
        }
        issues.append(issue)

issues = [issue for issue in issues if issue.get('number') not in editedIssues]

featuresByVersion = defaultdict(list)
fixesByVersion = defaultdict(list)
for issue in issues:
    if not issue['closed']:
        continue
    if len(issue['labels']) == 0:
        if 'url' in issue:
            if '/pull/' not in issue['url']:
                warnings.warn('Closed issue has no labels: ' + issue['url'])
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

    if issue.get('group') is None:
        pass
    elif issue.get('group') == BugGroup:
        fixesByVersion[version].append(issue)
    else:
        featuresByVersion[version].append(issue)

filename = abspath(join(__file__, '../../..', 'CHANGELOG.md'))
with open(filename, 'w') as file:
    includeComment = False
    if includeComment:
        file.write(r'''
[//]: # (
Note: This file is auto-generated. All edits will be overwritten.
-----------------------
How to update this file
  1. Run create_fetch_issues_bat.py to create fetch_issues.bat.
  2. Run fetch_issues.bat from inside the EnMAP-Box Repo folder.
     E.g. D:\source\QGISPlugIns\enmap-box> .\scripts\changelog\fetch_issues.bat
     This will create two files:
       fetch_issues.txt
       fetch_releases.txt
  3. Use create_changelog.py to build the changelog.
-------------------------------
How to properly annotate issues
  The content of the changelog is generated from the GitHub issue tracker:
    - choose a meaningful issue title, it will be displayed inside the changelog
    - use Labels to place an issue inside the correct changelog section, i.e. "feature request", "bug", 'qpa",
      "application", "data/metadata", "ci"
    - issues labeled as "task" or "invalid" won't be reported
    - use Milestones to properly assign an issue to it's correct EnMAP-Box release
    - look at the current changelog for best practice examples
---------------------------
How to provide manual edits
  In some cases, you may want to provide additional information for an issue or you want to group multiple issues,
  which are related to each other. You can do this by editing the MANUAL_EDITS.md file.
)
''')
    file.write('# CHANGELOG\n')
    for version in sorted(featuresByVersion, reverse=True):
        if version == currentDevVersion:
            if skipDevVersion:
                continue
            file.write(f'## Version {version} ({currentDevReleaseDate})\n')
        else:
            releaseDate = None
            for release in releases:
                if release['tagName'] == 'v' + version + '.0':
                    releaseDate = release['publishedAt'][:10]
            if releaseDate is None:
                assert 0
            file.write(f'## Version {version} ({releaseDate})\n')
        file.write(releaseHeader[version] + '\n')
        file.write('### New Features\n')

        appFeatures = list()
        ciFeatures = list()
        dataFeatures = list()
        guiFeatures = list()
        qpaFeatures = list()
        miscFeatures = list()

        for issue in featuresByVersion[version]:
            labels = [label['name'] for label in issue['labels']]
            isMisc = True
            if 'application' in labels or 'eo4q' in labels or issue.get('group') == ApplicationGroup:
                appFeatures.append(issue)
                isMisc = False
            if 'ci' in labels or issue.get('group') == CiGroup:
                ciFeatures.append(issue)
                isMisc = False
            if 'data/metadata' in labels or issue.get('group') == DataGroup:
                dataFeatures.append(issue)
                isMisc = False
            if 'gui' in labels or issue.get('group') == GuiGroup:
                guiFeatures.append(issue)
                isMisc = False
            if 'qpa' in labels or issue.get('group') == AlgorithmGroup:
                qpaFeatures.append(issue)
                isMisc = False
            if isMisc or issue.get('group') == MiscGroup:
                miscFeatures.append(issue)

        if len(appFeatures) > 0:
            file.write('#### Applications\n')
            for issue in appFeatures:
                file.write(issue["markdown"])
        if len(ciFeatures) > 0:
            file.write('#### Continuous Integration\n')
            for issue in ciFeatures:
                file.write(issue["markdown"])
        if len(dataFeatures) > 0:
            file.write('#### Data / Metadata Model\n')
            for issue in dataFeatures:
                file.write(issue["markdown"])
        if len(guiFeatures) > 0:
            file.write('#### GUI\n')
            for issue in guiFeatures:
                file.write(issue["markdown"])
        if len(qpaFeatures) > 0:
            file.write('#### Processing Algorithms\n')
            for issue in qpaFeatures:
                file.write(issue["markdown"])
        if len(miscFeatures) > 0:
            file.write('#### Miscellaneous\n')
            for issue in miscFeatures:
                file.write(issue["markdown"])
        file.write('### Fixed Bugs\n')
        file.write(f'<details><summary>Show all ({len(fixesByVersion[version])})</summary>\n\n')
        for issue in fixesByVersion[version]:
            file.write(issue["markdown"])
        file.write('</details>\n\n')

print('done!')
