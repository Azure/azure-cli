@echo off
SetLocal EnableDelayedExpansion
echo.

set "PATH=%PATH%;%ProgramFiles%\Git\bin;%ProgramFiles%\Git\usr\bin;C:\Program Files (x86)\Git\bin;"

set ARTIFACTS_DIR=%~dp0..\artifacts
mkdir %ARTIFACTS_DIR%
set PYTHON_VENV_PYINSTALLER_DIR=%ARTIFACTS_DIR%\pyinstaller_venv
set PYTHON_VENV_SOURCE_DIR=%ARTIFACTS_DIR%\source_venv
set PYINSTXTRACTOR_DIR=%ARTIFACTS_DIR%\pyinstxtractor
set PYINSTALLER_EXTRACTED_DIR=%ARTIFACTS_DIR%\pyinstaller_extracted

set REPO_ROOT=%~dp0..\..\..
set CLI_SRC=%REPO_ROOT%\src

::reset pyinstxtractor folders
if exist %PYINSTXTRACTOR_DIR% rmdir /s /q %PYINSTXTRACTOR_DIR%
::rmdir always returns 0, so check folder's existence
if exist %PYINSTXTRACTOR_DIR% (
    echo Failed to delete %PYINSTXTRACTOR_DIR%.
    goto ERROR
)
mkdir %PYINSTXTRACTOR_DIR%

git clone https://github.com/extremecoders-re/pyinstxtractor.git %PYINSTXTRACTOR_DIR%

::reset pyinstaller extracted folders
if exist %PYINSTALLER_EXTRACTED_DIR% rmdir /s /q %PYINSTALLER_EXTRACTED_DIR%
::rmdir always returns 0, so check folder's existence
if exist %PYINSTALLER_EXTRACTED_DIR% (
    echo Failed to delete %PYINSTALLER_EXTRACTED_DIR%.
    goto ERROR
)
mkdir %PYINSTALLER_EXTRACTED_DIR%

::reset venv folders
if exist %PYTHON_VENV_PYINSTALLER_DIR% rmdir /s /q %PYTHON_VENV_PYINSTALLER_DIR%
::rmdir always returns 0, so check folder's existence
if exist %PYTHON_VENV_PYINSTALLER_DIR% (
    echo Failed to delete %PYTHON_VENV_PYINSTALLER_DIR%.
    goto ERROR
)
if exist %PYTHON_VENV_SOURCE_DIR% rmdir /s /q %PYTHON_VENV_SOURCE_DIR%
::rmdir always returns 0, so check folder's existence
if exist %PYTHON_VENV_SOURCE_DIR% (
    echo Failed to delete %PYTHON_VENV_SOURCE_DIR%.
    goto ERROR
)

python -m venv %PYTHON_VENV_PYINSTALLER_DIR%
call %PYTHON_VENV_PYINSTALLER_DIR%\Scripts\activate
pip install pyinstaller==3.5
pip install --upgrade "setuptools<45.0.0"
del /f %CLI_SRC%\azure-cli\azure\__init__.py
del /f %CLI_SRC%\azure-cli\azure\cli\__init__.py
del /f %CLI_SRC%\azure-cli-core\azure\__init__.py
del /f %CLI_SRC%\azure-cli-core\azure\cli\__init__.py
del /f %CLI_SRC%\azure-cli-telemetry\azure\__init__.py
del /f %CLI_SRC%\azure-cli-telemetry\azure\cli\__init__.py
pip install --no-deps -e %CLI_SRC%\azure-cli-telemetry
pip install --no-deps -e %CLI_SRC%\azure-cli-core
pip install --no-deps -e %CLI_SRC%\azure-cli

pushd %REPO_ROOT%
python .\scripts\pyinstaller\patch\add_pip_main.py
python .\scripts\pyinstaller\patch\update_spec.py
python .\scripts\pyinstaller\patch\add_run_tests_command.py
python .\scripts\pyinstaller\patch\update_core_init_command_modules.py
pip install -r %CLI_SRC%\azure-cli\requirements.py3.windows.txt
popd

