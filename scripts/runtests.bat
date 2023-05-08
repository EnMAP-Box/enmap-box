@echo off
set QT_QPA_PLATFORM=offscreen
set CI=True

rmdir /s /q test-outputs
rmdir /s /q test-reports

set PYTHONPATH=%PYTHONPATH%;^
%cd%\enmapbox\apps;^
%cd%\enmapbox\coreapps;^
%cd%\enmapbox\eo4qapps;^
%cd%\tests\src

::echo %PYTHONPATH%
::echo %CD%
pytest --no-cov-on-fail --cov-config=%CD%\.coveragec
