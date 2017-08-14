@echo off
SetLocal EnableDelayedExpansion
echo build a msi installer using local cli sources and python executables. You need to have curl.exe, unzip.exe and msbuild.exe available under PATH
echo.

set "PATH=%PATH%;%ProgramFiles%\Git\bin;%ProgramFiles%\Git\usr\bin"

if "%CLIVERSION%"=="" (
    echo Please set the CLIVERSION environment variable, e.g. 2.0.13
    goto ERROR
)
set PYTHON_VERSION=3.6.1

set WIX_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/msi/wix310-binaries-mirror.zip"

:: Set up the output directory and temp. directories
echo Cleaning previous build artifacts...
set OUTPUT_DIR=%~dp0..\out
if exist %OUTPUT_DIR% rmdir /s /q %OUTPUT_DIR%
mkdir %OUTPUT_DIR%

set TEMP_SCRATCH_FOLDER=%HOMEDRIVE%%HOMEPATH%\zcli_scratch
set BUILDING_DIR=%HOMEDRIVE%%HOMEPATH%\zcli
set WIX_DIR=%HOMEDRIVE%%HOMEPATH%\zwix
set REPO_ROOT=%~dp0..\..\..

:: look for python 3.x so we can build into the installer
if not "%1"=="" (
   set PYTHON_DIR=%1
   set PYTHON_EXE=%1\python.exe
   goto PYTHON_FOUND
)

FOR /f %%i IN ('where python') DO (
  set PY_FILE_DRIVE=%%~di
  set PY_FILE_PATH=%%~pi
  set PY_FILE_NAME=%%~ni
  set PYTHON_EXE=!PY_FILE_DRIVE!!PY_FILE_PATH!!PY_FILE_NAME!.exe
  set PYTHON_DIR=!PY_FILE_DRIVE!!PY_FILE_PATH!
  FOR /F "delims=" %%j IN ('!PYTHON_EXE! --version') DO (
    set PYTHON_VER=%%j
    echo.!PYTHON_VER!|findstr /C:"%PYTHON_VERSION%" >nul 2>&1
    if not errorlevel 1 (
       goto PYTHON_FOUND
    )
  )
)
echo python %PYTHON_VERSION% is needed to create installer.
exit /b 1
:PYTHON_FOUND
echo Python Executables: %PYTHON_DIR%, %PYTHON_EXE%

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

copy %REPO_ROOT%\privates\*.whl %TEMP_SCRATCH_FOLDER%

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

:: Use the Python version on the machine that creates the MSI
robocopy %PYTHON_DIR% %BUILDING_DIR% /s /NFL /NDL

:: Build & install all the packages with bdist_wheel
%BUILDING_DIR%\python %~dp0build-packages.py %TEMP_SCRATCH_FOLDER% %REPO_ROOT%
if %errorlevel% neq 0 goto ERROR
:: Install them to the temp folder so to be packaged 
%BUILDING_DIR%\python.exe -m pip install -f %TEMP_SCRATCH_FOLDER% --no-cache-dir azure-cli
%BUILDING_DIR%\python.exe -m pip install --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg

echo Creating the wbin (Windows binaries) folder that will be added to the path...
mkdir %BUILDING_DIR%\wbin
copy %REPO_ROOT%\packaged_releases\windows\scripts\az.cmd %BUILDING_DIR%\wbin\
if %errorlevel% neq 0 goto ERROR
copy %REPO_ROOT%\packaged_releases\windows\resources\CLI_LICENSE.rtf %BUILDING_DIR%
copy %REPO_ROOT%\packaged_releases\windows\resources\ThirdPartyNotices.txt %BUILDING_DIR%
del %BUILDING_DIR%\Scripts\pip.exe
del %BUILDING_DIR%\Scripts\pip3.exe
del %BUILDING_DIR%\Scripts\pip3.6.exe
if %errorlevel% neq 0 goto ERROR

echo Building MSI...
msbuild /t:rebuild /p:Configuration=Release %REPO_ROOT%\packaged_releases\windows\azure-cli.wixproj

start %OUTPUT_DIR%

goto END

:ERROR
echo Error occurred, please check the output for details.
exit /b 1

:END
exit /b 0
popd
