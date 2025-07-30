pushd %~dp0..\..

Rem Upgrade pip to the latest version
python -m pip install --upgrade pip

Rem Uninstall any cruft that can poison the rest of the checks in this script.
pip freeze > baseline_deps.txt
pip uninstall -y -r baseline_deps.txt
pip list
pip check
if %errorlevel% neq 0 exit /b %errorlevel%
del baseline_deps.txt

Rem Install everything from our repository first.
call .\scripts\install_full.bat
if %errorlevel% neq 0 exit /b %errorlevel%

pip check
if %errorlevel% neq 0 exit /b %errorlevel%

python -m azure.cli --version
if %errorlevel% neq 0 exit /b %errorlevel%

python -m azure.cli self-test
if %errorlevel% neq 0 exit /b %errorlevel%
popd
