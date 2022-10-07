:: this script stats PyCharm in a requested QGIS environment
:: change the qgis-env.bat argument to qgis, qgis-dev or qgis-ltr
call "%~dp0\qgis_env.bat" qgis
start "PYCHARM" /B %PYCHARM_EXE%