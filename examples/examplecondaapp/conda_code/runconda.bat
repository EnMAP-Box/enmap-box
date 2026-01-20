set pythonpath=
echo change dir
cd C:\Users\geo_beja\AppData\Local\Continuum\miniconda3\Scripts
call activate.bat 
call python -c "import sys;print('\n'.join(sys.path))"