mkdir test-reports
mkdir test-reports\url-checks
urlchecker check --file-types .rst,.md,.py --save test-reports\url-checks\docs.csv doc/source
urlchecker check --file-types .rst,.md,.py --save test-reports\url-checks\enmapbox.csv --exclude-files .*\\pyqtgraph\\.* enmapbox
urlchecker check --file-types .rst,.md,.py --save test-reports\url-checks\enmapboxgeoalgorithms.csv enmapboxgeoalgorithms
urlchecker check --file-types .rst,.md,.py --save test-reports\url-checks\enmapboxprocessing.csv enmapboxprocessing
urlchecker check --file-types .rst,.md,.py --save test-reports\url-checks\hubdc.csv hubdc
urlchecker check --file-types .rst,.md,.py --save test-reports\url-checks\hubdsm.csv hubdsm
urlchecker check --file-types .rst,.md,.py --save test-reports\url-checks\hubflow.csv hubflow
