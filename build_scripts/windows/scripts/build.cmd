@echo off
SetLocal EnableDelayedExpansion
echo build a msi installer using local cli sources and python executables. You need to have curl.exe, unzip.exe and msbuild.exe available under PATH
echo.

set "PATH=%PATH%;%ProgramFiles%\Git\bin;%ProgramFiles%\Git\usr\bin;C:\Program Files (x86)\Git\bin;C:\Program Files (x86)\MSBuild\14.0\Bin;"

set PYTHON_DOWNLOAD_URL="https://www.python.org/ftp/python/3.6.5/python-3.6.5-embed-win32.zip"
set GET_PIP_DOWNLOAD_URL="https://bootstrap.pypa.io/get-pip.py"
set WIX_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/msi/wix310-binaries-mirror.zip"

if "%CLI_VERSION%"=="" (
    echo Please set the CLI_VERSION environment variable, e.g. 2.0.13
    goto ERROR
)


:: Set up the output directory and temp. directories
echo Cleaning previous build artifacts...

set OUTPUT_DIR=%~dp0..\out
if exist %OUTPUT_DIR% rmdir /s /q %OUTPUT_DIR%
mkdir %OUTPUT_DIR%

set ARTIFACTS_DIR=%~dp0..\artifacts
mkdir %ARTIFACTS_DIR%

set TEMP_SCRATCH_FOLDER=%ARTIFACTS_DIR%\cli_scratch
set BUILDING_DIR=%ARTIFACTS_DIR%\cli
set PYTHON_DIR=%ARTIFACTS_DIR%\Python
set WIX_DIR=%ARTIFACTS_DIR%\wix
set REPO_ROOT=%~dp0..\..\..

::reset working folders
if exist %BUILDING_DIR% rmdir /s /q %BUILDING_DIR%

::rmdir always returns 0, so check folder's existence 
if exist %BUILDING_DIR% (
    echo Failed to delete %BUILDING_DIR%.
    goto ERROR
)
mkdir %BUILDING_DIR%

:: get Python
if exist %PYTHON_DIR% rmdir /s /q %PYTHON_DIR%

:: rmdir always returns 0, so check folder's existence 
if exist %PYTHON_DIR% (
    echo Failed to delete %PYTHON_DIR%.
    goto ERROR
)

mkdir %PYTHON_DIR%
pushd %PYTHON_DIR%

echo Downloading Python.
curl -o python-archive.zip %PYTHON_DOWNLOAD_URL% -k
unzip -q python-archive.zip
unzip -q python36.zip
if %errorlevel% neq 0 goto ERROR

del python-archive.zip
del python36.zip

echo Python downloaded and extracted successfully.
echo Setting up pip
curl -o get-pip.py %GET_PIP_DOWNLOAD_URL% -k
%PYTHON_DIR%\python.exe get-pip.py
del get-pip.py
echo Pip set up successful.

popd

if exist %TEMP_SCRATCH_FOLDER% rmdir /s /q %TEMP_SCRATCH_FOLDER%
if exist %TEMP_SCRATCH_FOLDER% (
    echo Failed to delete %TEMP_SCRATCH_FOLDER%.
    goto ERROR
)
mkdir %TEMP_SCRATCH_FOLDER%

if exist %REPO_ROOT%\privates (
    copy %REPO_ROOT%\privates\*.whl %TEMP_SCRATCH_FOLDER%
)

:: ensure wix is available
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

:: Use the Python version on the machine that creates the MSI
robocopy %PYTHON_DIR% %BUILDING_DIR% /s /NFL /NDL

:: Build & install all the packages with bdist_wheel
echo Building CLI packages...

:: Workaround for get bdist_wheel to complete otherwise it fails to import azure_bdist_wheel
set PYTHONPATH=%BUILDING_DIR%\Lib\site-packages
del %BUILDING_DIR%\python36._pth

set CLI_SRC=%REPO_ROOT%\src
for %%a in (%CLI_SRC%\azure-cli %CLI_SRC%\azure-cli-core %CLI_SRC%\azure-cli-nspkg) do (
   pushd %%a
   %BUILDING_DIR%\python.exe setup.py bdist_wheel -d %TEMP_SCRATCH_FOLDER%
   popd
)

pushd %CLI_SRC%\command_modules
for /D %%a in (*) do (
   pushd %CLI_SRC%\command_modules\%%a
   %BUILDING_DIR%\python.exe setup.py bdist_wheel -d %TEMP_SCRATCH_FOLDER%
   popd
)
popd

:: Undo the rest of the workaround and add site-packages to ._pth.
:: See https://docs.python.org/3/using/windows.html#finding-modules
set PYTHONPATH=
(
  echo python36.zip
  echo .
  echo Lib\site-packages
) > %BUILDING_DIR%\python36._pth

echo Built CLI packages successfully.

if %errorlevel% neq 0 goto ERROR

set ALL_MODULES=
for %%i in (%TEMP_SCRATCH_FOLDER%\*.whl) do (
    set ALL_MODULES=!ALL_MODULES! %%i
)
echo All modules: %ALL_MODULES%
%BUILDING_DIR%\python.exe -m pip install --no-warn-script-location --no-cache-dir %ALL_MODULES%
%BUILDING_DIR%\python.exe -m pip install --no-warn-script-location --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg

echo Creating the wbin (Windows binaries) folder that will be added to the path...
mkdir %BUILDING_DIR%\wbin
copy %REPO_ROOT%\build_scripts\windows\scripts\az.cmd %BUILDING_DIR%\wbin\
if %errorlevel% neq 0 goto ERROR
copy %REPO_ROOT%\build_scripts\windows\resources\CLI_LICENSE.rtf %BUILDING_DIR%
copy %REPO_ROOT%\build_scripts\windows\resources\ThirdPartyNotices.txt %BUILDING_DIR%

: Delete some files we don't need
rmdir /s /q %BUILDING_DIR%\Scripts
for /f %%a in ('dir %BUILDING_DIR%\Lib\site-packages\*.egg-info /b /s /a:d') do (
    rmdir /s /q %%a
)

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
pushd %BUILDING_DIR%\Lib\site-packages\azure
for /f %%f in ('dir /b /s *.pyc') do (
    set PARENT_DIR=%%~df%%~pf..
    echo !PARENT_DIR! | findstr /C:"!BUILDING_DIR!\Lib\site-packages\pip" 1>nul
    if errorlevel 1 (
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