:: Remove unused Network SDK API versions
pushd %PYTHON_VENV_PYINSTALLER_DIR%\Lib\site-packages\azure\mgmt\network
rmdir /s /q v2016_09_01 v2016_12_01 v2017_03_01 v2017_06_01 v2017_08_01 v2017_09_01 v2017_11_01 v2018_02_01 v2018_04_01 v2018_06_01 v2018_10_01 v2018_12_01 v2019_04_01 v2019_08_01 v2019_09_01 v2019_11_01 v2019_12_01 v2020_03_01
popd

pyinstaller %REPO_ROOT%\az.spec
pushd %PYINSTALLER_EXTRACTED_DIR%
python %PYINSTXTRACTOR_DIR%\pyinstxtractor.py %REPO_ROOT%\dist\az\az.exe
popd
call deactivate

pushd %REPO_ROOT%
git checkout .
git clean -fdx %CLI_SRC%
popd
python -m venv %PYTHON_VENV_SOURCE_DIR%
call %PYTHON_VENV_SOURCE_DIR%\Scripts\activate
:: source code package
python -m pip install --no-warn-script-location --force-reinstall pycparser==2.18
for %%a in (%CLI_SRC%\azure-cli %CLI_SRC%\azure-cli-core %CLI_SRC%\azure-cli-telemetry) do (
   pushd %%a
   python -m pip install --no-warn-script-location --no-cache-dir --no-deps .
   popd
)
python -m pip install -r %CLI_SRC%\azure-cli\requirements.py3.windows.txt

if %errorlevel% neq 0 goto ERROR

pushd %PYTHON_VENV_SOURCE_DIR%
python %~dp0\patch_models_v2.py
popd

:: Use universal files and remove Py3 only files
pushd %PYTHON_VENV_SOURCE_DIR%\Lib\site-packages\azure\mgmt
for /f %%a in ('dir /b /s *_py3.py') do (
    set PY3_FILE=%%a
    if exist !PY3_FILE! del !PY3_FILE!
)
for /f %%a in ('dir /b /s *_py3.*.pyc') do (
    set PY3_FILE=%%a
    if exist !PY3_FILE! del !PY3_FILE!
)
popd

:: Remove unused Network SDK API versions
pushd %PYTHON_VENV_SOURCE_DIR%\Lib\site-packages\azure\mgmt\network
rmdir /s /q v2016_09_01 v2016_12_01 v2017_03_01 v2017_06_01 v2017_08_01 v2017_09_01 v2017_11_01 v2018_02_01 v2018_04_01 v2018_06_01 v2018_10_01 v2018_12_01 v2019_04_01 v2019_08_01 v2019_09_01 v2019_11_01 v2019_12_01 v2020_03_01
popd

:: Remove .py and only deploy .pyc files
pushd %PYTHON_VENV_SOURCE_DIR%\Lib\site-packages
for /f %%f in ('dir /b /s *.pyc') do (
    set PARENT_DIR=%%~df%%~pf..
    echo !PARENT_DIR! | findstr /C:\Lib\site-packages\pip\ 1>nul
    if !errorlevel! neq  0 (
        set FILENAME=%%~nf
        set BASE_FILENAME=!FILENAME:~0,-11!
        set pyc=!BASE_FILENAME!.pyc
        del !PARENT_DIR!\!BASE_FILENAME!.py
        copy %%~f !PARENT_DIR!\!pyc! >nul
        del %%~f
    ) ELSE (
        echo --SKIP !PARENT_DIR! under pip
    )
)
popd

for /d /r %PYTHON_VENV_SOURCE_DIR%\Lib\site-packages\pip %%d in (__pycache__) do (
    if exist %%d rmdir /s /q "%%d"
)

if %errorlevel% neq 0 goto ERROR
call deactivate

python %REPO_ROOT%\scripts\pyinstaller\check_files.py %PYTHON_VENV_SOURCE_DIR%\Lib\site-packages %PYINSTALLER_EXTRACTED_DIR%\az.exe_extracted\PYZ-00.pyz_extracted

goto END

:ERROR
echo Error occurred, please check the output for details.
exit /b 1

:END
exit /b 0
popd
