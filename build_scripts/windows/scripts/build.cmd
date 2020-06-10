@echo off
SetLocal EnableDelayedExpansion
echo build a msi installer using local cli sources and python executables. You need to have curl.exe, unzip.exe and msbuild.exe available under PATH
echo.

set "PATH=%PATH%;%ProgramFiles%\Git\bin;%ProgramFiles%\Git\usr\bin;C:\Program Files (x86)\Git\bin;C:\Program Files (x86)\MSBuild\14.0\Bin;C:\Program Files (x86)\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin;"

if "%CLI_VERSION%"=="" (
    echo Please set the CLI_VERSION environment variable, e.g. 2.0.13
    goto ERROR
)
set PYTHON_VERSION=3.6.6

set WIX_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/msi/wix310-binaries-mirror.zip"
set PYTHON_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/util/Python366-32.zip"
set PROPAGATE_ENV_CHANGE_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/util/propagate_env_change.zip"

:: Set up the output directory and temp. directories
echo Cleaning previous build artifacts...
set OUTPUT_DIR=%~dp0..\out
if exist %OUTPUT_DIR% rmdir /s /q %OUTPUT_DIR%
mkdir %OUTPUT_DIR%

set ARTIFACTS_DIR=%~dp0..\artifacts
mkdir %ARTIFACTS_DIR%
set TEMP_SCRATCH_FOLDER=%ARTIFACTS_DIR%\cli_scratch
set BUILDING_DIR=%ARTIFACTS_DIR%\cli
set WIX_DIR=%ARTIFACTS_DIR%\wix
set PYTHON_DIR=%ARTIFACTS_DIR%\Python366-32
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

if exist %TEMP_SCRATCH_FOLDER% rmdir /s /q %TEMP_SCRATCH_FOLDER%
if exist %TEMP_SCRATCH_FOLDER% (
    echo Failed to delete %TEMP_SCRATCH_FOLDER%.
    goto ERROR
)
mkdir %TEMP_SCRATCH_FOLDER%

if exist %REPO_ROOT%\privates (
    copy %REPO_ROOT%\privates\*.whl %TEMP_SCRATCH_FOLDER%
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

::ensure Python is available
if exist %PYTHON_DIR% (
    echo Using existing Python at %PYTHON_DIR%
)
if not exist %PYTHON_DIR% (
    mkdir %PYTHON_DIR%
    pushd %PYTHON_DIR%
    echo Downloading Python.
    curl -o Python366-32.zip %PYTHON_DOWNLOAD_URL% -k
    unzip -q Python366-32.zip
    if %errorlevel% neq 0 goto ERROR
    del Python366-32.zip
    echo Python downloaded and extracted successfully.
    popd
)
set PYTHON_EXE=%PYTHON_DIR%\python.exe

robocopy %PYTHON_DIR% %BUILDING_DIR% /s /NFL /NDL

set CLI_SRC=%REPO_ROOT%\src
%BUILDING_DIR%\python.exe -m pip install --no-warn-script-location --force-reinstall pycparser==2.18
for %%a in (%CLI_SRC%\azure-cli %CLI_SRC%\azure-cli-core %CLI_SRC%\azure-cli-nspkg %CLI_SRC%\azure-cli-telemetry) do (
   pushd %%a
   %BUILDING_DIR%\python.exe -m pip install --no-warn-script-location --no-cache-dir --no-deps .
   popd
)
%BUILDING_DIR%\python.exe -m pip install -r %CLI_SRC%\azure-cli\requirements.py3.windows.txt

if %errorlevel% neq 0 goto ERROR

%BUILDING_DIR%\python.exe -m pip install --no-warn-script-location --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg
%BUILDING_DIR%\python.exe -m pip install --no-warn-script-location --force-reinstall urllib3==1.24.2

pushd %BUILDING_DIR%
%BUILDING_DIR%\python.exe %~dp0\patch_models_v2.py
popd

echo Creating the wbin (Windows binaries) folder that will be added to the path...
mkdir %BUILDING_DIR%\wbin
copy %REPO_ROOT%\build_scripts\windows\scripts\az.cmd %BUILDING_DIR%\wbin\
copy %REPO_ROOT%\build_scripts\windows\scripts\az %BUILDING_DIR%\wbin\
if %errorlevel% neq 0 goto ERROR
copy %REPO_ROOT%\build_scripts\windows\resources\CLI_LICENSE.rtf %BUILDING_DIR%
copy %REPO_ROOT%\build_scripts\windows\resources\ThirdPartyNotices.txt %BUILDING_DIR%

:: Use universal files and remove Py3 only files
pushd %BUILDING_DIR%\Lib\site-packages\azure\mgmt
for /f %%a in ('dir /b /s *_py3.py') do (
    set PY3_FILE=%%a
    if exist !PY3_FILE! del !PY3_FILE!
)
for /f %%a in ('dir /b /s *_py3.*.pyc') do (
    set PY3_FILE=%%a
    if exist !PY3_FILE! del !PY3_FILE!
)
popd

:: Remove .py and only deploy .pyc files
pushd %BUILDING_DIR%\Lib\site-packages
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

for /d /r %BUILDING_DIR%\Lib\site-packages\pip %%d in (__pycache__) do (
    if exist %%d rmdir /s /q "%%d"
)

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