@echo off
SetLocal EnableDelayedExpansion

REM Double colon :: should not be used in parentheses blocks, so we use REM.
REM See https://stackoverflow.com/a/12407934/2199657

echo build a msi installer using local cli sources and python executables. You need to have curl.exe, unzip.exe and msbuild.exe available under PATH
echo.

set "PATH=%PATH%;%ProgramFiles%\Git\bin;%ProgramFiles%\Git\usr\bin;C:\Program Files (x86)\Git\bin;C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin"

if "%CLI_VERSION%"=="" (
    echo Please set the CLI_VERSION environment variable, e.g. 2.0.13
    goto ERROR
)
@REM ARCH can be x86 or x64
if "%ARCH%"=="" (
    set ARCH=x86
)
@REM TARGET can be msi or zip
if "%TARGET%"=="" (
    set TARGET=msi
)

if "%ARCH%"=="x86" (
    set PYTHON_ARCH=win32
) else if "%ARCH%"=="x64" (
    set PYTHON_ARCH=amd64
) else (
    echo Please set ARCH to "x86" or "x64"
    goto ERROR
)
set PYTHON_VERSION=3.13.13

set WIX_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/msi/wix310-binaries-mirror.zip"
set PYTHON_DOWNLOAD_URL="https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-%PYTHON_ARCH%.zip"

REM https://pip.pypa.io/en/stable/installation/#get-pip-py
set GET_PIP_DOWNLOAD_URL="https://bootstrap.pypa.io/get-pip.py"

REM Set up the output directory and temp. directories
echo Cleaning previous build artifacts...
set OUTPUT_DIR=%~dp0..\out
if exist %OUTPUT_DIR% rmdir /s /q %OUTPUT_DIR%
mkdir %OUTPUT_DIR%

set ARTIFACTS_DIR=%~dp0..\artifacts
mkdir %ARTIFACTS_DIR%
set TEMP_SCRATCH_FOLDER=%ARTIFACTS_DIR%\cli_scratch
set BUILDING_DIR=%ARTIFACTS_DIR%\cli
set WIX_DIR=%ARTIFACTS_DIR%\wix
set PYTHON_DIR=%ARTIFACTS_DIR%\Python

REM win32-only: apply setuptools<82 constraint to ALL pip operations in
REM this build, including the isolated PEP 517 BuildEnvironment that pip
REM creates for building sdists (e.g. pyyaml's in-tree _pyyaml_pep517
REM backend imports setuptools.build_meta; setuptools 82 fails to import
REM on the win32 embed Python because jaraco.text -> urllib.request ->
REM socket -> _socket is missing). PIP_CONSTRAINT is honored by pip's
REM BuildEnvironment. The x64 (amd64) embed Python does not have this
REM problem, so we leave pip on its defaults there.
if "%ARCH%"=="x86" (
    set PIP_CONSTRAINT=%~dp0build-constraints.txt
)

REM Get the absolute directory since we pushd into different levels of subdirectories.
PUSHD %~dp0..\..\..
SET REPO_ROOT=%CD%
POPD

REM reset working folders
if exist %BUILDING_DIR% rmdir /s /q %BUILDING_DIR%
REM rmdir always returns 0, so check folder's existence
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

if "%TARGET%" == "msi" (
    REM ensure wix is available
    if exist %WIX_DIR% (
        echo Using existing Wix at %WIX_DIR%
    )
    if not exist %WIX_DIR% (
        mkdir %WIX_DIR%
        pushd %WIX_DIR%
        echo Downloading Wix.
        curl --output wix-archive.zip %WIX_DOWNLOAD_URL%
        unzip wix-archive.zip
        if %errorlevel% neq 0 goto ERROR
        del wix-archive.zip
        echo Wix downloaded and extracted successfully.
        popd
    )
)

