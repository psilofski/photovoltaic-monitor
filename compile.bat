c:\python27\python.exe setup.py py2exe
pause
copy parks.csv dist\
mkdir dist\tmp
mkdir dist\data
mkdir dist\decor
mkdir dist\globals
copy decor\*.* dist\decor
copy globals\*.* dist\globals

ren dist PVmonitor-Pack


