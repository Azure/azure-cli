@echo off
SetLocal EnableDelayedExpansion
echo build a msi installer using local cli sources and python executables. You need to have curl.exe, unzip.exe and msbuild.exe available under PATH
echo.

set "PATH=%PATH%;%ProgramFiles%\Git\bin;%ProgramFiles%\Git\usr\bin;C:\Program Files (x86)\Git\bin;C:\Program Files (x86)\MSBuild\14.0\Bin;C:\Program Files (x86)\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin;"

if "%CLI_VERSION%"=="" (
    echo Please set the CLI_VERSION environment variable, e.g. 2.0.13
    goto ERROR
)

set WIX_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/msi/wix310-binaries-mirror.zip"
set PROPAGATE_ENV_CHANGE_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/util/propagate_env_change.zip"

:: Set up the output directory and temp. directories
echo Cleaning previous build artifacts...
set OUTPUT_DIR=%~dp0..\out
if exist %OUTPUT_DIR% rmdir /s /q %OUTPUT_DIR%
mkdir %OUTPUT_DIR%

set ARTIFACTS_DIR=%~dp0..\artifacts
mkdir %ARTIFACTS_DIR%
set BUILDING_DIR=%ARTIFACTS_DIR%\cli
set WIX_DIR=%ARTIFACTS_DIR%\wix
set PYTHON_VENV_DIR=%ARTIFACTS_DIR%\venv
set PROPAGATE_ENV_CHANGE_DIR=%~dp0..\propagate_env_change

set REPO_ROOT=%~dp0..\..\..

::reset working folders
if exist %BUILDING_DIR% rmdir /s /q %BUILDING_DIR%
::rmdir always returns 0, so check folder's existence
if exist %BUILDING_DIR% (
    echo Failed to delete %BUILDING_DIR%.
    goto ERROR
)
mkdir %BUILDING_DIR%

::reset venv folders
if exist %PYTHON_VENV_DIR% rmdir /s /q %PYTHON_VENV_DIR%
::rmdir always returns 0, so check folder's existence
if exist %PYTHON_VENV_DIR% (
    echo Failed to delete %PYTHON_VENV_DIR%.
    goto ERROR
)

::ensure wix is available
if exist %WIX_DIR% (
    echo Using existing Wix at %WIX_DIR%
)
if not exist %WIX_DIR% (
    mkdir %WIX_DIR%
    pushd %WIX_DIR%
    echo Downloading Wix.
    curl -o wix-archive.zip %WIX_DOWNLOAD_URL% -k
    unzip -q wix-archive.zip
    if %errorlevel% neq 0 goto ERROR
    del wix-archive.zip
    echo Wix downloaded and extracted successfully.
    popd
)

set CLI_SRC=%REPO_ROOT%\src

python -m venv %PYTHON_VENV_DIR%
call %PYTHON_VENV_DIR%\Scripts\activate
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
pushd %PYTHON_VENV_DIR%\Lib\site-packages\azure\mgmt\network
rmdir /s /q v2016_09_01 v2016_12_01 v2017_03_01 v2017_06_01 v2017_08_01 v2017_09_01 v2017_11_01 v2018_02_01 v2018_04_01 v2018_06_01 v2018_10_01 v2018_12_01 v2019_04_01 v2019_08_01 v2019_09_01 v2019_11_01 v2019_12_01 v2020_03_01
popd

pyinstaller %REPO_ROOT%\az.spec
call deactivate

robocopy %REPO_ROOT%\dist\az %BUILDING_DIR% /s /NFL /NDL
robocopy %REPO_ROOT%\dist\azpip %BUILDING_DIR% /s /NFL /NDL
robocopy %REPO_ROOT%\dist\aztelemetry %BUILDING_DIR% /s /NFL /NDL

echo Creating the wbin (Windows binaries) folder that will be added to the path...
mkdir %BUILDING_DIR%\wbin
copy %REPO_ROOT%\build_scripts\windows\scripts\az.cmd %BUILDING_DIR%\wbin\
copy %REPO_ROOT%\build_scripts\windows\scripts\az %BUILDING_DIR%\wbin\
if %errorlevel% neq 0 goto ERROR
copy %REPO_ROOT%\build_scripts\windows\resources\CLI_LICENSE.rtf %BUILDING_DIR%
copy %REPO_ROOT%\build_scripts\windows\resources\ThirdPartyNotices.txt %BUILDING_DIR%
copy %REPO_ROOT%\NOTICE.txt %BUILDING_DIR%

if %errorlevel% neq 0 goto ERROR

::ensure propagate_env_change.exe is available
if exist "%PROPAGATE_ENV_CHANGE_DIR%\propagate_env_change.exe" (
    echo Using existing propagate_env_change.exe at %PROPAGATE_ENV_CHANGE_DIR%
) else (
    pushd %PROPAGATE_ENV_CHANGE_DIR%
    echo Downloading propagate_env_change.exe.
    curl -o propagate_env_change.zip %PROPAGATE_ENV_CHANGE_DOWNLOAD_URL% -k
    unzip -q propagate_env_change.zip
    if %errorlevel% neq 0 goto ERROR
    del propagate_env_change.zip
    echo propagate_env_change.exe downloaded and extracted successfully.
    popd
)

echo Building MSI...
msbuild /t:rebuild /p:Configuration=Release %REPO_ROOT%\build_scripts\windows\azure-cli.wixproj

start %OUTPUT_DIR%

goto END

:ERROR
echo Error occurred, please check the output for details.
exit /b 1

:END
exit /b 0
popd
