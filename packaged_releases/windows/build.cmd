@echo off
echo Building the Windows Installer...
echo NOTE: This needs to be run from a .NET developer command prompt with msbuild in the path.
echo.

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
