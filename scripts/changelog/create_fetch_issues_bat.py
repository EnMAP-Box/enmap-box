nIssues = 2000

# create fetch_issues.bat
with open('fetch_issues.bat', 'w') as file:
    for i, issue in enumerate(range(1, nIssues + 1)):
        cmd = f'gh issue view {issue} --json assignees,author,closed,closedAt,createdAt,id,labels,milestone,number,projectCards,reactionGroups,state,title,updatedAt,url '
        cmd += '>' if i == 0 else '>>'
        cmd += ' ./scripts/changelog/fetch_issues.txt\n'
        file.write(cmd)
    cmd = 'gh release list --json createdAt,isDraft,isLatest,isPrerelease,name,publishedAt,tagName >  ./scripts/changelog/fetch_releases.txt\n'
    file.write(cmd)

# init fetch_issues.txt
with open('fetch_issues.txt', 'w') as file:
    pass
