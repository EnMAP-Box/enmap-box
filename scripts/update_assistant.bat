:: downloads the latest QGIS C++ API docs and
:: registers them to the qt assistant
curl --output qgisresources\qgis.qch --url https://api.qgis.org/api/qgis.qch
assistant -register qgisresources\qgis.qch -quiet