REM ensure Python is available
if exist %PYTHON_DIR% (
    echo Using existing Python at %PYTHON_DIR%
)
if not exist %PYTHON_DIR% (
    echo Setting up Python and pip
    mkdir %PYTHON_DIR%
    pushd %PYTHON_DIR%

    echo Downloading Python
    curl --output python-archive.zip %PYTHON_DOWNLOAD_URL%
    unzip python-archive.zip
    if %errorlevel% neq 0 goto ERROR
    del python-archive.zip
    echo Python downloaded and extracted successfully

    REM Delete _pth file so that Lib\site-packages is included in sys.path
    REM https://github.com/pypa/pip/issues/4207#issuecomment-297396913
    REM https://docs.python.org/3.10/using/windows.html#finding-modules
    del python*._pth

    echo Installing pip
    curl --output get-pip.py %GET_PIP_DOWNLOAD_URL%
    %PYTHON_DIR%\python.exe get-pip.py
    del get-pip.py
    echo Pip set up successful

    REM setuptools is not installed by default in Python 3.12, but it is required by some dependencys
    REM See https://github.com/Azure/azure-cli/pull/27196
    REM Install wheel to force pip install azure-cli in legacy mode
    REM see https://github.com/Azure/azure-cli/pull/29887
    REM win32-only: pin setuptools<82. setuptools 82 eagerly imports
    REM jaraco.text -> jaraco.context -> urllib.request -> http.client ->
    REM socket at module load. On the win32 embeddable Python distribution
    REM this fails with ModuleNotFoundError: _socket. The three azure-cli
    REM local installs below use --no-build-isolation (x86 only) to reuse
    REM this pinned setuptools. PIP_CONSTRAINT (set above for x86 only)
    REM propagates the same pin to any pip install that does use PEP 517
    REM isolation (e.g. building pyyaml from sdist). On x64 (amd64) the
    REM embed Python works normally, so install the latest setuptools.
    echo Installing setuptools wheel
    if "%ARCH%"=="x86" (
        %PYTHON_DIR%\python.exe -Im pip install "setuptools<82" wheel
    ) else (
        %PYTHON_DIR%\python.exe -Im pip install setuptools wheel
    )

    popd
)
set PYTHON_EXE=%PYTHON_DIR%\python.exe


robocopy %PYTHON_DIR% %BUILDING_DIR% /s /NFL /NDL

REM win32-only: pip 26+ defaults to PEP 517 builds even without a
REM pyproject.toml (uses setuptools.build_meta:__legacy__), and pip's
REM isolated BuildEnvironment subprocess cannot import setuptools.build_meta
REM on the win32 embeddable Python (the embed dir is not on sys.path under
REM -I, so _socket.pyd / stdlib extensions are unreachable). Using
REM --no-build-isolation reuses this env's already-working setuptools<82
REM and bypasses that subprocess entirely. On x64 (amd64) the isolated
REM subprocess works fine, so we leave pip on its defaults.
set NOBUILDISO_FLAG=
if "%ARCH%"=="x86" set NOBUILDISO_FLAG=--no-build-isolation

set CLI_SRC=%REPO_ROOT%\src
for %%a in (%CLI_SRC%\azure-cli %CLI_SRC%\azure-cli-core %CLI_SRC%\azure-cli-telemetry) do (
   pushd %%a
   %BUILDING_DIR%\python.exe -Im pip install --no-warn-script-location --no-cache-dir %NOBUILDISO_FLAG% --no-deps .
   if %errorlevel% neq 0 goto ERROR
   popd
)

REM win32-only: pre-build pyyaml from sdist with --no-build-isolation.
REM PyPI has no cp314 win32 wheel for pyyaml, so pip would otherwise spin
REM up a PEP 517 BuildEnvironment subprocess that fails to import pyyaml's
REM in-tree _pyyaml_pep517 backend on the win32 embeddable Python (same
REM root cause as the local installs above). Installing pyyaml into the
REM main env now (which already has setuptools<82 + wheel) makes the
REM requirements install below find it already satisfied. Cython is
REM pyyaml's only extra build requirement and ships a cp314 win32 wheel.
REM On x64 (amd64) PyPI ships a cp314 wheel, so this whole block is
REM unnecessary.
if "%ARCH%"=="x86" (
    %BUILDING_DIR%\python.exe -Im pip install --no-warn-script-location --no-cache-dir Cython
    if !errorlevel! neq 0 goto ERROR
    %BUILDING_DIR%\python.exe -Im pip install --no-warn-script-location --no-cache-dir --no-build-isolation pyyaml
    if !errorlevel! neq 0 goto ERROR
)

%BUILDING_DIR%\python.exe -Im pip install --no-warn-script-location --requirement %CLI_SRC%\azure-cli\requirements.py3.windows.txt
if %errorlevel% neq 0 goto ERROR

