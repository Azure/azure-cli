@echo off
echo Building the Windows Installer...
echo.
:: Add Git to the path as this should be run through a .NET command prompt
:: and not a Git bash shell... We also need the gnu toolchain (for curl & unzip)
set PATH=%PATH%;"C:\Program Files (x86)\Git\bin;C:\Program Files (x86)\MSBuild\14.0\Bin"

pushd %~dp0

CALL scripts\prepareBuild.cmd
if %errorlevel% neq 0 exit /b %errorlevel%

echo Building MSI...
msbuild /t:rebuild /p:Configuration=Release

echo.

if not "%1"=="-noprompt" (
   start .\out\
)
popd
