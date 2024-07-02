nIssues = 1000

# create fetch_issues.bat
with open('fetch_issues.bat', 'w') as file:
    for issue in range(1, nIssues + 1):
        cmd = f'gh issue view {issue} --json assignees,author,closed,closedAt,createdAt,id,labels,milestone,number,projectCards,reactionGroups,state,title,updatedAt,url >> ./scripts/changelog/fetch_issues.txt\n'
        file.write(cmd)
    cmd = 'gh release list --json createdAt,isDraft,isLatest,isPrerelease,name,publishedAt,tagName >  ./scripts/changelog/fetch_releases.txt\n'
    file.write(cmd)

# init fetch_issues.txt
with open('fetch_issues.txt', 'w') as file:
    pass

# ... manually execute fetch_issues.bat from inside the EnMAP-Box Repo folder
# e.g. D:\source\QGISPlugIns\enmap-box> .\scripts\changelog\fetch_issues.bat