REM Check azure.cli can be executed. This also prints the Python version.
%BUILDING_DIR%\python.exe -Im azure.cli --version
if %errorlevel% neq 0 goto ERROR


pushd %BUILDING_DIR%
%BUILDING_DIR%\python.exe -I %REPO_ROOT%\scripts\compact_aaz.py
if %errorlevel% neq 0 goto ERROR
%BUILDING_DIR%\python.exe -I %REPO_ROOT%\scripts\trim_sdk.py
if %errorlevel% neq 0 goto ERROR
popd

REM Remove pywin32 help file to reduce size.
del %BUILDING_DIR%\Lib\site-packages\PyWin32.chm

if "%TARGET%"=="msi" (
    REM Creating the wbin (Windows binaries) folder that will be added to the path...
    mkdir %BUILDING_DIR%\wbin
    copy %REPO_ROOT%\build_scripts\windows\scripts\az_msi.cmd %BUILDING_DIR%\wbin\az.cmd
    copy %REPO_ROOT%\build_scripts\windows\scripts\azps.ps1 %BUILDING_DIR%\wbin\
    copy %REPO_ROOT%\build_scripts\windows\scripts\az %BUILDING_DIR%\wbin\
) else (
    REM Creating the bin folder that will be added to the path...
    mkdir %BUILDING_DIR%\bin
    copy %REPO_ROOT%\build_scripts\windows\scripts\az_zip.cmd %BUILDING_DIR%\bin\az.cmd
)
if %errorlevel% neq 0 goto ERROR
copy %REPO_ROOT%\build_scripts\windows\resources\CLI_LICENSE.rtf %BUILDING_DIR%
copy %REPO_ROOT%\build_scripts\windows\resources\ThirdPartyNotices.txt %BUILDING_DIR%
copy %REPO_ROOT%\NOTICE.txt %BUILDING_DIR%

REM Remove .py and only deploy .pyc files
pushd %BUILDING_DIR%\Lib\site-packages
for /f %%f in ('dir /b /s *.pyc') do (
    set PARENT_DIR=%%~df%%~pf..
    echo !PARENT_DIR! | findstr /C:\Lib\site-packages\pip\ 1>nul
    if !errorlevel! neq  0 (
        REM Only take the file name without 'pyc' extension: e.g., (same below) __init__.cpython-310
        set FILENAME=%%~nf
        REM Truncate the '.cpython-310' postfix which is 12 chars long: __init__
        REM https://stackoverflow.com/a/636391/2199657
        set BASE_FILENAME=!FILENAME:~0,-12!
        REM __init__.pyc
        set pyc=!BASE_FILENAME!.pyc
        REM Delete ..\__init__.py
        del !PARENT_DIR!\!BASE_FILENAME!.py
        REM Copy to ..\__init__.pyc
        copy %%~f !PARENT_DIR!\!pyc! >nul
        REM Delete __init__.pyc
        del %%~f
    ) ELSE (
        REM pip source code is required when install packages from source code
        echo --SKIP !PARENT_DIR! under pip
    )
)
popd

REM Remove empty __pycache__ directories because .pyc files are already moved to parent directories
echo remove pycache
for /d /r %BUILDING_DIR%\Lib\site-packages\ %%d in (__pycache__) do (
    if exist %%d rmdir /s /q "%%d"
)

REM Remove dist-info
echo remove dist-info
pushd %BUILDING_DIR%\Lib\site-packages
for /d %%d in ("azure*.dist-info") do (
    if exist %%d rmdir /s /q "%%d"
)
popd


if "%TARGET%"=="msi" (
    echo Building MSI...
    msbuild /t:rebuild /p:Configuration=Release /p:Platform=%ARCH% %REPO_ROOT%\build_scripts\windows\azure-cli.wixproj
) else (
    echo Building ZIP...
    "%ProgramFiles%\7-Zip\7z.exe" a -tzip "%OUTPUT_DIR%\Microsoft Azure CLI.zip" "%BUILDING_DIR%\*"
)

if %errorlevel% neq 0 goto ERROR

echo Output Dir: %OUTPUT_DIR%

goto END

:ERROR
echo Error occurred, please check the output for details.
exit /b 1

:END
exit /b 0
popd
