@echo off
:: Microsoft Azure CLI - Windows Installer - Author file components script
:: Copyright (C) Microsoft Corporation. All Rights Reserved.
::
:: This re-builds partial WiX files for use in cloning the repo after install.
:: heat.exe from the WiX toolset is used for this.
::
set CLI_VERSION=0.2.3

set PYTHON_VERSION=3.6.1

pushd %~dp0..\

set CLI_ARCHIVE_DOWNLOAD_URL=https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_%CLI_VERSION%.tar.gz

:: Download URL for Wix 10 from https://wix.codeplex.com/downloads/get/1587180
:: Direct download URL http://download-codeplex.sec.s-msft.com/Download/Release?ProjectName=wix&DownloadId=1587180&FileTime=131118854877130000&Build=21050
:: We use a mirror of Wix storage on Azure blob storage as the above link can be slow...
set WIX_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/msi/wix310-binaries-mirror.zip"

set PYTHON_DOWNLOAD_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%.exe

:: Set up the output directory and temp. directories
echo Cleaning previous build artifacts...
set OUTPUT_DIR=.\out
if exist %OUTPUT_DIR% rmdir /s /q %OUTPUT_DIR%
mkdir %OUTPUT_DIR%

set TEMP_CLI_FOLDER=zcli
set TEMP_SCRATCH_FOLDER=zcli_scratch
set TEMP_WIX_FOLDER=zwix
set TEMP_PYTHON_FOLDER=zPython
set BUILDING_DIR=%HOMEDRIVE%%HOMEPATH%\%TEMP_CLI_FOLDER%
set SCRATCH_DIR=%HOMEDRIVE%%HOMEPATH%\%TEMP_SCRATCH_FOLDER%
set WIX_DIR=%HOMEDRIVE%%HOMEPATH%\%TEMP_WIX_FOLDER%
set PYTHON_DIR=%HOMEDRIVE%%HOMEPATH%\%TEMP_PYTHON_FOLDER%

pushd %HOMEDRIVE%%HOMEPATH%
if exist %TEMP_CLI_FOLDER% rmdir /s /q %TEMP_CLI_FOLDER%
::rmdir always returns 0, so check folder's existence 
if exist %TEMP_CLI_FOLDER% (
    echo Failed to delete %TEMP_CLI_FOLDER%.
    goto ERROR
)
mkdir %TEMP_CLI_FOLDER%

if exist %TEMP_SCRATCH_FOLDER% rmdir /s /q %TEMP_SCRATCH_FOLDER%
if exist %TEMP_SCRATCH_FOLDER% (
    echo Failed to delete %TEMP_SCRATCH_FOLDER%.
    goto ERROR
)
mkdir %TEMP_SCRATCH_FOLDER%

if exist %TEMP_PYTHON_FOLDER% (
    echo Using existing Python at %PYTHON_DIR%
)
if not exist %TEMP_PYTHON_FOLDER% (
    mkdir %TEMP_PYTHON_FOLDER%
    pushd %PYTHON_DIR%
    echo Downloading Python %PYTHON_VERSION%
    curl -o python-installer.exe %PYTHON_DOWNLOAD_URL%
    python-installer.exe /quiet InstallAllUsers=0 TargetDir=%PYTHON_DIR% PrependPath=0 AssociateFiles=0 CompileAll=1 Shortcuts=0 Include_test=0 Include_doc=0 Include_dev=0 Include_launcher=0 Include_tcltk=0 Include_tools=0
    if %errorlevel% neq 0 goto ERROR
    del python-installer.exe
    echo Downloaded Python %PYTHON_VERSION% to %PYTHON_DIR% successfully.
    popd
)

if exist %TEMP_WIX_FOLDER% (
    echo Using existing Wix at %WIX_DIR%
)
if not exist %TEMP_WIX_FOLDER% (
    mkdir %TEMP_WIX_FOLDER%
    pushd %WIX_DIR%
    echo Downloading Wix.
    curl -o wix-archive.zip %WIX_DOWNLOAD_URL%
    unzip -q wix-archive.zip
    del wix-archive.zip
    if %errorlevel% neq 0 goto ERROR
    echo Wix downloaded and extracted successfully.
    popd
)

popd

:: Download & unzip CLI archive
pushd %BUILDING_DIR%
echo Downloading CLI archive version %CLI_VERSION%
curl -o cli-archive.tar.gz %CLI_ARCHIVE_DOWNLOAD_URL%
gzip -d < cli-archive.tar.gz | tar xvf - 
del cli-archive.tar.gz
if %errorlevel% neq 0 goto ERROR
echo Downloaded and extracted CLI archive successfully.
popd

:: Use the Python version on the machine that creates the MSI
robocopy %PYTHON_DIR% %BUILDING_DIR% /s /NFL /NDL /NJH /NJS

:: Build & install all the packages with bdist_wheel
%BUILDING_DIR%\python.exe -m pip install wheel
echo Building CLI packages...
set CLI_SRC=%BUILDING_DIR%\azure-cli_packaged_%CLI_VERSION%\src
for %%a in (%CLI_SRC%\azure-cli %CLI_SRC%\azure-cli-core %CLI_SRC%\azure-cli-nspkg) do (
   pushd %%a
   %BUILDING_DIR%\python.exe setup.py bdist_wheel -d %SCRATCH_DIR%
   popd
)
pushd %CLI_SRC%\command_modules
for /D %%a in (*) do (
   pushd %CLI_SRC%\command_modules\%%a
   %BUILDING_DIR%\python.exe setup.py bdist_wheel -d %SCRATCH_DIR%
   popd
)
echo Built CLI packages successfully.
popd
%BUILDING_DIR%\python.exe -m pip install azure-cli -f %SCRATCH_DIR%

rmdir /s /q %BUILDING_DIR%\azure-cli_packaged_%CLI_VERSION%

echo Creating the wbin (Windows binaries) folder that will be added to the path...
mkdir %BUILDING_DIR%\wbin
copy .\scripts\az.cmd %BUILDING_DIR%\wbin\
if %errorlevel% neq 0 goto ERROR
copy .\resources\CLI_LICENSE.rtf %BUILDING_DIR%
copy .\resources\ThirdPartyNotices.txt %BUILDING_DIR%
if %errorlevel% neq 0 goto ERROR

echo.

:SUCCESS
echo Looks good.

goto END

:ERROR
echo Error occurred, please check the output for details.
exit /b 1

:END
exit /b 0
popd
