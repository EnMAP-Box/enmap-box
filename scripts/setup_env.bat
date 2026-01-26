@echo off
set REPO=%~dp0..
set CI=True
set PYTHONPATH=^
%REPO%\;^
%REPO%\site-packages;^
%REPO%\tests\src;^
%PYTHONPATH%

set PYTHON=python
