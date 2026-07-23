mkdir test-reports
urlchecker check ^
    --retry-count 3 ^
    --timeout 5 ^
    --file-types .rst,.md,.py ^
    --save test-reports\url-checks.csv ^
    --exclude-files pyqtgraph ^
    --exclude-urls https://bitbucket.org/hu-geomatics/enmap-box/issues//422,http://mrcc.com/qgis.dtd ^
    --exclude-patterns type=xyz,%7Bx%7D,%7Bz%7D,%7zmin=,strict.dtd\,wfs/geometry/senstadt ^
    enmapbox
